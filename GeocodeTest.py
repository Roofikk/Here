import requests
from bs4 import BeautifulSoup
import json
import geojson
import re
import time

_apiKey = "SNgeI1tCT-oihjeZDGi6WqcM0a9QAttLhKTecPaaETQ"

def Geocode(address, apiKey):
    URL = 'https://geocode.search.hereapi.com/v1/geocode'

    # Параметры запроса
    params = {
        'q': address,
        'apiKey': apiKey
    }
    
    import pdb; pdb.set_trace()
    # Парсинг ответа в JSON формате
    response = requests.get(URL, params=params).json()
    item = response['items'][0]

    address = item['address']
    position = item['position']

    result = {
        'address': address['label'],
        'lat': position['lat'],
        'lng': position['lng'],
    }
    
    return result

if __name__ == "__main__":
    address = "Украина, Александрия, Соборный проспект 98"
    res = Geocode(address, _apiKey)