import requests
from pprint import pprint

url = "https://api.intelligence.io.solutions/api/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjQzYzg3NGVlLWY1NGItNGU2Zi04NTM5LWEwZjllZmVkMmVhOSIsImV4cCI6NDkwMDQ5NDgwNX0.Ydko0GRPqtQJGSd2x6qH7BnmK9EKAQGoY9W_AxZUXzDjvtdw0JyfMbJw_OvU-IA3EAVkHH0lbDrQ4iocF3lQEg ",
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