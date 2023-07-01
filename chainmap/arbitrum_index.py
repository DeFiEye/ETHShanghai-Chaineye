from dune_provider import query_dune
from functools import lru_cache
import requests
from config import ARBITRUM_URL

sess = requests.session()

@lru_cache()
def get_arbitrum_index(_ts):
    result = []
    arbitrum_data = query_dune(2447723)
    response = sess.get(ARBITRUM_URL).json()
    tvl_data = response["daily"]["data"][-91:]
    for index, item in enumerate(arbitrum_data):
        result.append(
            {
                "date": item["block_date"],
                "unique users": item["daily_unique_users"],
                "transactions": item["daily_txn"],
                "tvl_usd": tvl_data[index][1]
            }
        )
    return result


if __name__ == '__main__':
    print(get_arbitrum_index(1))

