# trade_api.py - Flask app for MT5 execution with detailed logging
import configparser
import os
from flask import Flask, request, jsonify
import MetaTrader5 as mt5
import logging

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

    # Initialize MT5
    logging.info("🔌 Initializing MetaTrader 5...")
    if not mt5.initialize(path=MT5_PATH, login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        error_msg = mt5.last_error()
        logging.error(f"❌ MT5 initialization failed: {error_msg}")
        return jsonify({"error": "MT5 init failed"}), 500
    logging.info("✅ MT5 initialized successfully.")

    result = None

    if action in ("buy", "sell"):
        order_type = mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL
        tick = mt5.symbol_info_tick(symbol)

        if not tick:
            logging.error(f"❌ Could not fetch tick data for symbol: {symbol}")
            mt5.shutdown()
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
            "comment": "TextCmd",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC
        }

        logging.info("📤 Sending trade order: %s", request_params)
        result = mt5.order_send(request_params)
        logging.info("📬 Order response: %s", result)

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
                "comment": "VoiceExit",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            logging.info("📤 Closing position: %s", close_request)
            close_result = mt5.order_send(close_request)
            logging.info("📬 Close response: %s", close_result)

    else:
        logging.error("❌ Invalid action: %s", action)
        mt5.shutdown()
        return jsonify({"error": "invalid action"}), 400

    mt5.shutdown()
    logging.info("🔌 MT5 shutdown complete.")
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
