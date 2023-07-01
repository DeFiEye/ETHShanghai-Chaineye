import sys, os
from common import *
from typing import Any
from functools import partial
sess = requests.session()

Singleton_Asset = {}
class Asset:
    symbol: str
    place: str
    note: str


    def __init__(self, symbol, place, note=""):
        if getattr(self, "symbol", None):
            return
        self.symbol = symbol
        self.place = place
        self.note = note
        Singleton_Asset[(symbol, place)] = self
    
    def __hash__(self):
        return hash((self.symbol, self.place))
    
    def __eq__(self, other):
        return (self.symbol, self.place) == (other.symbol, other.place)
    
    def __str__(self):
        return self.symbol+"("+self.place+")"

class CEX_Asset(Asset):
    pass

class Chain_Asset(Asset):
    pass

class Chain_Asset_Accurate(Chain_Asset):
    address: str
    decimals: int
    bridge: str
    def __init__(self, symbol, place, address, decimals, bridge, note=""):
        super().__init__(symbol, place, note=note)
        self.address = address.lower()
        self.decimals = decimals
        self.bridge = bridge

    def __hash__(self):
        return hash((self.symbol, self.place, self.bridge))

    def __eq__(self, other):
        return (self.symbol, self.place, self.bridge) == (other.symbol, other.place, other.bridge)

    def __str__(self):
        return f"{self.symbol}({self.place}{(' '+self.bridge) if self.bridge else ''})"

chain_assets = {}
for chain in ChainTokenAddresses.keys():
    if chain not in CHAINWHITELIST:
        continue
    chain_assets[chain] = []
    for symbol in ChainTokenAddresses[chain].keys():
        if symbol not in TOKENWHITELIST:
            continue
        tokenDecimal = 18 if chain == "BSC" else TokenDecimals[symbol]
        if isinstance(ChainTokenAddresses[chain][symbol], str):
            chain_assets[chain].append(Chain_Asset_Accurate(symbol,chain,ChainTokenAddresses[chain][symbol],tokenDecimal,''))
        else:
            for bridge in ChainTokenAddresses[chain][symbol].keys():
                chain_assets[chain].append(Chain_Asset_Accurate(symbol,chain,ChainTokenAddresses[chain][symbol][bridge],tokenDecimal,bridge))

class AssetNotFound(Exception):
    pass
def getChainAsset(chain, symbol, _raise=True):
    candidates = [i for i in chain_assets.get(chain, []) if i.symbol == symbol]
    if len(candidates)>1:
        candidates = [i for i in candidates if i.bridge == 'Native']
    if not candidates:
        if _raise:
            raise AssetNotFound()
        else:
            return None
    return candidates[0]

def getChainAcurateAsset(chain, symbol, address, _raise=True):
    candidates = [i for i in chain_assets.get(chain, []) if i.symbol == symbol]
    if len(candidates)>1:
        candidates = [i for i in candidates if i.address == address]
    if not candidates:
        if _raise:
            raise AssetNotFound()
        else:
            return None
    return candidates[0]

EDGES = {}
class Action:
    from_asset: Asset
    to_asset: Asset
    quote: Any 
    def __init__(self, from_asset: Asset, to_asset: Asset, quote_function):
        self.from_asset = from_asset
        self.to_asset = to_asset
        self.quote = partial(quote_function, self)
        EDGES.setdefault(from_asset, []).append(self)
    def __str__(self):
        return f"{self.from_asset}->{self.to_asset}"

class CEX_Deposit_Paused(Exception):
    pass

class Bridge_Server_Error(Exception):
    pass

class Chain2CEX(Action):
    def __init__(self, from_asset, to_asset, can_deposit):
        assert isinstance(to_asset, CEX_Asset)
        def quote(act, amount):
            if not can_deposit:
                raise CEX_Deposit_Paused()
            fee = 0
            if act.from_asset.place in Chain2Id:
                chainid = Chain2Id[act.from_asset.place]
                gasprice = get_gasPrice(chainid)
                fee = gasprice*(65613 if chainid==1 else 36103)/1e18*get_price(ChainID2Native[chainid])
            return amount, fee
        super().__init__(from_asset, to_asset, quote)

def quote_1inch(act, amount):
    print("quote_1inch", act, amount)
    amount = amount*10**act.from_asset.decimals
    gas_price = get_gasPrice(act.chainid)

    x = GET(f'https://api.1inch.io/v5.0/{act.chainid}/quote?'\
                f'fromTokenAddress={act.from_asset.address}'\
                f'&toTokenAddress={act.to_asset.address}'\
                f'&amount={amount}')
    r = x.json()
    #print(r)
    return int(r["toTokenAmount"])/10**r['toToken']['decimals'], gas_price*int(r['estimatedGas'])/1e18*get_price(ChainID2Native[act.chainid])

def quote_paraswap(act, amount):
    gas_price = get_gasPrice(act.chainid)
    x = GET(f'https://api.paraswap.io/prices/?side=SELL&network={act.chainid}&'\
                    f'srcToken={act.from_asset.address}&srcDecimals={act.from_asset.decimals}'\
                    f'&destToken={act.to_asset.address}&destDecimals={act.to_asset.decimals}'\
                    f'&amount={int(amount*10**act.from_asset.decimals)}')
    r = x.json()
    #print(r)
    return int(r["priceRoute"]["destAmount"])/10**act.to_asset.decimals, float(r["priceRoute"]["gasCostUSD"])


class Chain2Chain(Action):
    chainid: int
    dex: str
    def __init__(self, from_asset, to_asset, quote_function):
        assert isinstance(from_asset, Chain_Asset_Accurate)
        assert isinstance(to_asset, Chain_Asset_Accurate)
        assert from_asset != to_asset, "same token"
        assert from_asset.place == to_asset.place
        chainid = Chain2Id[from_asset.place]
        self.chainid = chainid
        super().__init__(from_asset,to_asset,quote_function)
    def __str__(self):
        return f"{self.from_asset}->{self.to_asset} via {self.dex}"

class Chain2Chain_1inch(Chain2Chain):
    def __init__(self, from_asset, to_asset):
        self.dex = "1inch"
        self.hint = "1inch"
        super().__init__(from_asset, to_asset, quote_1inch)
        assert self.chainid in [1, 56, 137, 10, 42161, 100, 43114, 250, 8217, 1313161554, 23448594291968334, 324, 42161], f"{self.chainid} not supported by 1inch"

class Chain2Chain_Paraswap(Chain2Chain):
    def __init__(self, from_asset, to_asset):
        self.dex = "paraswap"
        self.hint = "paraswap"
        super().__init__(from_asset, to_asset, quote_paraswap)
        assert self.chainid in [1, 137, 56, 43114, 250, 42161, 10], f"{self.chainid} not supported by paraswap"
        

class UnknownFee(Exception):
    pass

def quote_chaineye(act, amount):
    assert isinstance(act, Chain2Bridge_ChainEye)
    tmp = ("/"+act.bridge) if act.query_twostep else ""
    url = f"https://api.chaineye.tools/api/v1/crosschain/estimateFee{tmp}?token={act.from_asset.symbol}&srcchain={act.from_asset.place}&dstchain={act.to_asset.place}&amount={amount}"
    x = GET(url, headers={"origin":"prod"}, cachetime=600)
    if not x.status_code==200:
        raise UnknownFee(x)
    candidates = [i for i in x.json() if i["bridge"].lower()==act.bridge.lower()]
    if not candidates:
        raise UnknownFee("bridge not found")
    b = candidates[0]
    if b["fee_status"]!="ok":
        raise UnknownFee("chaineye not ok")
    return b['received'], b["total_fee_usd"]-get_price(act.from_asset.symbol)*(amount-b['received'])

class Chain2Bridge(Action):
    bridge: str
    bridgeName: str
    website: str
    bridge_fee: str
    def __init__(self, from_asset, to_asset, bridge, bridgeName, website, quote_function):
        assert isinstance(from_asset, Chain_Asset_Accurate)
        assert isinstance(to_asset, Chain_Asset_Accurate)
        self.bridge = bridge
        self.hint = bridge
        self.bridgeName = bridgeName
        self.website = website
        super().__init__(from_asset, to_asset, quote_function)
    def __str__(self):
        return f"{self.from_asset}->{self.to_asset} via {self.bridgeName}"

class Chain2Bridge_ChainEye(Chain2Bridge):
    def __init__(self, from_asset, to_asset, bridge, bridgeName, website, query_twostep):
        self.query_twostep = query_twostep
        super().__init__(from_asset, to_asset, bridge, bridgeName, website, quote_chaineye)

class Amount_Not_Enough(Exception):
    pass

class CEX_Withdraw_Paused(Exception):
    pass

class CEX2Chain(Action):
    def __init__(self, from_asset, to_asset, can_withdraw, min_withdraw, withdraw_fee):
        min_withdraw: float
        withdraw_fee: float
        assert isinstance(from_asset, CEX_Asset)
        self.min_withdraw = min_withdraw
        self.withdraw_fee = withdraw_fee
        def quote(act, amount):
            if amount<min_withdraw:
                raise Amount_Not_Enough()
            if not can_withdraw:
                raise CEX_Withdraw_Paused()
            return amount-withdraw_fee, 0
        super().__init__(from_asset, to_asset, quote)

class CEX2CEX(Action):
    def __init__(self, cex2chain, chain2cex):
        assert isinstance(cex2chain.from_asset, CEX_Asset)
        assert isinstance(cex2chain.to_asset, Chain_Asset)
        assert cex2chain.to_asset == chain2cex.from_asset
        assert isinstance(chain2cex.to_asset, CEX_Asset)
        self.cex2chain = cex2chain
        self.chain2cex = chain2cex
        def quote(act, amount):
            out1, fee1 = act.cex2chain.quote(amount)
            out2, fee2 = act.chain2cex.quote(out1)
            return out2, fee1+fee2
        super().__init__(cex2chain.from_asset, chain2cex.to_asset, quote)
    #def __str__(self):
    #    return f"{self.symbol}({self.from_asset.place}->{self.to_asset.place} via {self.cex2chain.to_asset.place})"


def EDGE_iterate(asset_cls, route_cls):
    for from_asset, routes in EDGES.copy().items():
        if isinstance(from_asset, asset_cls):
            for route in routes:
                if isinstance(route, route_cls):
                    yield from_asset, route


def print_routes(routes, end="\n", do_print=True):
    res = []
    for r in routes:
        res.append(str(r.from_asset))
        if getattr(r, "hint", None):
            res.append(r.hint+"->")
        else:
            res.append("->")
    res.append(str(r.to_asset))
    if do_print:
        print(" ".join(res), end=end)
    return res
