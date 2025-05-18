import requests
from pprint import pprint


url = "https://api.intelligence.io.solutions/api/v1/chat/completions" 

headers = {
    "accept": "application/json",
    "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjVmZDNiMjZjLWQyNzAtNDVlYy1iMWYyLTcwZDFhZWVhNGM3OSIsImV4cCI6NDkwMDkzNjA0NX0.hzNBrIDZ38QmR8GgDf2DSIxojVe8wW6KX8T5pw_lXNNvVxdG5kDMMeac5wGxmg6MT9psvf-_wSav1l8Jnaq_LA",
}

response = requests.get(url, headers=headers)
data = response.json()
pprint(data)

for i in range(len(data['data'])):
    name = data['data'][i]['id']
    print(name)
