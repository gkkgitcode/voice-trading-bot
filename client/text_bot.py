import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import REMOTE_SERVERS, API_KEY
from command_parser import parse_command

# Settings
#SERVER_URL = "http://192.168.29.133:5000/trade"  # Your Flask server
API_KEY = "YourSecureApiKeyHere"  # Match the value in your trade_api.py


def send_order(client, command):
    """Send order to a single client"""
    url = f"http://{client['host']}:{client['port']}/trade"

    client_command = command.copy()

    # Add lot size only for buy/sell
    if client_command["action"] in ["buy", "sell"]:
        if "lot" not in client:
            raise ValueError(f"Lot size missing for {client['id']}")
        client_command["volume"] = client["lot"]

    print(f"➡️ Sending to {client['id']} → {url} → {client_command}")

    try:
        response = requests.post(url, json=client_command, timeout=10)
        print(f"✅ {client['id']} responded: {response.text}")
    except Exception as e:
        print(f"❌ Error sending to {client['id']}: {e}")

def main():
    print("💬 Text Command Mode (type 'b', 's', or 'e' to exit; 'q' to quit)")

    while True:
        user_input = input("Enter command: ").strip().lower()

        if user_input == 'q':
            print("👋 Quitting text command bot...")
            break

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

            # # 🚀 Send to all configured remote servers
            # for client in REMOTE_SERVERS:
            #     url = f"http://{client['host']}:{client['port']}/trade"
                
            #     client_command = command.copy()

            #     # Add lot size only for buy/sell
            #     if client_command["action"] in ["buy", "sell"]:
            #         client_command["volume"] = client.get("lot", 0.01)
            #     print(f"➡️ Sending to {client['id']} → {url} → {client_command}")

            #     try:
            #         response = requests.post(url, json=client_command, timeout=10)
            #     # print(f"➡️ Sending to {client['id']} → {url} → {command}")
            #     # try:
            #     #     response = requests.post(url, json=command, timeout=10)
            #         print(f"✅ {client['id']} responded: {response.text}")
            #     except Exception as e:
            #         print(f"❌ Error sending to {client['id']}: {e}")
        else:
            print("⚠️ Invalid command. Type 'b', 's', or 'e'.")

if __name__ == "__main__":
    main()
