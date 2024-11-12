#-*-codint:utf-8-*-
import requests
from fake_useragent import UserAgent, FakeUserAgentError
import json
import os
import time
from discord_webhook import DiscordWebhook, create_webhook  # 导入 DiscordWebhook 类和 create_webhook 函数
from datetime import datetime, timedelta
from token_name import get_token_name  # 导入 get_token_name 函数

try:
    ua = UserAgent()
    headers = {"User-Agent": ua.random}
except FakeUserAgentError:
    # 使用一个默认的用户代理
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

s = requests.session()
s.headers.update(headers)

# 设置抓取数量，默认是20
max_fetch_count = 12 

# 创建 DiscordWebhook 实例
DISCORD_WEBHOOK_URLS = create_webhook()  # 从 discord_webhook.py 获取 Webhook URLs
discord_webhook = DiscordWebhook(DISCORD_WEBHOOK_URLS)  # 创建 DiscordWebhook 实例

# 读取现有地址和名称
def load_existing_addresses(filename='addresses.txt'):
    existing_addresses = {}
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            for line in file:
                parts = line.strip().split(',')
                # 确保只有两个部分，并且没有特殊字符
                if len(parts) == 2 and all(part.isprintable() for part in parts):
                    address, nickname = parts
                    existing_addresses[address] = nickname
                else:
                    print(f"跳过无效行: {line.strip()}")  # 打印无效行以便调试
    return existing_addresses

# 保存新地址和名称到文件
def save_address(address, nickname, filename='addresses.txt'):
    with open(filename, 'a') as file:
        file.write(f"{address},{nickname}\n")

# 读取代理设置
def load_proxies(filename='proxy.txt'):
    proxies = []
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            for line in file:
                # 假设格式为 IP:PORT:USER:PASSWORD:TYPE
                parts = line.strip().split(':')
                if len(parts) == 5:
                    ip, port, user, password, proxy_type = parts
                    proxy = {
                        "http": f"{proxy_type}://{user}:{password}@{ip}:{port}",
                        "https": f"{proxy_type}://{user}:{password}@{ip}:{port}"
                    }
                    proxies.append(proxy)
    return proxies

# ANSI 转义序列，用于设置文本颜色
GREEN = "\033[92m"
RESET = "\033[0m"

# 新增一个字典来跟踪连续上榜次数
consecutive_counts = {}

# 设置输出频率（例如每小时输出一次）
output_interval = 600  # 600秒 = 10分鐘
last_output_time = time.time()  # 记录上次输出的时间

# 主循环
while True:
    # 从代理文件中加载代理
    proxies = load_proxies()
    if not proxies:
        print("没有找到可用的代理。")
        break

    # 初始化一个标志来跟踪请求是否成功
    request_success = False

    # 尝试使用代理进行请求
    for attempt in range(len(proxies)):
        proxy = proxies[attempt]  # 选择当前代理
        try:
            r1 = s.get("https://ultrasound.money/#burn", proxies=proxy, timeout=10)
            r2 = s.get("https://ultrasound.money/api/fees/grouped-analysis-1", proxies=proxy, timeout=10)

            # 假设 r2 的内容是 JSON 格式
            if r2.status_code == 200:
                response_data = r2.json()
                leaderboard5m_data = response_data.get('leaderboards', {}).get('leaderboard5m', [])
                
                existing_addresses = load_existing_addresses()  # 加载现有地址和昵称

                count = 1  # 初始化计数器
                # 获取当前 UTC 时间
                utc_now = datetime.utcnow()
                # 将 UTC 时间转换为 UTC+8
                utc_plus_8 = utc_now + timedelta(hours=8)
                formatted_time = utc_plus_8.strftime("%Y/%m/%d %H:%M")
                print(f"==================== {formatted_time} ====================")

                # 处理当前的前10名
                current_top_addresses = [item.get('address') for item in leaderboard5m_data[:10]]

                # 检查是否需要输出前10名到 Discord
                if time.time() - last_output_time >= output_interval:
                    # 创建一个嵌入消息
                    embed = {
                        "title": f"{output_interval // 60} minutes Burn",
                        "description": "",
                        "color": 0x00ff00  # 绿色
                    }

                    for index, address in enumerate(current_top_addresses):
                        if address in consecutive_counts:
                            consecutive_counts[address] += 1  # 连续上榜次数 +1
                        else:
                            consecutive_counts[address] = 1  # 初始化为1

                        nickname = existing_addresses.get(address, "未知")  # 获取名称，若不存在则为“未知名称”
                        
                        # 将每个地址的信息添加到嵌入的描述中
                        embed["description"] += f"#{str(index + 1).zfill(2)}： [{nickname}](https://etherscan.io/address/{address}) |  連續{consecutive_counts[address]}次\n"

                    # 发送到 Discord
                    discord_webhook.send_embed(embed['title'], embed['description'], embed['color'])
                    
                    last_output_time = time.time()  # 更新上次输出时间

                # 处理新地址和发送 Discord 通知
                for count, item in enumerate(leaderboard5m_data[:max_fetch_count], start=1):
                    address = item.get('address')
                    name = item.get('name')
                    if address:
                        if address not in existing_addresses:
                            nickname = name  # 使用原始名称（可能为 None）
                            if nickname is None or nickname == "None":
                                # 如果原始名称为 None，则通过 get_token_name 查询
                                nickname = get_token_name(address)  # 查询代币名称
                            
                            save_address(address, nickname)  # 保存新地址和名称到文件
                            # 打印地址和名称，包含名次
                            print(f"{GREEN}#{str(count).zfill(2)}: 合约地址: {address}, 名称: {nickname}{RESET}")  # 打印地址和名称
                            # 发送 Discord 嵌入式通知，标题包含名次
                            discord_webhook.send_embed(
                                f"New token Burn #{str(count).zfill(2)}", 
                                f"合约地址: {address}\n名称: [{nickname}]({f'https://etherscan.io/address/{address}'})"
                            )  # 发送嵌入式通知
                        else:
                            nickname = existing_addresses[address]
                            if nickname is None or nickname == "None":
                                print(f"#{str(count).zfill(2)}: 合约地址: {address}, 名称: {nickname}")
                        
                        count += 1
                        if count > max_fetch_count:
                            break

                request_success = True  # 请求成功
                break  # 退出代理尝试循环
            else:
                print(f"请求失败，状态码: {r2.status_code}")

        except Exception as e:
            print(f"使用代理 {proxy} 时发生错误: {e}")
            # 如果是最后一个代理，退出循环
            if attempt == len(proxies) - 1:
                print("所有代理均无法使用，退出程序。")
                break

    if not request_success:
        print("未能成功请求数据，等待重试...")
    
    # 每分钟查询一次
    time.sleep(60)


# 定义获取代币名称的函数
def get_token_info(contract_address):
    try:
        # 将地址转换为校验和格式
        checksum_address = Web3.to_checksum_address(contract_address)
        
        # 创建合约实例
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        
        # 调用 name() 函数
        token_name = contract.functions.name().call()
        return token_name
    except Exception as e:
        print(f"无法获取代币名称: {e}")
        return "未知"  # 返回一个默认值
