from config import CHAINBASE_KEY
import requests
import json
chainbase_url = "https://optimism-mainnet.s.chainbase.online/v1/" + CHAINBASE_KEY
headers = {
    "accept": "application/json",
    "content-type": "application/json"
}


def get_block_number():
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_blockNumber"
    }
    response = requests.post(chainbase_url, json=payload, headers=headers)
    return json.loads(response.text)["result"]


def hex2decimal(hex_string):
    return int(hex_string, 16)


def decimal2hex(decimal):
    return hex(decimal)


def get_block_time(block_number):
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_getBlockByNumber",
        "params": [block_number, False]
    }
    response = requests.post(chainbase_url, json=payload, headers=headers)
    return json.loads(response.text)["result"]["timestamp"]


def create_filter(from_block, to_block, address, topics):
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_newFilter",
        "params": [
            {
                "toBlock": decimal2hex(to_block),
                "fromBlock": decimal2hex(from_block),
                "topics": topics,
                "address": address
            }
        ]
    }
    response = requests.post(chainbase_url, json=payload, headers=headers)

    if json.loads(response.text).get("result", None) is None:
        print("creat filter failed")
        print(response.text)
    return json.loads(response.text)["result"]


def get_filter_change(filter_id):
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_getFilterChanges",
        "params": [filter_id]
    }
    response = requests.post(chainbase_url, json=payload, headers=headers)
    if json.loads(response.text).get("result", None) is None:
        print("get filter failed")
        print(response.text)

    return json.loads(response.text)["result"]


def uninstall_filter(filter_id):
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "eth_uninstallFilter",
        "params": [filter_id]
    }
    response = requests.post(chainbase_url, json=payload, headers=headers)
