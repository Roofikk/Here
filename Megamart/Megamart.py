import requests
import geojson
import re

url = "https://www.megamart.ru/ajax/getmap.php?x1=55.82504531742157&y1=59.30033735937501&x2=57.63633293833316&y2=66.441450640625&section=300"

def getPoints(url):

    res = requests.get(f'{url}', verify=False)

    if res.status_code == 200: 
        return toGeojson(res.json())

def toGeojson(data):
    
    geoList = []
    for gj in data:
        my_point = geojson.Point((float(gj['lat']), float(gj['lon'])))
        myProperties = {'name': gj['name'],
                        'street': gj['address'],
                        'work_time': gj['work_time']}
        feature = geojson.Feature(geometry=my_point, properties=myProperties)
        geoList.append(feature)
    return geojson.FeatureCollection(geoList)

if __name__ == "__main__":
    data = getPoints(url)
    f = open('pickpoint.geojson', 'w', encoding ='utf-8').write(str(data))