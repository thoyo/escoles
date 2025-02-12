import json
import os
import psycopg2
from flask import Flask, request, jsonify, render_template
from geopy.distance import geodesic
from shapely.geometry import shape, Point
from dotenv import load_dotenv
import datetime

load_dotenv()

app = Flask(__name__)

# Load GeoJSON data once at startup
with open("filtered_data.geojson", "r") as f:
    geojson_data = json.load(f)

with open("barcelona_areas.geojson", "r") as f:
    areas_data = json.load(f)

if os.environ.get("AM_I_IN_A_DOCKER_CONTAINER", False):
    POSTGRES_HOST = "postgres"
else:
    POSTGRES_HOST = "localhost"

db_config = {
    "host": POSTGRES_HOST,
    "port": "5432",
    "database": "postgres_db",
    "user": "postgres_usr",
    "password": os.getenv("POSTGRES_PASSWORD")
}


def find_features(lat, lng, radius, option):
    clicked_point = (lat, lng)
    point_geom = Point(lng, lat)  # Shapely expects (x, y) => (lng, lat)
    nearby_features = []
    edu_features = []
    edu_features_top3 = []
    non_edu_features = []
    non_edu_features_top3 = []
    private_features = []
    area_features = []

    # Check which area the clicked point belongs to
    for area in areas_data["features"]:
        area_geom = shape(area["geometry"])  # Create a Shapely geometry
        if area_geom.contains(point_geom):  # Check if the point is inside the area
            detected_area = area
            print(f"Clicked point is inside area: {area['id']}")
            break
    else:
        print("Clicked point is not inside any area.")
        return {
            "type": "FeatureCollection",
            "features": [],
            "area": "Out of bounds"
        }

    # Tots els centres públics i concertats de la seva zona
    if option == "max_points":
        detected_area_geom = shape(detected_area["geometry"])
        for feature in geojson_data["features"]:
            feature_point = Point(feature["geometry"]["coordinates"])  # Shapely expects (lng, lat)
            if detected_area_geom.contains(feature_point):  # Feature is within the detected area
                area_features.append(feature)   # TODO: pre-compute and store in a DB
                print(
                    f"Feature {feature['properties']['denominaci_completa']} selected: inside detected area.")

    for feature in geojson_data["features"]:
        feature_coords = (feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
        distance = geodesic(clicked_point, feature_coords).meters
        if distance <= radius:
            feature["properties"]["distance_to_home"] = distance
            nearby_features.append(feature)
        naturalesa = feature["properties"].get("nom_naturalesa", "")
        if naturalesa == "Públic":
            edu_features.append((feature, distance))
        elif naturalesa == "Concertat":
            non_edu_features.append((feature, distance))
        elif naturalesa == "Privat":
            private_features.append((feature, distance))

    if option == "max_points":
        # Els 3 centres públics i 3 centres concertats més propers al domicili.
        edu_features_top3 = sorted(edu_features, key=lambda x: x[1])[:3]
        non_edu_features_top3 = sorted(non_edu_features, key=lambda x: x[1])[:3]

        # Extract features from sorted lists
        edu_features_top3 = [item[0] for item in edu_features_top3]
        non_edu_features_top3 = [item[0] for item in non_edu_features_top3]

    # Combine all unique features (no duplicates)
    all_features = {f["properties"]["codi_centre"]: f for f in
                    (nearby_features + edu_features_top3 + non_edu_features_top3 + private_features +
                     area_features)}    # TODO: remove duplicates?

    if option == "max_points":
        # I, si s'escau, altres centres de proximitat fins arribar a 6 centres públics i 6 centres concertats.
        publics = 0
        concertats = 0
        # Log unique features added
        for feature in all_features.values():
            if feature["properties"]["nom_naturalesa"] == "Públic":
                publics += 1
            elif naturalesa == "Concertat":
                concertats += 1
            feature_coords = (feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
            distance = geodesic(clicked_point, feature_coords).meters
            feature["properties"]["distance_to_home"] = distance  # Add distance to the properties

        if publics < 6:
            extra_publics = sorted(edu_features, key=lambda x: x[1])[publics:6]
            for feature, _ in extra_publics:
                feature_coords = (feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
                distance = geodesic(clicked_point, feature_coords).meters
                feature["properties"]["distance_to_home"] = distance  # Add distance to the properties
                all_features[feature["properties"]["codi_centre"]] = feature
        if concertats < 6:
            extra_concertats = sorted(non_edu_features, key=lambda x: x[1])[concertats:6]
            for feature, _ in extra_concertats:
                feature_coords = (feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
                distance = geodesic(clicked_point, feature_coords).meters
                feature["properties"]["distance_to_home"] = distance  # Add distance to the properties
                all_features[feature["properties"]["codi_centre"]] = feature

    # Connect to the database
    connection = psycopg2.connect(**db_config)
    cursor = connection.cursor()
    for feature in all_features.values():
        if feature["properties"].get("distance_to_home") is None:
            feature_coords = (feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
            distance = geodesic(clicked_point, feature_coords).meters
            feature["properties"]["distance_to_home"] = distance

        query = f"""
            SELECT 
                year AS time, 
                (places_ofertades - assignacions_en_primera - assignacions_altres) AS remaining_places
            FROM 
                school_assignments
            WHERE 
                codi_centre = '{feature['properties']['codi_centre'].lstrip("0")}'
            ORDER BY 
                time
        """

        try:
            # Execute the query
            cursor.execute(query)
            results = cursor.fetchall()
            # Convert the query results to a list of tuples with the year as a date string
            formatted_results = [
                (datetime.date(year=item[0].year, month=9, day=1).isoformat(), item[1])  # Set to September 1st
                for item in results
            ]
            all_features[feature['properties']['codi_centre']]['properties']['remaining_places'] = formatted_results
        except Exception as e:
            print(f"Error for feature {feature}, {e}")
            all_features[feature['properties']['codi_centre']]['properties']['remaining_places'] = []

        query = f"""
           SELECT
               places_ofertades 
           FROM
               school_assignments
            WHERE 
                codi_centre = '{feature['properties']['codi_centre'].lstrip("0")}'
           ORDER BY 
               year desc
        """

        try:
            # Execute the query
            cursor.execute(query)
            results = cursor.fetchall()
            all_features[feature['properties']['codi_centre']]['properties']['total_places'] = results[0]
        except Exception as e:
            print(f"Error for feature {feature}, {e}")
            all_features[feature['properties']['codi_centre']]['properties']['total_places'] = -1

    if cursor:
        cursor.close()
    if connection:
        connection.close()

    return {
        "type": "FeatureCollection",
        "features": list(all_features.values()),
        "area": detected_area
    }


# API endpoint to fetch nearby features
@app.route("/projects/escoles/nearby", methods=["GET"])
def get_nearby_features():
    # Extract latitude, longitude, and radius from query parameters
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    radius = float(request.args.get("radius", 500))  # Default radius is 500m
    option = request.args.get("option")  # TODO: apply logic based on option

    # Find nearby features
    filtered_geojson = find_features(lat, lng, radius, option)
    return jsonify(filtered_geojson)


# Serve the frontend (index.html)
@app.route("/projects/escoles", strict_slashes=False)
def serve_frontend():
    return render_template('index.html')


# Catch-all route for all other paths
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return '<h1>Site Under Construction</h1>', 200


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
