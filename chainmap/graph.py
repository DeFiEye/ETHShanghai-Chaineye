from config import THEGRAPH_KEY
from python_graphql_client import GraphqlClient


graph_arbitrum_id_dict = {
    "camelot": "8zagLSufxk5cVhzkzai3tyABwJh53zxn9tmUYJcJxijG",
    "uniswap V3": "FQ6JYszEKApsBpAmiHesRsd9Ygc6mzmpNRANeVQFYoVX",
    "aave": "4xyasjQeREe7PxnF6wVdobZvCw5mhoHZq3T7guRpuNPf",
    "sushi V3": "3oHCddbQGTi42kPZBwyGzD2JzZR33zK2MwXtxAerNJy2",
    "radiant": "8PUSqUn6dSkoxJb3LDLmdKHzbHFn1cz7XjbSob5uiR4v",
    "convex": "7rFZ2x6aLQ7EZsNx8F5yenk4xcqwqR3Dynf9rdixCSME",
    "abracadabra": "3m97d2dJ2pXwPFuiHrm8T37V9TCoAHBpMqRwdguyUZXF",
    "chronos": "FZh7YNb6NjtpBEAHqArkUgAnU9UBSZjMtnwjGwzGNUR"
}

stable_coins = ["USDT", "USDC", "DAI", "USDP", "TUSD", "FRAX"]

graph_query_url = "https://gateway-arbitrum.network.thegraph.com/api/" + THEGRAPH_KEY + "/subgraphs/id/"
query = """
    query {
        tokens(first: 5, orderBy: tradeVolumeUSD, orderDirection: desc) {
            id
            name
            symbol
            decimals
        }
    }
"""


def get_top_tokens(project):
    subgraph_id = graph_arbitrum_id_dict.get(project, None)
    result = []
    if subgraph_id:
        url = graph_query_url + subgraph_id
        client = GraphqlClient(endpoint=url)
        tokens = client.execute(query=query)["data"]["tokens"]
        for token in tokens:
            if token["symbol"] not in stable_coins:
                result.append({
                    "address": token["id"],
                    "symbol": token["symbol"],
                    "name": token["name"],
                    "decimals": token["decimals"]
                })
    return result


if __name__ == '__main__':
    print(get_top_tokens("camelot"))