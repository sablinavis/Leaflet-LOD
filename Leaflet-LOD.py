"""
POC gebruik SPARQL API in LeafLet map


API van de query: [Aardbevingen in Groningen](https://linkeddata.cultureelerfgoed.nl/rce/-/queries/Query-17/4) gebruikt.

Download de html output als je het runt, en dubbelklik. 

Idee was om te kijken of zou lukken om API direct te gebruiken en wat er allemaal bij komt kijken en of LeafLet een goede oplossing is voor LOD.

Zoals je ziet moeten de geo WKT omgezet worden naar format dat LeafLet begrijpt. Daarnaast is het traag in rendering als de query te veel resultaten oplevert.
"""

from shapely import wkt
from shapely.geometry import Polygon, MultiPolygon, Point

import requests, json
url = "https://api.linkeddata.cultureelerfgoed.nl/queries/rce/Query-3-2-3/6/run?&page=1&pageSize=200"
response = requests.get(url)
data = response.json()
#data


def modify_list_with_wkt(data):
    # Define a function to convert WKT to lat/lng format
    def wkt_to_lat_lng(wkt_string):
        # Convert WKT string to a Shapely geometry object
        geometry = wkt.loads(wkt_string)
        #this is where I had the most difficulty with Leaflet:
        # If it's a MultiPolygon, convert the first polygon to a point
        if isinstance(geometry, MultiPolygon):
            first_polygon = geometry.geoms[0]
            point = first_polygon.representative_point()
        # If it's a Polygon, convert it to a point
        elif isinstance(geometry, Polygon):
            point = geometry.representative_point()
            # If it's a Point, extract latitude and longitude directly
        elif geometry.geom_type == 'Point':
            lat = geometry.y
            lng = geometry.x
            return {"lat": lat, "lng": lng}
        else:
            return None  # Unsupported geometry type

        # Extract latitude and longitude from the point (! this is the supported format)
        lat = point.y
        lng = point.x

        return {"lat": lat, "lng": lng}

    # Modify the list data to include lat/lng format
    modified_data = []
    for item in data:
        if "shape" in item:
            wkt_point = item["geo"]
            lat_lng = wkt_to_lat_lng(wkt_point)
            if lat_lng:
                item["lat"] = lat_lng["lat"]
                item["lng"] = lat_lng["lng"]
                del item["geo"]  # Remove the original WKT point
                modified_data.append(item)

    return modified_data


result = modify_list_with_wkt(data)
print(result)


# Convert result to JSON string
result_json = json.dumps(result)

# HTML content with result injected into JavaScript (this is just placing it on a website like template)
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Leaflet Map with JSON Data</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
    <style>
        #map {
            height: 1000px;
        }
    </style>
</head>
<body>

<div id="map"></div>

<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
<script>
    var map = L.map('map').setView([53.2191, 6.56667], 10);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
    }).addTo(map);

    // Sample JSON data with coordinates
    var jsonData = %s;

    // Add markers from JSON data
    jsonData.forEach(function (marker) {
        L.marker([marker.lat, marker.lng]).addTo(map)
            .bindPopup(marker.rmn);
    });
</script>

</body>
</html>
""" % result_json

# Write HTML content to a file
with open("leaflet_map.html", "w") as file:
    file.write(html_content)
