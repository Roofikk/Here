import requests
from bs4 import BeautifulSoup
import geojson
import re
import asyncio
import aiohttp

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

async def GetStore(url):
    data = []
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as res:
            if res.status == 200:
                print(f"Request status is 200 in {url}")
            text = await res.read()

        #import pdb; pdb.set_trace()
        soup1 = BeautifulSoup(text.decode('utf-8'), 'lxml')
        div = soup1.find('div', class_="wrapper")
        pShops = div.find_all('p')

        if len(pShops) == 0:
            print(f"Shops not found in {url} city")
            return await False

        for store in pShops:
            check = store.find('a')
            if check:
                urlStore = check.get('href')
                
                response2 = requests.get(f'{url}{urlStore}')
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
                        storeLoad = Store(street, store.text, url + urlStore, phone, workTime, float(coords[0]), float(coords[1]))
                        data.append(storeLoad)
                        break
        print(url + ' - Successful')
        return await data

def main(url):
    data = []

    response = requests.get(f'{url}')
    if response.status_code != 200:
        print("Bad request")
        return False

    soup = BeautifulSoup(response.text, 'lxml')
    divs = soup.find_all('div', class_="col-sm-4 col-xs-6")

    if len(divs) == 0:
        print("Error")
        return False

    for div in divs:
        aHrefCity = div.find_all('a')
        if len(aHrefCity) == 0:
            print("City links not found")
            break 

        tasks = []

        for aCity in aHrefCity:
            s = aCity.get('href')
            urlCity = s.replace('/store', '')
            city = aCity.text
            loop = asyncio.get_event_loop()
            tasks.append(loop.create_task(GetStore(f'{url}{urlCity}')))
            
        wait_task = asyncio.wait(tasks)
        results = loop.run_until_complete(wait_task)
        #loop.close()
    geojsonData = getGeojson(data)
    return geojsonData

def getGeojson(data):

    geoList = []
    for pt in data:
        my_point = geojson.Point((pt.lon, pt.lat))
        myProperties = {'street': pt.street,
                        'store': pt.store,
                        'url': pt.url,
                        'phone': pt.phone,
                        'workTime': pt.workTime}
        feature = geojson.Feature(geometry=my_point, properties = myProperties)
        geoList.append(feature)
    return geojson.FeatureCollection(geoList)

if __name__ == '__main__':
    data = main(url)
    f = open('pickpoint.geojson', 'w', encoding ='utf-8').write(str(data))