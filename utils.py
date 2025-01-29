import json
import sys
import folium
import os
import pandas as pd
from sqlalchemy import create_engine
import re
from datetime import datetime
import pprint

pp = pprint.PrettyPrinter(indent=4)

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

    # Disambiguate if public, concertat or privat from the xls file (the geojson has only either public, or others),
    # and drop privates
    filtered_features = []
    df = pd.read_excel('inventory.xls')
    for feature in filtered_geojson["features"]:
        nom_naturalesa = df[df["Codi del centre"] == int(feature["properties"]["codi_centre"])]["Nom naturalesa"]
        if len(nom_naturalesa) > 0:
            feature["properties"]["nom_naturalesa"] = nom_naturalesa.iloc[0]
        else:
            pp.pprint(f"Feature {feature} not found in the xls file")
        if feature["properties"]["nom_naturalesa"] != "Privat":
            filtered_features.append(feature)

    filtered_geojson["features"] = filtered_features

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

def csv_to_psql():
    # Database connection (adjust with your credentials)
    db_url = "postgresql://postgres_usr:postgres_pwd@0.0.0.0:5432/postgres_db"
    engine = create_engine(db_url)

    # Folder containing CSV files
    csv_folder = "assignations_data"

    # List of CSV files (e.g., 2024.csv, 2025.csv)
    csv_files = [f for f in os.listdir(csv_folder) if f.endswith('.csv')]

    # Function to parse a file using regex
    def parse_file_with_regex(file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Extract and clean the header
        header = re.split(r'\s{2,}|\t', lines[0].strip())

        # Parse the rest of the rows
        data = []
        for line in lines[1:]:
            # Split each row using multiple spaces or tabs
            row = re.split(r'\s{2,}|\t', line.strip())
            if len(row) == len(header):  # Ensure row matches the header length
                data.append(row)
            else:
                print(f"Error parsing row {row}")

        # Create a DataFrame
        df = pd.DataFrame(data, columns=header)
        return df

    # Iterate through each file and insert into the database
    for file in csv_files:
        # Extract year from the filename (e.g., 2025.csv -> 2025)
        year = int(re.search(r'\d{4}', file).group())
        year_datetime = datetime(year - 1, 9, 1)

        file_path = os.path.join(csv_folder, file)

        print(f"Processing file {file}")
        # Parse the file using regex
        df = parse_file_with_regex(file_path)

        # Add the 'year' column
        df['year'] = year_datetime

        # Insert into PostgreSQL
        df.to_sql('school_assignments', engine, if_exists='append', index=False)
        print(f"Inserted data from {file}")

    print("All files have been processed and inserted.")


if __name__ == "__main__":
    if sys.argv[1] == "filter_geojson":
        filter_geojson()
    elif sys.argv[1] == "show_areas":
        show_areas()
    elif sys.argv[1] == "csv_to_psql":
        csv_to_psql()