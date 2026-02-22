# trade_api.py - Flask app for MT5 execution with detailed logging
import configparser
import os
import json                      
from datetime import datetime, timedelta    
from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import logging
import threading              
import time                   

app = Flask(__name__)
API_KEY = "YourSecureApiKeyHere"

# Setup logging
logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Load config from config.ini
config = configparser.ConfigParser()
config.read(os.path.join(os.path.dirname(__file__), 'config.ini'))

MT5_LOGIN = int(config.get("MT5", "login"))
MT5_PASSWORD = config.get("MT5", "password")
MT5_SERVER = config.get("MT5", "server")
MT5_PATH = config.get("MT5", "path")

# =========================
# RISK CONFIG
# =========================
RISK_FILE = "risk_state.json"
DAILY_LIMIT = 0.019   # 0.90%
PEAK_LIMIT = 0.019    # 1.90%

def load_risk_state():
    if not os.path.exists(RISK_FILE):
        return {}
    with open(RISK_FILE, "r") as f:
        return json.load(f)

def save_risk_state(state):
    with open(RISK_FILE, "w") as f:
        json.dump(state, f)

def risk_check():
    acc = mt5.account_info()
    if not acc:
        return False, "account fetch failed"

    balance = acc.balance
    today = datetime.now().strftime("%Y-%m-%d")
    state = load_risk_state()

    # First time initialization
    if not state:
        state = {
            "date": today,
            "daily_open_balance": balance,
            "peak_balance": balance
        }

    # Reset daily balance if new day
    if state["date"] != today:
        state["date"] = today
        state["daily_open_balance"] = balance
        state["peak_balance"] = balance

    # Update peak balance
    if balance > state["peak_balance"]:
        state["peak_balance"] = balance

    daily_limit_balance = state["daily_open_balance"] * (1 - DAILY_LIMIT)
    peak_limit_balance = state["peak_balance"] * (1 - PEAK_LIMIT)

    save_risk_state(state)

    if balance <= daily_limit_balance:
        return False, "Daily drawdown exceeded"

    if balance <= peak_limit_balance:
        return False, "Peak drawdown exceeded"

    return True, "ok"
# =========================
# END RISK SECTION
# =========================

# ==================================================
# >>> NEW – CLOSE ALL POSITIONS (AUTO RISK CONTROL)
# ==================================================
def close_all_positions():
    positions = mt5.positions_get() or []
    for pos in positions:
        symbol = pos.symbol
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            continue

        close_type = mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask

        req = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": pos.volume,
            "type": close_type,
            "position": pos.ticket,
            "price": price,
            "deviation": 10,
            "magic": 20250803,
            "comment": "AUTO_RISK_CLOSE",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }
        logging.warning(f"🚨 Auto closing position {pos.ticket}")
        mt5.order_send(req)


# ==================================================
# >>> NEW – LIVE RISK MONITOR THREAD
# ==================================================
def risk_monitor_loop():
    while True:
        try:
            acc = mt5.account_info()
            if not acc:
                logging.error("MT5 connection lost in monitor")
                time.sleep(5)
                continue

            allowed, reason = risk_check()

            if not allowed:
                logging.error(f"🚨 LIVE RISK HIT: {reason}")
                close_all_positions()
 

        except Exception as e:
            logging.error(f"Risk Monitor Error: {e}")

        time.sleep(10)   # check every 10 seconds

# =========================
# >>> NEW – P/L SNAPSHOT
# =========================
def get_pl_snapshot():
    acc = mt5.account_info()
    if not acc:
        return {
            "current_trade_pl": 0,
            "today_pl": 0,
            "today_pl_percent": 0
        }

    # Current open trades P/L
    positions = mt5.positions_get() or []
    current_trade_pl = sum(p.profit for p in positions)

    # Today P/L from risk state
    state = load_risk_state()
    today = datetime.now().strftime("%Y-%m-%d")

    # >>> ADD THIS BLOCK
    if not state or state.get("date") != today:
        state = {
            "date": today,
            "daily_open_balance": acc.balance,
            "peak_balance": acc.balance
        }
        save_risk_state(state)
    
    
    daily_open_balance = state.get("daily_open_balance", acc.balance)

    today_pl = acc.equity - daily_open_balance
    today_pl_percent = (today_pl / daily_open_balance) * 100 if daily_open_balance else 0

    return {
        "current_trade_pl": round(current_trade_pl, 2),
        "today_pl": round(today_pl, 2),
        "today_pl_percent": round(today_pl_percent, 2)
    }

@app.route("/trade", methods=["POST"])
def trade():
    data = request.json or {}
    logging.info("📥 Received request: %s", data)

    if data.get("api_key") != API_KEY:
        logging.warning("❌ Unauthorized access attempt.")
        return jsonify({"error": "unauthorized"}), 403

    action = data.get("action")
    volume = float(data.get("volume", 0))
    symbol = data.get("symbol", "XAUUSD")

    logging.info("🧠 Parsed command: action=%s, volume=%.2f, symbol=%s", action, volume, symbol)

    result = None

    if action in ("buy", "sell") and volume <= 0:
        logging.error("❌ Invalid volume received: %s", volume)
        return jsonify({"error": "invalid volume"}), 400
    
    if action in ("buy", "sell"):
        
        # ENTRY GATE RISK CHECK
        allowed, reason = risk_check()
        if not allowed:
            logging.warning(f"🛑 Trading blocked: {reason}")
            return jsonify({"error": reason}), 403        
        
        order_type = mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)        

        if not tick:
            logging.error(f"❌ Could not fetch tick data for symbol: {symbol}")
            return jsonify({"error": "tick fetch failed"}), 500

        price = tick.ask if order_type == mt5.ORDER_TYPE_BUY else tick.bid
        request_params = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "price": price,
            "deviation": 10,
            "magic": 20250803,
            "comment": "GKK_Gold_Entry",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }

        logging.info("📤 Sending trade order: %s", request_params)
        result = mt5.order_send(request_params)
        logging.info("📬 Order response: %s", result)

    elif action == "exit_half":
        positions = mt5.positions_get()

        if not positions:
            return jsonify({"message": "No open positions"})

        total_positions = len(positions)
        positions_to_close = total_positions // 2

        if positions_to_close == 0:
            return jsonify({"message": "Only 1 position open. Nothing to close."})

        closed = 0

        for pos in positions[:positions_to_close]:
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": pos.ticket,
                "price": mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask,
                "deviation": 20,
                "magic": 123456,
                "comment": "Half Exit",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(close_request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                closed += 1

        return jsonify({
            "message": f"Closed {closed} of {total_positions} positions"
        })

    elif action == "exit":
        logging.info("🔍 Fetching open positions for symbol: %s", symbol)
        positions = mt5.positions_get(symbol=symbol) or []

        if not positions:
            logging.info("ℹ️ No open positions found.")
        for pos in positions:
            tp = pos.type
            close_type = mt5.ORDER_TYPE_SELL if tp == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            price = (mt5.symbol_info_tick(symbol).bid if close_type == mt5.ORDER_TYPE_SELL
                     else mt5.symbol_info_tick(symbol).ask)
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": close_type,
                "position": pos.ticket,
                "price": price,
                "deviation": 10,
                "magic": 20250803,
                "comment": "GKK_Gold_Exit",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            logging.info("📤 Closing position: %s", close_request)
            close_result = mt5.order_send(close_request)
            logging.info("📬 Close response: %s", close_result)

    else:
        logging.error("❌ Invalid action: %s", action)
        return jsonify({"error": "invalid action"}), 400

    # Capture P/L 
    pl_data = get_pl_snapshot()

    # Response now includes P/L
    # return jsonify({
    #     "status": "ok",
    #     "pl": pl_data
    # })
    return jsonify({
    "status": "ok",
    "server_time": datetime.now().isoformat(),
    "action": action,
    "symbol": symbol,
    "volume": volume,
    "ticket": result.order if result else None,
    "retcode": result.retcode if result else None,
    "comment": result.comment if result else None,
    "pl": pl_data
    })
@app.route("/dashboard", methods=["GET"])
def dashboard():
    
    acc = mt5.account_info()
    state = load_risk_state()

    balance = acc.balance
    equity = acc.equity

    daily_open = state.get("daily_open_balance", balance)
    peak_balance = state.get("peak_balance", balance)
    
    today_pl = equity - daily_open
    today_pl_percent = (today_pl / daily_open) * 100 if daily_open else 0
    
    daily_drawdown_percent = ((daily_open - equity) / daily_open) * 100 if daily_open else 0
    peak_drawdown_percent = ((peak_balance - equity) / peak_balance) * 100 if peak_balance else 0

    return jsonify({
        "today_open_balance": round(daily_open, 2),  
        "today_peak_balance": round(peak_balance, 2),
        "balance": round(balance, 2),
        "equity": round(equity, 2),
        "today_pl": round(today_pl, 2),
        "today_pl_percent": round(today_pl_percent, 2),
        "daily_drawdown_percent": round(daily_drawdown_percent, 2),
        "peak_drawdown_percent": round(peak_drawdown_percent, 2)
    })

import atexit

def shutdown_mt5():
    print("🔌 Shutting down MT5...")
    mt5.shutdown()

if __name__ == "__main__":

    # ✅ Initialize MT5 ONCE at startup
    if not mt5.initialize(
        path=MT5_PATH,
        login=MT5_LOGIN,
        password=MT5_PASSWORD,
        server=MT5_SERVER
    ):
        print("❌ MT5 Initialization Failed:", mt5.last_error())
        exit()

    print("✅ MT5 Connected Successfully")

    # ✅ Register shutdown handler
    atexit.register(shutdown_mt5)

    # ✅ Start live risk monitor thread
    t = threading.Thread(target=risk_monitor_loop, daemon=True)
    t.start()

    # ✅ Start Flask
    app.run(host="0.0.0.0", port=5005)
