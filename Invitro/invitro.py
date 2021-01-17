import requests
from bs4 import BeautifulSoup
import json
import geojson
import re
import time

_countries = {
    'ru': 'https://www.invitro.ru',
    'ua': 'https://www.invitro.ua',
    'by': 'https://invitro.by',
    'kz': 'https://invitro.kz',
    'kg': 'https://invitro.kg',
    'am': 'https://invitromed.am'
}

class PointData:
    def __init__(self, url, lat, lon, street, store, phone, metroName):
        self.url = url
        self.lat = lat
        self.lon = lon
        self.street = street
        self.store = store
        self.phone = phone
        self.metroName = metroName
        
def getPoints(url):
    res = requests.get(f'{url}')
    if res.status_code != 200:
        print("Bad request")
        return False

    data = []

    soup = BeautifulSoup(res.text, 'lxml')
    rowCities = soup.find('div', class_='row cities')
    cities = rowCities.findAll('div', class_='select-basket-city-cities')
    firstly = True
    for city in cities:
        if firstly:
            firstly = False
            continue

        columns = city.findAll('div', class_='select-basket-city-column mobile')
        if len(columns) == 0:
            print('No cities found')
        for column in columns:
            links = column.findAll('a')
            for link in links:
                codeCity = link.get('href').split('=')[1]
                nameCity = link.text
                res1 = requests.get(f'{url}/offices/{codeCity}')
                if (res1.status_code != 200):
                    print(f"Bad request in {nameCity} city")
                    break
                soup1 = BeautifulSoup(res1.text, 'lxml')
                offices = soup1.findAll('div', {'data-filter-show': 'true'})
                if len(offices) == 0:
                    offices = soup1.findAll('div', class_='iwg_wite_bg office-card')
                for office in offices:
                    hrefOffice = office.find('a')
                    nameOffice = hrefOffice.text
                    codeOffice = hrefOffice.get('href')
                    res2 = requests.get(f'{url}{codeOffice}')
                    if res.status_code != 200:
                        print(f"Bad request in {nameOffice} office")
                        break
                    soup2 = BeautifulSoup(res2.text, 'lxml')
                    scripts = soup2.findAll('script')

                    for script in scripts:
                        script_content = script.string
                        if script_content is not None and "var configMapOffice = " in script_content:
                            match = re.search(r"var configMapOffice = \{\"ITEMS\":\[(.+)\],", script_content)
                            jsonObject = json.loads(match.group(1))
                            splitStr = jsonObject['UF_COORD'].split(',')
                            lat = float(splitStr[0])
                            lon = float(splitStr[1])
                            pointData = PointData(f'{url}{codeOffice}', lat, lon, jsonObject['UF_ADDRESS'], jsonObject['UF_NAME'], 
                                                  jsonObject['UF_PHONE'], jsonObject['UF_METRO_NAME'])
                            data.append(pointData)

                    time.sleep(1)
                print(nameCity + ' finished')
    return ToGeojson(data)

def ToGeojson(data):
    dataGeojson = []

    for gj in data:
        my_point = geojson.Point((gj.lat, gj.lon))
        myProperties = {'url': gj.url,
                        'nameStore': gj.store,
                        'street': gj.street,
                        'phone': gj.phone,
                        'metroName': gj.metroName}
        feature = geojson.Feature(geometry=my_point, properties=myProperties)
        dataGeojson.append(feature)
    return geojson.FeatureCollection(dataGeojson)

if __name__ == '__main__':
    data = getPoints(_countries['ru'])
    f = open('pickpoint.geojson', 'w', encoding ='utf-8').write(str(data))