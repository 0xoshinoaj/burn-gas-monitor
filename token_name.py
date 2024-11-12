from web3 import Web3
from config import WEB3_PROVIDER

# 连接到以太坊节点
w3 = Web3(Web3.HTTPProvider(WEB3_PROVIDER))

# ERC-20 合约 ABI（只需包含 name() 函数）
abi = [
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "payable": False,
        "stateMutability": "view",
        "type": "function"
    }
]

def get_token_name(contract_address):
    try:
        # 将地址转换为校验和格式
        checksum_address = w3.to_checksum_address(contract_address)
        
        # 创建合约实例
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        
        # 调用 name() 函数
        token_name = contract.functions.name().call()
        return token_name
    except Exception as e:
        print(f"无法获取代币名称: {e}")
        return "未知"  # 返回一个默认值
