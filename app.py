import json
from flask import Flask, request, jsonify, send_from_directory
from geopy.distance import geodesic
from shapely.geometry import shape, Point

app = Flask(__name__)

# Load GeoJSON data once at startup
with open("filtered_data.geojson", "r") as f:
    geojson_data = json.load(f)

with open("areas.geojson", "r") as f:
    areas_data = json.load(f)

# Helper function to calculate distance and find nearby features
def find_features(lat, lng, radius=500):
    clicked_point = (lat, lng)
    point_geom = Point(lng, lat)  # Shapely expects (x, y) => (lng, lat)
    nearby_features = []
    edu_features = []
    non_edu_features = []
    area_features = []
    log_details = []
    detected_area = None
        
    # Tots els centres públics i concertats de la seva zona
    # Check which area the clicked point belongs to
    for area in areas_data["features"]:
        area_geom = shape(area["geometry"])  # Create a Shapely geometry
        if area_geom.contains(point_geom):  # Check if the point is inside the area
            detected_area = area
            log_details.append(f"Clicked point is inside area: {area['id']}")
            break
    # If a detected area exists, include all its features
    if detected_area:
        detected_area_geom = shape(detected_area["geometry"])
        for feature in geojson_data["features"]:
            feature_point = Point(feature["geometry"]["coordinates"])  # Shapely expects (lng, lat)
            if detected_area_geom.contains(feature_point):  # Feature is within the detected area
                area_features.append(feature)
                log_details.append(f"Feature {feature['properties']['denominaci_completa']} selected: inside detected area.")

    # Els centres situats a menys de 500 metres, encara que no siguin de la mateixa zona.
    for feature in geojson_data["features"]:
        feature_coords = (feature["geometry"]["coordinates"][1], feature["geometry"]["coordinates"][0])
        distance = geodesic(clicked_point, feature_coords).meters
        if distance <= radius:
            nearby_features.append(feature)
            log_details.append(f"Feature {feature['properties']['denominaci_completa']} selected: within 500m radius (distance: {distance:.2f}m).")
        titularitat = feature["properties"].get("nom_titularitat", "")
        if titularitat == "Departament d'Educació":
            edu_features.append((feature, distance))
        else:
            non_edu_features.append((feature, distance))
    
    # Els 3 centres públics i 3 centres concertats més propers al domicili.
    # Sort by distance for nearest search
    edu_features_top3 = sorted(edu_features, key=lambda x: x[1])[:3]  # 3 nearest where titularitat = "Departament d'Educació"
    non_edu_features_top3 = sorted(non_edu_features, key=lambda x: x[1])[:3]  # 3 nearest where titularitat != "Departament d'Educació"

    # Log reasons for the nearest features
    for feature, distance in edu_features_top3:
        log_details.append(f"Feature {feature['properties']['denominaci_completa']} selected: one of 3 nearest 'Departament d'Educació' (distance: {distance:.2f}m).")

    for feature, distance in non_edu_features_top3:
        log_details.append(f"Feature {feature['properties']['denominaci_completa']} selected: one of 3 nearest non-'Departament d'Educació' (distance: {distance:.2f}m).")

    # Extract features from sorted lists
    edu_features_top3 = [item[0] for item in edu_features_top3]
    non_edu_features_top3 = [item[0] for item in non_edu_features_top3]

    # Combine all unique features (no duplicates)
    all_features = {f["properties"]["codi_centre"]: f for f in
                    (nearby_features + edu_features_top3 + non_edu_features_top3 + area_features)}

    # I, si s'escau, altres centres de proximitat fins arribar a 6 centres públics i 6 centres concertats.
    publics = 0
    concertats = 0
    # Log unique features added
    for feature in all_features.values():
        if feature["properties"]["nom_titularitat"] == "Departament d'Educació":
            publics += 1
        else:
            concertats += 1

    if publics < 6:
        extra_publics = sorted(edu_features, key=lambda x: x[1])[publics:6]
        for feature, _ in extra_publics:
            all_features[feature["properties"]["codi_centre"]] = feature
    if concertats < 6:
        extra_concertats = sorted(non_edu_features, key=lambda x: x[1])[concertats:6]
        for feature, _ in extra_concertats:
            all_features[feature["properties"]["codi_centre"]] = feature

    for feature in all_features.values():
        log_details.append(f"Feature {feature['properties']['denominaci_completa']} is part of the final result set.")

    # Print logs to the terminal
    for log in log_details:
        print(log)

    return {
        "type": "FeatureCollection",
        "features": list(all_features.values()),
        "area": detected_area
    }

# API endpoint to fetch nearby features
@app.route("/nearby", methods=["GET"])
def get_nearby_features():
    # Extract latitude, longitude, and radius from query parameters
    lat = float(request.args.get("lat"))
    lng = float(request.args.get("lng"))
    radius = float(request.args.get("radius", 500))  # Default radius is 500m

    # Find nearby features
    filtered_geojson = find_features(lat, lng, radius)
    return jsonify(filtered_geojson)

# Serve the frontend (index.html)
@app.route("/")
def serve_frontend():
    return send_from_directory('.', 'index.html')

# Serve any static files (like CSS or JS) from the same directory
@app.route("/<path:filename>")
def serve_static_files(filename):
    return send_from_directory('.', filename)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
