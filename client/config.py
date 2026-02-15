# config.py - Remote desktop configuration
# List up to 10 clients
REMOTE_SERVERS = [
    {"id": "Client 1 - GOAT1 - 5K", "host": "192.168.1.3", "port": 5001, "lot": 0.01},
    {"id": "Client 2 - GOAT2 - 5K", "host": "192.168.1.3", "port": 5002, "lot": 0.01},
    {"id": "Client 3 - GOAT3 - 5K", "host": "192.168.1.3", "port": 5003, "lot": 0.02},
    {"id": "Client 4 - FNDPP1 - 5K", "host": "192.168.1.3", "port": 5004, "lot": 0.01},
    {"id": "Client 5 - FNDPP2 - 5K", "host": "192.168.1.3", "port": 5005, "lot": 0.02},
    {"id": "Client Master - FNDPP3 - 5K", "host": "192.168.1.3", "port": 5000, "lot": 0.01},
    # add more up to Client 10...
]

# Clients   - Forex Broker     - Account ID - Types   - Account Size - Account Bal   - Lot Size
# Client 1  - GOATFundedTrader - 314437952  - Step1   - 5000 USD     - 4671          - 0.01
# Client 2  - GOATFundedTrader - 314437953  - Step1   - 5000 USD     - 4663          - 0.01
# Client 3  - GOATFundedTrader - 314437954  - Step1   - 5000 USD     - 4805          - 0.02
# Client 4  - FundingPips      - 11493313   - Step1   - 5000 USD     - 4639          - 0.01
# Client 5  - FundingPips      - 11493342   - Step1   - 5000 USD     - 4730          - 0.02
# Client 6  - FundingPips      - 11493370   - Step1   - 5000 USD     - 4641          - 0.01

# Shared secret for REST calls
API_KEY = "YourSecureApiKeyHere"
#API_ENDPOINT = "http://192.168.29.133:5000/trade"

