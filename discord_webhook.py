import requests
from config import DISCORD_WEBHOOK_URLS

class DiscordWebhook:
    def __init__(self, webhook_urls):
        self.webhook_urls = webhook_urls  # 接收多个 Webhook URL

    def send_message(self, message):
        data = {
            "content": message
        }
        for url in self.webhook_urls:
            response = requests.post(url, json=data)
            if response.status_code != 204:
                print(f"Failed to send message to {url}: {response.status_code}, {response.text}")

    def send_embed(self, title, description, color=0x00ff00):
        embed = {
            "embeds": [
                {
                    "title": title,
                    "description": description,
                    "color": color
                }
            ]
        }
        for url in self.webhook_urls:
            response = requests.post(url, json=embed)
            if response.status_code != 204:
                print(f"Failed to send embed to {url}: {response.status_code}, {response.text}")

# 设置 Webhook URL
def create_webhook():
    return DISCORD_WEBHOOK_URLS  # 使用配置文件中的 Webhook URLs

# 示例用法
if __name__ == "__main__":
    webhook_urls = create_webhook()  # 获取 Webhook URLs
    discord_webhook = DiscordWebhook(webhook_urls)

    # 发送测试嵌入消息
    discord_webhook.send_embed("Gas燃燒排行-#1", "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045\n名稱：[vitalik.eth](https://etherscan.io/address/0xd8da6bf26964af9d7eed9e03e53415d37aa96045)")
