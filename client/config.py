# config.py - Remote desktop configuration
# List up to 10 clients
REMOTE_SERVERS = [
    {"id": "MQ1-100k", "host": "127.0.0.1", "port": 5001, "lot": 0.50},
    {"id": "MQ2-100k", "host": "127.0.0.1", "port": 5002, "lot": 0.50},
    {"id": "MQ3-100k", "host": "127.0.0.1", "port": 5003, "lot": 0.50},
    {"id": "MQ4-100k", "host": "127.0.0.1", "port": 5004, "lot": 0.50},
    {"id": "MQ5-100k", "host": "127.0.0.1", "port": 5005, "lot": 0.50},
    {"id": "MQM-100k", "host": "127.0.0.1", "port": 5000, "lot": 0.50},
    # add more up to Client 10...
]


# Forex Broker     - Account ID - Types   - Account Size - Account Bal   - Lot Size
# GOATFundedTrader - 314437952  - Step1   - 5000 USD     - 4694.15       - 0.02
# GOATFundedTrader - 314437953  - Step1   - 5000 USD     - 4686.76       - 0.02
# GOATFundedTrader - 314437954  - Step1   - 5000 USD     - 4841.79       - 0.02
# FundingPips      - 11493313   - Step1   - 5000 USD     - 4633.96       - 0.01
# FundingPips      - 11493342   - Step1   - 5000 USD     - 4614.09       - 0.01
# FundingPips      - 11493370   - Step1   - 5000 USD     - 4640.12       - 0.01

# Shared secret for REST calls
API_KEY = "YourSecureApiKeyHere"
#API_ENDPOINT = "http://192.168.29.133:5000/trade"

