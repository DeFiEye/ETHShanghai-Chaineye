import requests
from functools import lru_cache
sess = requests.session()
from config import STARKNET_URL

chartMap = {
    "transactions": 2012,
    "users": 2013,
    "wallet": 2011
}


@lru_cache()
def get_stark_tx(_ts):
    result = []
    chart_id = chartMap["transactions"]
    url = STARKNET_URL + chart_id
    res = sess.get(url).json()
    if res:
        response = res["data"]["list"]
        for item in response:
            daily = {
                "time": item["first_tx"],
                "transactions": item["tx_hashs_per_day"]
            }
            result.append(daily)
    return result


@lru_cache()
def get_stark_user(_ts):
    result = []
    chart_id = chartMap["users"]
    url = STARKNET_URL + chart_id
    res = sess.get(url).json()
    if res:
        response = res["data"]["list"]
        for item in response:
            daily = {
                "time": item["date"],
                "active users": item["distinct_users"],
                "new users": item["new_users"]
            }
            result.append(daily)
    return result


@lru_cache()
def get_stark_wallet(_ts):
    result = []
    chart_id = chartMap["wallet"]
    url = STARKNET_URL + chart_id
    res = sess.get(url).json()
    if res:
        response = res["data"]["list"]
        for item in response:
            daily = {
                "time": item["first_tx"],
                "total wallets": item["cumulative_new"]
            }
            result.append(daily)
    return result
