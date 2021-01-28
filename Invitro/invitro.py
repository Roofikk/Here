import requests
from bs4 import BeautifulSoup
import json
import geojson
import re
import time

_countries = {
    'ru': ['https://www.invitro.ru', 'Россия'],
    'ua': ['https://www.invitro.ua', 'Украина'],
    'by': ['https://invitro.by', 'Белорусь'],
    'kz': ['https://invitro.kz', 'Казахстан'],
    'kg': ['https://invitro.kg', 'Кыргызстан'],
    'am': ['https://invitromed.am', 'Армения']
}

_template = {
    ', д.': '',
    'пр-т': 'проспект',
    'пр-кт': 'проспект',
    'пл.': 'площадь',
    'ул.': 'улица',
    'г. ': '',
    'пер.': 'перекрёсток',
    'обл.': 'область',
    'пр.': 'проспект'
}

_apiKey = "Civl-afRyVsSHQr6fBFZ448sbrVqCuN6EgouNgax9BI"

class PointData:
    def __init__(self, country, city, url, lon, lat, address, store, phone, metroName, coordinatesType):
        self.country = country
        self.city = city
        self.url = url
        self.original_lat = lat
        self.original_lon = lon
        self.address = address
        self.store = store
        self.phone = phone
        self.metroName = metroName
        self.coordinatesType = coordinatesType

def getPointsInOtherCountries(country):
    res = requests.get(f'{country[0]}/offices')
    if res.status_code != 200:
        print("Bad request")
        return False
    
    data = []

    soup = BeautifulSoup(res.text, 'lxml')
    listCities = soup.findAll('a', class_='change-city-block__item')
    for city in listCities:
        linkCity = city.get('href')
        cityName = city.text

        res1 = requests.get(f'{country[0]}{linkCity}')
        if res1.status_code != 200:
            print('No city found')
            break
        soup1 = BeautifulSoup(res1.text, 'lxml')
        container = soup1.find('div', class_='article article--mb0 article--p0 article--full')
        if container:
            yield GetData(soup1, country[0] + linkCity, cityName, country)
        else:
            addresses = soup1.findAll('div', class_='offices-list__item')
            for address in addresses:
                tagHref = address.find('a', class_='map-panel__result-name')
                linkPoint = tagHref.get('href')
                namePoint = tagHref.text
                res2 = requests.get(f'{country[0]}{linkPoint}')
                if res2.status_code != 200:
                    print("Point not found")
                    break
                soup2 = BeautifulSoup(res2.text, 'lxml')
                yield GetData(soup2, country[0] + linkPoint, cityName, country)

def GetData(soup, link, cityName, country):
    pointData = None
    if soup.find('div', class_='map-block show-block'):
        scripts = soup.findAll('script')
        for script in scripts:
            script_content = script.string
            if script_content is not None and "var configMapOffice = " in script_content:
                match = re.search(r"var configMapOffice = \{\"ITEMS\":\[(.+)\],", script_content)
                jsonObject = json.loads(match.group(1))
                if jsonObject['UF_COORD'] is not None:
                    splitStr = str(jsonObject['UF_COORD']).split(',')
                    lat = float(splitStr[0])
                    lon = float(splitStr[1])
                else:
                    lat = 0
                    lon = 0
                pointData = PointData(country[1], cityName, f'{link}', lat, lon, jsonObject['UF_ADDRESS'], 
                                      jsonObject['UF_NAME'], jsonObject['UF_PHONE'], jsonObject['UF_METRO_NAME'], 'From site')
                break

    if pointData is None:
        container = soup.find('p', class_='main')
        if container.find('span', class_='office-pnones'):
            phone = []
            phoneData = container.find('span', class_='office-pnones').findAll('em')
            for ph in phoneData:
                phone.append(ph.text.replace(',', ''))
            address = container.getText().lstrip().rstrip().split('\n\t\t\t\t')[0]
        else: 
            addressWithPhone = container.text.rstrip().lstrip().split(';')
            address = addressWithPhone[0]
            phone = addressWithPhone[1].split(',') if len(addressWithPhone) != 1 else False
        pointData = PointData(country[1], cityName, f'{link}', 0, 0, address, address, phone, '', 'From site')
    
    return pointData

def getPoints(country):
    res = requests.get(f'{country[0]}')
    if res.status_code != 200:
        print("Bad request")
        return False

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
                res1 = requests.get(f'{country[0]}/offices/{codeCity}')
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
                    res2 = requests.get(f'{country[0]}{codeOffice}')
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
                            pointData = PointData(country[1], nameCity, f'{country[0]}{codeOffice}', lat, lon, jsonObject['UF_ADDRESS'], 
                                                  jsonObject['UF_NAME'], jsonObject['UF_PHONE'], jsonObject['UF_METRO_NAME'], 'From site')
                            yield pointData
                            break

                    time.sleep(1)

def Geocode(address, apiKey):
    URL = 'https://geocode.search.hereapi.com/v1/geocode'

    # Параметры запроса
    params = {
        'q': address,
        'apiKey': apiKey
    }
    
    # Парсинг ответа в JSON формате
    response = requests.get(URL, params=params)
    if response.status_code != 200:
        print('Bad request in HERE API')
        return False
    response = response.json()
    if len(response) == 0:
        print(address)
        return False
    if len(response['items']) == 0:
        print(address)
        return False
    item = response['items'][0]

    address = item['address']
    position = item['position']

    result = {
        'address': address['label'],
        'lat': position['lat'],
        'lng': position['lng'],
    }
    
    return result

def ToGeojson(data):
    dataGeojson = []

    for gj in data:
        my_point = geojson.Point((gj.original_lon, gj.original_lat))
        myProperties = {'url': gj.url,
                        'country': gj.country,
                        'city': gj.city,
                        'nameStore': gj.store,
                        'address': gj.address,
                        'phone': gj.phone,
                        'metroName': gj.metroName}
        feature = geojson.Feature(geometry=my_point, properties=myProperties)
        dataGeojson.append(feature)
    return geojson.FeatureCollection(dataGeojson)

def main(country):
    data = []
    if country == 'ru':
        for dx in getPoints(_countries[country]):
            data.append(dx)
    else:
        for dx in getPointsInOtherCountries(_countries[country]):
            data.append(dx)

    for dt in data:
        if dt.original_lon == 0 and dt.original_lat == 0:
            address = dt.address
            address = dt.country + ", " + address
            for tp in _template:
                address = address.replace(tp, _template[tp])
            res = Geocode(address, _apiKey)
            if res:
                dt.original_lat = res['lat']
                dt.original_lon = res['lng']
                dt.coordinatesType = "From HERE API"

    f = open('pickpoint.geojson', 'w', encoding ='utf-8').write(str(ToGeojson(data)))

if __name__ == '__main__':
    main('ru')