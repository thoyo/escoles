import json
import folium
import pyproj
from shapely.geometry import shape, mapping
from shapely.ops import transform


def filter_geojson():
    with open("data.geojson", "r") as f:
        geojson_data = json.load(f)

    # Filter features where "Nom municipi" equals "Barcelona"
    filtered_features = [
        feature for feature in geojson_data["features"]
        if feature["properties"].get("nom_municipi") == "Barcelona" and "EINF2C EPRI" in feature["properties"].get("estudis")
    ]

    # Create a new GeoJSON object with the filtered features
    filtered_geojson = {
        "type": "FeatureCollection",
        "features": filtered_features,
    }

    # Save the filtered GeoJSON to the output file
    with open("filtered_data.geojson", "w") as f:
        json.dump(filtered_geojson, f)


def show_areas():
    with open("areas.geojson", "r") as f:
        geojson_data = json.load(f)

    m = folium.Map(location=[41.7, 2.4], zoom_start=10)
    folium.GeoJson(geojson_data, name="GeoJSON Data").add_to(m)

    # Save and display map
    m.save("map.html")