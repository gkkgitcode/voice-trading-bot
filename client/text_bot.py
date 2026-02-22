import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import REMOTE_SERVERS, API_KEY
from command_parser import parse_command
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
import os
import threading

# Settings
#SERVER_URL = "http://192.168.29.133:5000/trade"  # Your Flask server
API_KEY = "YourSecureApiKeyHere"  # Match the value in your trade_api.py

# Setup trade logger
handler = RotatingFileHandler(
    "client_trades.log",
    maxBytes=5_000_000,   # 5MB
    backupCount=5
)

logging.basicConfig(
    handlers=[handler],
    level=logging.INFO,
    format="%(asctime)s | %(message)s"
)

# ===============================
# JSON AUDIT WRITER
# ===============================
JSON_FILE = "client_trades.json"

# def append_trade_json(trade_data):
#     try:
#         # If file doesn't exist, create empty list
#         if not os.path.exists(JSON_FILE):
#             with open(JSON_FILE, "w") as f:
#                 json.dump([], f)

#         # Load existing data
#         with open(JSON_FILE, "r") as f:
#             trades = json.load(f)

#         # Append new trade
#         trades.append(trade_data)

#         # Save back
#         with open(JSON_FILE, "w") as f:
#             json.dump(trades, f, indent=4)

#     except Exception as e:
#         logging.error(f"JSON Write Error: {e}")

# def append_trade_json(trade_data):
#     with open("client_trades.json", "a") as f:
#         f.write(json.dumps(trade_data) + "\n")

json_lock = threading.Lock()

def append_trade_json(trade_data):
    with json_lock:
        with open("client_trades.json", "a") as f:
            f.write(json.dumps(trade_data) + "\n")

# def send_order(client, command):
#     """Send order to a single client"""
#     url = f"http://{client['host']}:{client['port']}/trade"

#     client_command = command.copy()

#     # Add lot size only for buy/sell
#     if client_command["action"] in ["buy", "sell"]:
#         if "lot" not in client:
#             raise ValueError(f"Lot size missing for {client['id']}")
#         client_command["volume"] = client["lot"]

#     print(f"➡️ Sending to {client['id']} → {url} → {client_command}")

#     try:
#         response = requests.post(url, json=client_command, timeout=10)
#         print(f"✅ {client['id']} responded: {response.text}")
#     except Exception as e:
#         print(f"❌ Error sending to {client['id']}: {e}")

def send_order(client, command):
    """Send order to a single client"""
    url = f"http://{client['host']}:{client['port']}/trade"
    client_command = command.copy()

    if client_command["action"] in ["buy", "sell"]:
        if "lot" not in client:
            raise ValueError(f"Lot size missing for {client['id']}")
        client_command["volume"] = client["lot"]

    print(f"➡️ Sending to {client['id']} → {client_command}")

    try:
        response = requests.post(url, json=client_command, timeout=10)
        data = response.json()

        print(f"✅ {client['id']} responded: {data}")

        # -----------------------------
        # Build trade record
        # -----------------------------
        trade_record = {
            "timestamp": datetime.now().isoformat(),
            "server": client["id"],
            "action": data.get("action"),
            "symbol": data.get("symbol"),
            "volume": data.get("volume"),
            "ticket": data.get("ticket"),
            "retcode": data.get("retcode"),
            "status": data.get("status")
        }

        # -----------------------------
        # Write to readable log
        # -----------------------------
        logging.info(
            f"SERVER={trade_record['server']} | "
            f"ACTION={trade_record['action']} | "
            f"SYMBOL={trade_record['symbol']} | "
            f"VOL={trade_record['volume']} | "
            f"TICKET={trade_record['ticket']} | "
            f"RETCODE={trade_record['retcode']} | "
            f"STATUS={trade_record['status']}"
        )

        # -----------------------------
        # Write to JSON audit file
        # -----------------------------
        append_trade_json(trade_record)

    except Exception as e:
        error_msg = f"SERVER={client['id']} | ERROR={str(e)}"
        print(f"❌ {error_msg}")
        logging.error(error_msg)

def get_dashboard(client):
    url = f"http://{client['host']}:{client['port']}/dashboard"
    try:
        r = requests.get(url, timeout=5)
        return client['id'], r.json()
    except Exception as e:
        return client['id'], {"error": str(e)}

def main():
    #print("💬 Text Command Mode (type 'b' to Buy, 's' to Sell, or 'e' to Exit or 'd' for Dashbaord; 'q' to Quit)")
    print("💬 Text Command Mode (type 'b' to Buy, 's' to Sell, 'e' to Exit All, 'h' to Exit 50%, 'd' for Dashboard; 'q' to Quit)")
    while True:
        user_input = input("Enter command: ").strip().lower()

        if user_input == 'h':
            command = {
                "action": "exit_half"
            }
            command["api_key"] = API_KEY

            with ThreadPoolExecutor(max_workers=len(REMOTE_SERVERS)) as executor:
                futures = [
                    executor.submit(send_order, client, command)
                    for client in REMOTE_SERVERS
                ]

                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"⚠️ Thread error: {e}")

            continue

        if user_input == 'q':
            print("👋 Quitting text command bot...")
            break

        # if user_input == 'd':
        #     results = []

        #     with ThreadPoolExecutor(max_workers=len(REMOTE_SERVERS)) as executor:
        #         futures = [executor.submit(get_dashboard, client) for client in REMOTE_SERVERS]

        #         for future in as_completed(futures):
        #             results.append(future.result())

        #     # PRINT CLEANLY AFTER THREADS FINISH
        #     for server_id, data in results:
        #         print(f"\n📊 {server_id} Dashboard")
        #         for k, v in data.items():
        #             print(f"   {k}: {v}")

        #     continue
        
        if user_input == 'd':
            results = []

            with ThreadPoolExecutor(max_workers=len(REMOTE_SERVERS)) as executor:
                futures = [executor.submit(get_dashboard, client) for client in REMOTE_SERVERS]

                for future in as_completed(futures):
                    results.append(future.result())

            # -----------------------------
            # Aggregation Variables
            # -----------------------------
            total_balance = 0
            total_equity = 0
            total_today_pl = 0
            total_today_open_balance = 0
            total_peak_balance = 0

            # -----------------------------
            # Per Server Print + Aggregate
            # -----------------------------
            for server_id, data in results:

                print(f"\n📊 {server_id} Dashboard")

                if "error" in data:
                    print(f"   ❌ Error: {data['error']}")
                    continue

                for k, v in data.items():
                    print(f"   {k}: {v}")

                total_balance += data.get("balance", 0)
                total_equity += data.get("equity", 0)
                total_today_pl += data.get("today_pl", 0)
                total_today_open_balance += data.get("today_open_balance", 0)
                total_peak_balance += data.get("today_peak_balance", 0)

            # -----------------------------
            # Master Aggregation
            # -----------------------------
            master_today_pl_percent = (
                (total_today_pl / total_today_open_balance) * 100
                if total_today_open_balance else 0
            )

            master_daily_dd_percent = (
                ((total_today_open_balance - total_equity) / total_today_open_balance) * 100
                if total_today_open_balance else 0
            )

            master_peak_dd_percent = (
                ((total_peak_balance - total_equity) / total_peak_balance) * 100
                if total_peak_balance else 0
            )

            # -----------------------------
            # Print Master Summary
            # -----------------------------
            print("\n================ MASTER SUMMARY ================")
            print(f"Total Balance: {round(total_balance, 2)}")
            print(f"Total Equity: {round(total_equity, 2)}")
            print(f"Total Today P/L: {round(total_today_pl, 2)}")
            print(f"Master Today P/L %: {round(master_today_pl_percent, 2)}")
            print(f"Master Daily DD %: {round(master_daily_dd_percent, 2)}")
            print(f"Master Peak DD %: {round(master_peak_dd_percent, 2)}")
            print("================================================")

            continue

        command = parse_command(user_input)
        if command:
            command["api_key"] = API_KEY
            
            # Parallel execution
            with ThreadPoolExecutor(max_workers=len(REMOTE_SERVERS)) as executor:
                futures = [
                    executor.submit(send_order, client, command)
                    for client in REMOTE_SERVERS
                ]

                # Wait for all to finish
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        print(f"⚠️ Thread error: {e}")
        else:
            print("⚠️ Invalid command. Type 'b', 's', 'd', 'q' or 'e'.")

if __name__ == "__main__":
    main()
