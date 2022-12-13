"""
Convert entries from Geonames to Carmen-compatible JSONlines files
Author: Alexandra DeLucia
"""
import pandas as pd
import logging


# Config logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

#######
# Load and format Geonames data
#######
geonames_data_dir = "Geonames"
geonames_countries_df = pd.read_csv(
    f"{geonames_data_dir}/countryInfo.txt",
    delimiter="\t",
    header=0,
    keep_default_na=False,
    na_values=['', 'NULL', 'n/a', 'nan', 'null']
)
geoname_country_lookup = geonames_countries_df[~geonames_countries_df.ISO.isna()].set_index("ISO")[["Country", "geonameid"]].to_dict(orient="index")
geonames_counties_df = pd.read_csv(
        f"{geonames_data_dir}/admin2Codes.txt",
        delimiter="\t",
        header=0,
        keep_default_na=False,
        na_values=['', 'NULL', 'n/a', 'nan', 'null']
    )
geonames_states_df = pd.read_csv(
        f"{geonames_data_dir}/admin1CodesASCII.txt",
        delimiter="\t",
        header=0,
        keep_default_na=False,
        na_values=['', 'NULL', 'n/a', 'nan', 'null']
    )
geonames_states_df[["country code", "admin1 code"]] = geonames_states_df.apply(
    lambda x: x["code"].split("."),
    axis="columns",
    result_type="expand")
geonames_state_lookup = geonames_states_df.set_index(["country code", "admin1 code"])[["name ascii", "geonameid"]].to_dict(orient="index")
geonames_counties_df[["country code", "admin1 code", "admin2 code"]] = geonames_counties_df.apply(
    lambda x: x["concatenated codes"].split("."),
    axis="columns",
    result_type="expand")
geonames_counties_lookup = geonames_counties_df.set_index(["concatenated codes"])[["asciiname", "geonameId"]].to_dict(orient="index")
geonames_cities_df = pd.read_csv(
    f"{geonames_data_dir}/cities15000.txt",
    delimiter="\t",
    header=0,
    keep_default_na=False,
    na_values=['', 'NULL', 'n/a', 'nan', 'null']
)
geonames_coordinates_lookup = pd.read_csv(
    f"{geonames_data_dir}/shapes_all_low.txt",
    delimiter="\t",
    header=0
)
geonames_coordinates_lookup["geoNameId"] = geonames_coordinates_lookup["geoNameId"].astype(str)
geonames_coordinates_lookup = geonames_coordinates_lookup.set_index("geoNameId")["geoJSON"].to_dict()


########
# Helper methods
########
def convert_geonames_to_carmen(geonames_entry):
    carmen_loc = {
        "id": "",
        "city": "",
        "county": "",
        "countycode": "",
        "state": "",
        "statecode": "",
        "country": "",
        "countrycode": "",
        "parent_id": "",
        "aliases": set(),
        "longitude": "",
        "latitude": "",
        "postal": "",
        "radius": None,
        "uzip": ""
    }
    aliases = geonames_entry.get("alternatenames", "")
    if not pd.isna(aliases):
        carmen_loc["aliases"] = set([i.strip() for i in aliases.split(",") if i.strip() != ""])
    if geonames_entry.get("name"):
        carmen_loc["aliases"].add(geonames_entry["name"])  # Add full name instead of ASCII name
    carmen_loc["id"] = str(geonames_entry.get("geonameid", geonames_entry.get("geonameId")))
    carmen_loc["countycode"] = geonames_entry.get("admin2 code") if not pd.isna(geonames_entry.get("admin2 code")) else ""
    carmen_loc["statecode"] = geonames_entry.get("admin1 code", "")
    carmen_loc["country"] = geonames_entry.get("Country")
    carmen_loc["countrycode"] = geonames_entry.get("country code", geonames_entry.get("ISO", ""))
    if carmen_loc["countrycode"] and not carmen_loc["country"]:
        country = geoname_country_lookup.get(carmen_loc["countrycode"])
        if country:
            carmen_loc["country"] = country["Country"]
    if carmen_loc["statecode"] and not carmen_loc["state"]:
        state = geonames_state_lookup.get((carmen_loc["countrycode"], carmen_loc["statecode"]))
        if state:
            carmen_loc["state"] = state["name ascii"]
    if carmen_loc["countycode"] and not carmen_loc["county"]:
        county_code = f"{carmen_loc['countrycode']}.{carmen_loc['statecode']}.{carmen_loc['countycode']}"
        county = geonames_counties_lookup.get(county_code)
        if county:
            carmen_loc["county"] = county["asciiname"]
    carmen_loc["longitude"] = str(geonames_entry.get("longitude", ""))
    carmen_loc["latitude"] = str(geonames_entry.get("latitude", ""))
    carmen_loc["dem"] = geonames_entry.get("dem", 0)  # Radius?

    geonames_name = geonames_entry.get("asciiname", geonames_entry.get("ascii name", geonames_entry.get("name ascii", "")))
    if "code" in geonames_entry:
        carmen_loc["state"] = geonames_name
    elif "concatenated codes" in geonames_entry:
        carmen_loc["county"] = geonames_name
    else:
        carmen_loc["city"] = geonames_name
    return carmen_loc


########
# Helper methods
########
if __name__ == "__main__":
    # Other settings
    outfile = "../data/geonames_locations_only.json"

    converted_entries = []
    # 1. Countries
    for i, row in geonames_countries_df.iterrows():
        new_entry = convert_geonames_to_carmen(row)
        converted_entries.append(new_entry)
    # 2. States / "admin1"
    for i, row in geonames_states_df.iterrows():
        new_entry = convert_geonames_to_carmen(row)
        new_entry["parent_id"] = geoname_country_lookup[new_entry["countrycode"]]["geonameid"]
        converted_entries.append(new_entry)
    # 3. Counties / "admin2"
    for i, row in geonames_counties_df.iterrows():
        new_entry = convert_geonames_to_carmen(row)
        # If state is listed, use state ID
        # Else map to country
        if new_entry["state"]:
            new_entry["parent_id"] = geonames_state_lookup[(new_entry["countrycode"], new_entry["statecode"])]["geonameid"]
        else:
            new_entry["parent_id"] = geoname_country_lookup[new_entry["countrycode"]]["geonameid"]
        converted_entries.append(new_entry)
    # 4. Cities
    for i, row in geonames_cities_df.iterrows():
        new_entry = convert_geonames_to_carmen(row)
        if new_entry["county"]:
            county_code = f"{new_entry['countrycode']}.{new_entry['statecode']}.{new_entry['countycode']}"
            new_entry["parent_id"] = geonames_counties_lookup[county_code]["geonameId"]
        elif new_entry["state"]:
            new_entry["parent_id"] = geonames_state_lookup[(new_entry["countrycode"], new_entry["statecode"])]["geonameid"]
        else:
            new_entry["parent_id"] = geoname_country_lookup[new_entry["countrycode"]]["geonameid"]
        converted_entries.append(new_entry)

    # Write out
    df = pd.DataFrame(converted_entries)
    df.drop_duplicates(subset=["id"], inplace=True)
    df["polygon"] = df.id.map(lambda x: geonames_coordinates_lookup.get(x, {}))
    df.to_json(outfile, orient="records", lines=True)
