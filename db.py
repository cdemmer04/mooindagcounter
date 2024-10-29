import requests



# client_ip = request.headers.get('X-Forwarded-For')
# if client_ip:
#     client_ip = client_ip.split(',')[0]
# else:
#     client_ip = request.remote_addr

# Gebruik een externe API om de locatie op te halen
client_ip = "141.224.195.119"

try:
    response = requests.get(f'https://ipinfo.io/{client_ip}/json')
    location_data = response.json()
    
    city = location_data.get('city', 'Unknown')
    country = location_data.get('country', 'Unknown')
except requests.RequestException:
    city = country = 'Unknown'

f"{city}, {country}"
