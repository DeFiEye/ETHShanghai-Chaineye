import time
import json

from util import get_block_number, hex2decimal, create_filter, get_filter_change, get_block_time, uninstall_filter

filter_provider = ['https://optimism.blockpi.network/v1/rpc/6183d79c5158904466f2316bb71460aaeadf51cd', 'https://opt-mainnet.g.alchemy.com/v2/j6ojwgnIlFClhRbRusTqxOquhhyJi9h8']
pool_names = ['Uni WETH-OP-0.3%','Uni OP-USDC-0.3%']
pool_addresses = ['0x68f5c0a2de713a54991e01858fd27a3832401849','0x1C3140aB59d6cAf9fa7459C6f83D4B52ba881d36']
coin_names = [['WETH','OP'],['OP','USDC']]
swap_event_topic = {"Uni":'0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'}
threshhold = 10
data_len = 200
file_path = "./data/op_transfer.json"

address_tag = {
    '0x2501c477d0a35545a387aa4a3eee4292a9a8b3f0': 'Optimism: Foundation',
    '0xfedfaf1a10335448b7fa0268f56d2b44dbd357de': 'Optimism: Airdrop',
    '0xacd03d601e5bb1b275bb94076ff46ed9d753435a': 'Binance 1',
    '0xd6216fc19db775df9774a6e33526131da7d19a2c': 'KuCoin3',
    '0x0d162447b8df47c2e7910441bf3c8c1b55b9b124': 'Uniswap: Uniswap Grants Program',
    '0x392ac17a9028515a3bfa6cce51f8b70306c6bd43': 'Stargate Finance: Multisig',
    '0xa3f45e619ce3aae2fa5f8244439a66b203b78bcc': 'KuCoin',
    '0xdf90c9b995a3b10a5b8570a47101e6c6a29eb945': 'MEXC: OP Hot Wallet',
    '0xebb8ea128bbdff9a1780a4902a9380022371d466': 'KuCoin2',
    '0x60b28637879b5a09d21b68040020ffbf7dba5107': 'Wintermute/OP Exploiter',
    '0xc224bf25dcc99236f00843c7d8c4194abe8aa94a': 'Alchemix Finance: Optimism Multisig',
    '0x4645e0952678e9566fb529d9313f5730e4e1c412': 'Iron Bank: iOP Token',
    '0x4dea9e918c6289a52cd469cac652727b7b412cd2': 'Stargate Finance: LP Staking Time',
    '0x4200000000000000000000000000000000000042': 'Optimism: OP Token',
    '0x1470c87e2db5247a36c60de3d65d7c972c62ea0f': 'PoolTogether: Twab Rewards',
    '0xc35dadb65012ec5796536bd9864ed8773abc74c4': 'SushiSwap: BentoBoxV1',
    '0xf0694acc9e941b176e17b9ef923e71e7b8b2477a': '1inch',
    '0xa3128d9b7cca7d5af29780a56abeec12b05a6740': '0x: Flash Wallet',
    '0xba12222222228d8ba445958a75a0704d566bf2c8': 'Vault'
}


class Transfer:

    def __init__(self):
        time.sleep(30)
        self.now_block = hex2decimal(get_block_number()) - 200
        self.data = {}
        self.run()

    def run(self):
        while True:
            new_block = hex2decimal(get_block_number())
            try:
                print(self.now_block,new_block,"transfer")
                if new_block - self.now_block >= 200:
                    filter_id = create_filter(max(self.now_block + 1, new_block - 400), new_block, "0x4200000000000000000000000000000000000042", ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'])
                    log_entries = get_filter_change(filter_id)
                    uninstall_filter(filter_id)
                    for j in log_entries:
                        block = j['blockNumber']
                        timestamp = hex2decimal(get_block_time(block))
                        hash = j['transactionHash'].hex()
                        topics = j['topics']
                        event_data = j['data']
                        split_event_data = [event_data[2:66]]
                        for k in range(len(topics)):
                            topics[k] = topics[k].hex()
                        if int(split_event_data[0],16)>threshhold*1e18:
                            if block not in self.data.keys():
                                self.data[block] = []
                            from_tag = ''
                            to_tag = ''
                            if '0x'+topics[1][26:] in address_tag.keys():
                                from_tag = address_tag['0x'+topics[1][26:]]
                            if '0x'+topics[2][26:] in address_tag.keys():
                                to_tag = address_tag['0x'+topics[2][26:]]
                            self.data[block].append({"from_tag":from_tag,"to_tag":to_tag,"timestamp":timestamp,"from":'0x'+topics[1][26:],'to':'0x'+topics[2][26:],'volume':int(split_event_data[0],16)/1e18,'transcationHash':hash})
                    if len(self.data.keys())>data_len:
                        key_list = sorted(list(self.data.keys()), key=lambda x: int(x))
                        for i in key_list[:-data_len]:
                            del self.data[i]
                    with open(file_path, "w") as output:
                        json.dump(self.data, output)
            except Exception as e:
                print(e)
            self.now_block = new_block
            time.sleep(30)


if __name__ == '__main__':
    Transfer()
