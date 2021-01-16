import requests
from bs4 import BeautifulSoup
import geojson
import re

url = "https://beeline-tochki.ru/store"

class Store:
    def __init__(self, street, store, url, phone, workTime, lon, lat):
        self.street = street
        self.store = store
        self.url = url
        self.phone = phone
        self.workTime = workTime
        self.lat = lat
        self.lon = lon

def getStore(url):
    data = []

    response = requests.get(f'{url}')

    soup = BeautifulSoup(response.text, 'lxml')

    divs = soup.find_all('div', class_="col-sm-4 col-xs-6")
    for div in divs:
        aHrefCity = div.find_all('a')
        for aCity in aHrefCity:
            s = aCity.get('href')
            urlCity = s.replace('/store', '')
            city = aCity.text
            response1 = requests.get(f'{url}{urlCity}')
            soup1 = BeautifulSoup(response1.text, 'lxml')
            div = soup1.find('div', class_="wrapper")
            pShops = div.find_all('p')
            for store in pShops:
                check = store.find('a')
                if check:
                    s = check.get('href')
                    urlStore = s.replace('/store' + urlCity, '')
                    
                    response2 = requests.get(f'{url}{urlCity}{urlStore}')
                    soup2 = BeautifulSoup(response2.text, 'lxml')

                    street = soup2.find('span', itemprop='streetAddress')
                    if street:
                        street = street.text

                    phone = soup2.find('span', itemprop='telephone')
                    if phone:
                        phone = phone.text.split(';')

                    table = soup2.find('table', class_='gray_table')
                    if table:
                        tr = table.findAll('tr')
                        workTime = []
                        for line in tr:
                            day = line.find('th').text
                            time = line.find('td').text
                            workTime.append({"day": day, 
                                             "time": time})

                    scripts = soup2.find_all('script')
                    for script in scripts:
                        script_content = script.string
                        if script_content is not None and "var map" in script_content:
                            match = re.search(r"center: \[(.+)\],", str(script_content))
                            match = re.search(r"\[(.+)\]", str(match.group(0)))
                            coords = match.group(1).split(', ')
                            storeLoad = Store(street, store.text, url + urlCity + urlStore, phone, workTime, float(coords[0]), float(coords[1]))
                            data.append(storeLoad)
                            break
            print (city + ' - completed')
    
    geojsonData = getGeojson(data)
    return geojsonData

def getGeojson(data):

    geoList = []
    for pt in data:
        my_point = geojson.Point((pt.lat, pt.lon))
        myProperties = {'street': pt.street,
                        'store': pt.store,
                        'url': pt.url,
                        'phone': pt.phone,
                        'workTime': pt.workTime}
        feature = geojson.Feature(geometry=my_point, properties = myProperties)
        geoList.append(feature)
    return geojson.FeatureCollection(geoList)

data = getStore(url)
f = open('pickpoint.geojson', 'w', encoding ='utf-8').write(str(data))