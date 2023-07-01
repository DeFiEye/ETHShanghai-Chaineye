from graph_provider import query_graph
from functools import lru_cache
from config import zkSync_query_code


@lru_cache()
def get_zksync_index(_ts):
    result = []
    zksync_data = query_graph(zkSync_query_code)
    for item in zksync_data:
        result.append(
            {
                "date": item["date"],
                "unique_wallets": item["unique_wallets"],
                "total_value": item["total_value"]
            }
        )
    return result


if __name__ == '__main__':
    print(get_zksync_index(1))

