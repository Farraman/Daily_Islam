import requests
from pprint import pprint

url = "https://api.intelligence.io.solutions/api/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjVmZDNiMjZjLWQyNzAtNDVlYy1iMWYyLTcwZDFhZWVhNGM3OSIsImV4cCI6NDkwMDkzNjA0NX0.hzNBrIDZ38QmR8GgDf2DSIxojVe8wW6KX8T5pw_lXNNvVxdG5kDMMeac5wGxmg6MT9psvf-_wSav1l8Jnaq_LA",
}

data = {
    "model": "deepseek-ai/DeepSeek-R1",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant"
        },
        {
            "role": "user",
            "content": "how are you doing"
        }
    ],
}

response = requests.post(url, headers=headers, json=data)
data = response.json()
# pprint(data)

text = data['choices'][0]['message']['content']
print(text.split('</think>\n\n')[1])
