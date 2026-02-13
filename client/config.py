# config.py - Remote desktop configuration
# List up to 10 clients
REMOTE_SERVERS = [
    {"id": "Client 1", "host": "192.168.1.3", "port": 5000},
    {"id": "Client 2", "host": "192.168.1.3", "port": 5001},
    {"id": "Client 3", "host": "192.168.1.3", "port": 5002},
    {"id": "Client 4", "host": "192.168.1.3", "port": 5003},
    {"id": "Client 5", "host": "192.168.1.3", "port": 5004},
    {"id": "Client 6", "host": "192.168.1.3", "port": 5005},
    # add more up to Client 10...
]

# Shared secret for REST calls
API_KEY = "YourSecureApiKeyHere"
#API_ENDPOINT = "http://192.168.29.133:5000/trade"

