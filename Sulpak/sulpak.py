import requests
from bs4 import BeautifulSoup
import json
import geojson
import re
import time

_urlCities = 'Home/GetCities'
_urlDomen = 'https://www.sulpak.kz/'

class City:
    def __init__(self, id, name):
        self.id = id
        self.name = name

class PointData:
    def __init__(self, city, url, lat, lng, address, phone, time):
        self.city = city
        self.url = url
        self.lat = lat
        self.lng = lng
        self.address = address
        self.phone = phone
        self.time = time


def GetIdCities(url):
    listCities = []
    res = requests.get(url)
    if res.status_code != 200:
        print("Bad request get cities")
        return False
    soup = BeautifulSoup(res.text, 'lxml')

    cities = soup.findAll('li')
    for city in cities:
        nameCity = city.text
        idCity = city.get('data-id')
        city = City(idCity, nameCity)
        listCities.append(city)
    return listCities

def GetPoints(city):
    url = f'{_urlDomen}Shops/{city.id}'
    res = requests.get(url)
    if res.status_code != 200:
        print("Bad request in get store")
        return False
    soup = BeautifulSoup(res.text, 'lxml')
    points = soup.findAll('div', class_='item-block')
    for point in points:
        divs = point.find('div', class_='description').findAll('div', class_=None)
        address = divs[0].text
        phone = divs[1].text
        time = divs[2].text
        link = point.find('a').get('data-link')
        match = re.search(r"ll=(.+)\&", str(link))
        coords = match.group(1).split("&")[0].split('%2C')
        lat = float(coords[0])
        lng = float(coords[1])
        pointData = PointData(city.name, url, lat, lng, address, phone, time)
        yield pointData

def ToGeojson(data):
    dataGeojson = []

    for gj in data:
        my_point = geojson.Point((gj.lat, gj.lng))
        myProperties = {'url': gj.url,
                        'city': gj.city,
                        'address': gj.address,
                        'phone': gj.phone,
                        'time': gj.time}
        feature = geojson.Feature(geometry=my_point, properties=myProperties)
        dataGeojson.append(feature)
    return geojson.FeatureCollection(dataGeojson)

if __name__ == '__main__':
    data = []

    cities = GetIdCities(f'{_urlDomen}{_urlCities}')
    for city in cities:
        for point in GetPoints(city):
            data.append(point)

    f = open('pickpoint.geojson', 'w', encoding ='utf-8').write(str(ToGeojson(data)))