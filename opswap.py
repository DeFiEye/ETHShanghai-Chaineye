from web3 import Web3
import time
import json

from util import get_block_number, hex2decimal, create_filter, get_filter_change, get_block_time, uninstall_filter

filter_provider = ['https://endpoints.omniatech.io/v1/op/mainnet/public','https://optimism.blockpi.network/v1/rpc/6183d79c5158904466f2316bb71460aaeadf51cd', 'https://opt-mainnet.g.alchemy.com/v2/j6ojwgnIlFClhRbRusTqxOquhhyJi9h8']
pool_names = ['Uni WETH-OP-0.3%','Uni OP-USDC-0.3%']
pool_addresses = ['0x68f5c0a2de713a54991e01858fd27a3832401849','0x1C3140aB59d6cAf9fa7459C6f83D4B52ba881d36']
coin_names = [['WETH','OP'],['OP','USDC']]
swap_event_topic = {"Uni":'0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'}
threshhold = 10
data_len = 200
file_path = "./data/op_swap.json"

coin = {
    "USDC":{
        "address":'0x7F5c764cBc14f9669B88837ca1490cCa17c31607',
        "decimal":1e6
    },
    "OP":{
        "address":'0x4200000000000000000000000000000000000042',
        "decimal":1e18
    },
    "WETH":{
        "address":'0x4200000000000000000000000000000000000006',
        "decimal":1e18
    }
}


def twos_complement(hex_str, num_bits):
    bin_str = bin(int(hex_str, 16))[2:]
    value = (int(bin_str, 2) ^ (1 << num_bits) - 1) + 1
    if bin_str[0] == '1':
        value = -value
    return value


class Swap:

    def __init__(self):
        self.fliters = []
        self.now_block = hex2decimal(get_block_number()) - 200
        for i in range(len(pool_names)):
            host = pool_names[i].split(" ")[0]
            topic = swap_event_topic[host]
            address = pool_addresses[i]
            self.fliters.append({"address":Web3.toChecksumAddress(address),"name":pool_names[i],"topic":topic,"host":host,"coins":coin_names[i]})
        self.data = {}
        self.run()

    def run(self):
        while True:
            try:
                new_block = hex2decimal(get_block_number())
                print(self.now_block,new_block,"swap")
                if new_block - self.now_block >= 200:
                    for i in self.fliters:
                        filter_id = create_filter(max(self.now_block+1,new_block-400), new_block, i['address'], [i['topic']])
                        log_entries = get_filter_change(filter_id)
                        uninstall_filter(filter_id)
                        for j in log_entries:
                            block = j['blockNumber']
                            timestamp = hex2decimal(get_block_time(block))
                            hash = j['transactionHash'].hex()
                            address = j['address']
                            topics = j['topics']
                            event_data = j['data']
                            split_event_data = []
                            index = 2
                            while index<len(event_data):
                                split_event_data.append(event_data[index:index+64])
                                index+=64
                            for k in range(len(topics)):
                                topics[k] = topics[k].hex()
                            if i['host']=='Uni':
                                if int(split_event_data[1],16) > 0 and int(split_event_data[1],16) < 1e50:
                                    from_volume = -int(twos_complement(split_event_data[0], 64*4))/coin[i['coins'][0]]['decimal']
                                    to_volume = int(split_event_data[1],16)/coin[i['coins'][1]]['decimal']
                                    if i['coins'][1]=='OP' and to_volume>threshhold or i['coins'][0]=='OP' and from_volume>threshhold:
                                        if block not in self.data.keys():
                                            self.data[block] = []
                                        self.data[block].append({"timestamp":timestamp,"swapFrom":i['coins'][0],'swapTo':i['coins'][1],'fromVolume':from_volume,'toVolume':to_volume,'transcationHash':hash,'pool_address':address,"pool_name":i['name']})
                                else:
                                    from_volume = -int(twos_complement(split_event_data[1], 64*4))/coin[i['coins'][1]]['decimal']
                                    to_volume = int(split_event_data[0],16)/coin[i['coins'][0]]['decimal']
                                    if i['coins'][0]=='OP' and to_volume>threshhold or i['coins'][1]=='OP' and from_volume>threshhold:
                                        if block not in self.data.keys():
                                            self.data[block] = []
                                        self.data[block].append({"timestamp":timestamp,"swapFrom":i['coins'][1],'swapTo':i['coins'][0],'fromVolume':from_volume,'toVolume':to_volume,'transcationHash':hash,'pool_address':address,"pool_name":i['name']})                 
                    if len(self.data.keys())>data_len:
                        key_list = sorted(list(self.data.keys()), key=lambda x: int(x))
                        for i in key_list[:-data_len]:
                            del self.data[i]
                    self.now_block = new_block
                    with open(file_path, "w") as output:
                        json.dump(self.data, output)
            except Exception as e:
                print(e)
                time.sleep(30)
            time.sleep(30)


if __name__ == '__main__':
    Swap()
