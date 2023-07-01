
from asset import *
from config import BRIDGE_URL, INFO_URL

bridge_url = BRIDGE_URL
basicInfo = sess.get(INFO_URL).json()


def bridgeAssets(from_asset, to_asset, amount):
    headers = {"origin": "prod"}
    url = BRIDGE_URL + "?token={}&srcchain[]={}&dstchain={}&amount={}".format(from_asset.symbol, from_asset.place, to_asset.place, amount)
    response = GET(url, headers=headers, cachetime=600)
    existing_bridges = set()
    if response and response.status_code == 200:
        bridges = response.json()
        for bridge in bridges:
            bridge_name = bridge["bridge"].lower()
            if bridge_name in existing_bridges or bridge_name in CEXWHITELIST or bridge_name in BRIDGE_BLACKLIST:
                continue
            if to_asset.place != "StarkNet": # StarkNet has a different contract address system
                if bridge["srctoken_contract"].lower() != from_asset.address.lower() or bridge["dsttoken_contract"].lower() != to_asset.address.lower():
                    continue
            existing_bridges.add(bridge_name)
            website = ""
            if bridge_name in basicInfo:
                website = basicInfo[bridge_name]["url"]
                bridge_name = basicInfo[bridge_name]["display_name"]
            if bridge["fee_status"] == "ok":
                Chain2Bridge_ChainEye(from_asset, to_asset, bridge["bridge"], bridge_name, website, False)
            elif bridge["fee_status"] == "ok_LOAD" or bridge["fee_status"] == "LOAD":
                Chain2Bridge_ChainEye(from_asset, to_asset, bridge["bridge"], bridge_name, website, True)

for from_chain in chain_assets:
    if from_chain not in CHAINWHITELIST:
        continue
    for to_chain in SUPPORTED_CHAINS:
        if to_chain not in CHAINWHITELIST:
            continue
        if from_chain == to_chain:
            continue
        from_assets = chain_assets[from_chain]
        to_assets = chain_assets[to_chain]
        for from_asset in from_assets:
            amt = 1000 if from_asset.symbol in ["USDT", "BUSD", "DAI", "USDC", "OP"] else 0.5
            for to_asset in to_assets:
                if from_asset.symbol != to_asset.symbol:
                    continue
                bridgeAssets(from_asset, to_asset, amt)  # 这里传入跨链Amount

def load_bridge():
    res = {}
    for from_asset, route in EDGE_iterate(Chain_Asset_Accurate, Chain2Bridge):
        if route.bridge in BRIDGE_BLACKLIST:
            continue
        print(route, end=" ", flush=True)
        amt = 1000 if route.from_asset.symbol in ["USDT", "BUSD", "DAI", "USDC", "OP"] else 0.5
        try:
            out, extrafee = route.quote(amt)
            if extrafee<0.01:
                extrafee = 0
            totalfee = amt*get_price(route.from_asset)-out*get_price(route.to_asset) + extrafee
            diff = amt - out if route.from_asset.symbol == route.to_asset.symbol else 0
            print(out, extrafee, "=", totalfee)
            res[route] = (diff, totalfee)
        except:
            print("bridge failed")
    return res


