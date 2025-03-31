# 官方 API 调用示例（需配置 API 密钥）
import requests
from urllib.parse import quote

API_KEY = "AIzaSyATBXajvzQLTDHEQbcpq0Ihe0vWDHmO520"
text = "需要翻译的文本"
target_lang = "en"

url = f"https://translation.googleapis.com/language/translate/v2?key={API_KEY}&q={quote(text)}&target={target_lang}"
response = requests.get(url)
translated_text = response.json()["data"]["translations"][0]["translatedText"]
print(translated_text)