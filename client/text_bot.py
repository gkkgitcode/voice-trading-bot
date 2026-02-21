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

        if user_input == 'd':
            results = []

            with ThreadPoolExecutor(max_workers=len(REMOTE_SERVERS)) as executor:
                futures = [executor.submit(get_dashboard, client) for client in REMOTE_SERVERS]

                for future in as_completed(futures):
                    results.append(future.result())

            # PRINT CLEANLY AFTER THREADS FINISH
            for server_id, data in results:
                print(f"\n📊 {server_id} Dashboard")
                for k, v in data.items():
                    print(f"   {k}: {v}")

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
