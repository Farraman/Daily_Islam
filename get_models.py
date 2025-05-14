import requests
from pprint import pprint


url = "https://api.intelligence.io.solutions/api/v1/models"

headers = {
    "accept": "application/json",
    "Authorization": "Bearer io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6IjQzYzg3NGVlLWY1NGItNGU2Zi04NTM5LWEwZjllZmVkMmVhOSIsImV4cCI6NDkwMDQ5NDgwNX0.Ydko0GRPqtQJGSd2x6qH7BnmK9EKAQGoY9W_AxZUXzDjvtdw0JyfMbJw_OvU-IA3EAVkHH0lbDrQ4iocF3lQEg ",
}

response = requests.get(url, headers=headers)
data = response.json()
pprint(data)

for i in range(len(data['data'])):
    name = data['data'][i]['id']
    print(name)