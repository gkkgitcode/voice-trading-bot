# config.py - Remote desktop configuration
# List up to 10 clients
REMOTE_SERVERS = [
    {"id": "Server1-GOAT1-5K", "host": "127.0.0.1", "port": 5001, "lot": 0.02},
    {"id": "Server2-GOAT2-5K", "host": "127.0.0.1", "port": 5002, "lot": 0.02},
    {"id": "Server3-GOAT3-5K", "host": "127.0.0.1", "port": 5003, "lot": 0.02},
    {"id": "Server4-FNDPP1-5K", "host": "127.0.0.1", "port": 5004, "lot": 0.01},
    {"id": "Server5-FNDPP2-5K", "host": "127.0.0.1", "port": 5005, "lot": 0.01},
    {"id": "ServerM-FNDPP3-5K", "host": "127.0.0.1", "port": 5000, "lot": 0.01},
    # add more up to Client 10...
]


# Clients   - Forex Broker     - Account ID - Types   - Account Size - Account Bal   - Lot Size
# Client 1  - GOATFundedTrader - 314437952  - Step1   - 5000 USD     - 4719.87       - 0.02
# Client 2  - GOATFundedTrader - 314437953  - Step1   - 5000 USD     - 4713.72       - 0.02
# Client 3  - GOATFundedTrader - 314437954  - Step1   - 5000 USD     - 4867.49       - 0.02
# Client 4  - FundingPips      - 11493313   - Step1   - 5000 USD     - 4661.88       - 0.01
# Client 5  - FundingPips      - 11493342   - Step1   - 5000 USD     - 4642.07       - 0.01
# Client 6  - FundingPips      - 11493370   - Step1   - 5000 USD     - 4667.28       - 0.01

# Shared secret for REST calls
API_KEY = "YourSecureApiKeyHere"
#API_ENDPOINT = "http://192.168.29.133:5000/trade"

