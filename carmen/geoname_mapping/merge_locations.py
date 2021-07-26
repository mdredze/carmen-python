"""
Map and combine entries from Carmen and Geonames. Assumes Geonames entries have already been converted
to Carmen format with `convert_geonames_to_carmen.py` and is saved in `carmen/data/geonames_locations_only.json`.

Output is `carmen/data/combined_locations.json`

Author: Alexandra DeLucia
"""
import pandas as pd
import logging
from tqdm import tqdm
from geopy import distance
from iso3166 import countries
import pickle
import os
import re
from difflib import SequenceMatcher

# Config logging for debugging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


# Load and format Carmen locations
carmen_filename = "../data/locations.json"
logging.info(f"Reading locations from {carmen_filename}")
carmen_locations_df = pd.read_json(carmen_filename, lines=True).sort_values(by=["countrycode", "state", "county", "city"])
carmen_locations_df.fillna("", inplace=True)
carmen_locations_df["coordinates"] = carmen_locations_df.apply(
    lambda x: (x.latitude, x.longitude) if not pd.isna(x.latitude) else None,
    axis="columns")

# Load and format Geonames data
geonames_filename = "../data/geonames_locations_only.json"
geonames_locations_df = pd.read_json(geonames_filename, lines=True).sort_values(by=["countrycode", "state", "county", "city"])
geonames_locations_df.fillna("", inplace=True)
geonames_locations_df["coordinates"] = geonames_locations_df.apply(
    lambda x: (x.latitude, x.longitude) if not pd.isna(x.latitude) else None,
    axis="columns")

# Create master country name to code lookup
country_name_to_code = carmen_locations_df[~carmen_locations_df.countrycode.isna()].set_index("country")["countrycode"].to_dict()
geoname_country_to_code = geonames_locations_df[~geonames_locations_df.countrycode.isna()].set_index("country")["countrycode"].to_dict()
country_name_to_code.update(geoname_country_to_code)
def map_country_name_to_code(name):
    # Check Carmen+Geonames entries
    if country_name_to_code.get(name):
        return country_name_to_code.get(name)
    # Check ISO3166 package
    try:
        countries.get(name)
    except KeyError as err:
        return ""
    return countries.get(name).alpha2
# Create master statecode lookup with a state, country code pair
state_name_to_code = carmen_locations_df[carmen_locations_df.statecode!=""].set_index(["state", "countrycode"])["statecode"].to_dict()
geoname_state_to_code = geonames_locations_df[~geonames_locations_df["statecode"].isna()].set_index(["state", "countrycode"])["statecode"].to_dict()
for state, code in geoname_state_to_code.items():
    if state not in state_name_to_code:
        state_name_to_code[state] = code


# Other settings
DISTANCE_THRESHOLD = 5.0  # Miles
NAME_THRESHOLD = 0.9
mapping_file = "mapped_locations_dict.pkl"
outfile = "../data/all_locations.json"


def coordinate_distance(coord1, coord2):
    """Distance between coordinates in miles"""
    return distance.distance(coord1, coord2).miles


def name_similarity(a, b):
    """
    Graciously from StackOverflow
    https://stackoverflow.com/questions/17388213/find-the-similarity-metric-between-two-strings
    """
    a = re.sub("county|provincia de", "", a.lower()).strip()
    b = re.sub("county|provincia de", "", b.lower()).strip()
    return SequenceMatcher(None, a, b).ratio()


cities_only = geonames_locations_df[(geonames_locations_df.city!="")]
def map_city(carmen_obj):
    match = cities_only[
        cities_only.apply(
            lambda x: _city_match(x, carmen_obj),
            axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        logging.info(f"{len(match)} hits for {carmen_obj.city},{carmen_obj.county},{carmen_obj.state},{carmen_obj.countrycode} ({carmen_obj.id}).")
        return
    else:
        return


counties_only = geonames_locations_df[(geonames_locations_df.city=="")&(geonames_locations_df.county!="")]
def map_county(carmen_obj):
    match = counties_only[
        counties_only.apply(lambda x: _county_match(x, carmen_obj), axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        # Check for exact name match
        match = counties_only[
            counties_only.apply(
                lambda x: _county_match(x, carmen_obj, exact_match=True),
                axis="columns")
        ]
        if len(match) == 1:
            return match.iloc[0]
        logging.warning(f"{len(match)} hits for {carmen_obj.county},{carmen_obj.state},{carmen_obj.countrycode} ({carmen_obj.id}) after exact search")
        logging.warning(f"{match[['id','county','state','coordinates']]}")
        exit(1)
        return
    else:
        return


states_only = geonames_locations_df[(geonames_locations_df.state!="")&(geonames_locations_df.county=="")&(geonames_locations_df.city=="")]
def map_state(carmen_obj):
    match = states_only[
        states_only.apply(
            lambda x: _state_match(x, carmen_obj),
            axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        match = match[
            match.apply(
                lambda x: _state_match(x, carmen_obj, exact_match=True),
                axis="columns")
        ]
        if len(match) == 1:
            return match.iloc[0]
        else:
            logging.info(f"{len(match)} hits for {carmen_obj.state},{carmen_obj.countrycode} ({carmen_obj.id}) after strict search")
            return
    else:
        return


countries_only = geonames_locations_df[(geonames_locations_df.city=="")&(geonames_locations_df.state=="")&(geonames_locations_df.county=="")]
def map_country(carmen_obj):
    match = countries_only[
        countries_only.apply(
            lambda x: x.countrycode==carmen_obj.countrycode or x.country==carmen_obj.country,
            axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        logging.info(f"{len(match)} hits for {carmen_obj.country}, ({carmen_obj.countrycode}) ({carmen_obj.id})")
    else:
        return


def _state_match(x, carmen_obj, exact_match=False):
    if x.countrycode != carmen_obj.countrycode:
        return False
    name_sim = name_similarity(x.state, carmen_obj.state)
    # Check for best match or exact match
    if exact_match:
        thresh = 1.0
    else:
        thresh = NAME_THRESHOLD
    if name_sim >= thresh or x.statecode == carmen_obj.statecode:
        return True
    return False


def _city_match(x, carmen_obj):
    if x.countrycode != carmen_obj.countrycode:
        return False
    if carmen_obj.statecode and (x.statecode != carmen_obj.statecode):
        return False
    dist = coordinate_distance(x.coordinates, carmen_obj.coordinates)
    name_sim = name_similarity(x.city, carmen_obj.city)
    if (name_sim >= NAME_THRESHOLD) and dist < DISTANCE_THRESHOLD:
        return True
    return False


def _county_match(x, carmen_obj, exact_match=False):
    # Check country and state
    if carmen_obj.countrycode and (x.countrycode != carmen_obj.countrycode):
        return False
    # Carmen statcode is not always filled in
    if carmen_obj.statecode and (x.statecode != carmen_obj.statecode):
        return False
    if carmen_obj.state and (x.state != carmen_obj.state):
        return False
    # Check for best match or exact match
    if exact_match:
        thresh = 1.0
    else:
        thresh = NAME_THRESHOLD
    if name_similarity(x.county, carmen_obj.county) >= thresh:
        return True
    return False


if __name__ == "__main__":
    # Fill in missing Carmen country codes
    carmen_locations_df["countrycode"] = carmen_locations_df.apply(
        lambda x: x.countrycode if x.countrycode != "" else map_country_name_to_code(x.country),
        axis="columns"
    )

    # Load previously mapped locations and drop ones that have already been done
    if os.path.exists(mapping_file):
        with open(mapping_file, "rb") as f:
            mapped_locations = pickle.load(f)
    else:
        mapped_locations = {}
    total_num_locations = len(carmen_locations_df)
    unmapped_carmen_locations_df = carmen_locations_df.drop(
        carmen_locations_df[carmen_locations_df.id.isin(mapped_locations.keys())].index,
    )
    unmapped_carmen_locations_df.reset_index(drop=True)

    # Map the Carmen entries
    for i, obj in tqdm(unmapped_carmen_locations_df.iterrows(), desc="Locations", total=len(unmapped_carmen_locations_df)):
        if obj.city != "":
            continue
            match = map_city(obj)
        elif obj.county != "":
            match = map_county(obj)
        elif obj.state != "":
            continue
            match = map_state(obj)
        elif obj.country != "":
            continue
            match = map_country(obj)
        else:
            logging.info(f"Skipping {obj}")
            continue
        if match is not None:
            mapped_locations[obj.id] = match.to_dict()
        else:
            logging.info(f"No match for {obj.id},{obj.city},{obj.county},{obj.state}({obj.statecode}),{obj.countrycode}")

    num_mapped = len(mapped_locations)
    logging.info(f"Writing {num_mapped:,} out of {total_num_locations:,} ({num_mapped/total_num_locations:.2%}) mapped locations to file.")
    with open(mapping_file, "wb") as f:
        pickle.dump(mapped_locations, f)
    output = ""
    for i, item in enumerate(mapped_locations.items()):
        output += f"{item}\n"
        if i > 10:
            break
    logging.info(output)

    # Combine the mapped locations with the Geonames entries
    combined_entries = []
    carmen_locations = carmen_locations_df.set_index("id").to_dict(orient="index")
    for carmen_id, geonames_loc in mapped_locations.items():
        carmen_loc = carmen_locations.get(carmen_id)
        geonames_loc["old_id"] = str(carmen_id)
        geonames_loc["aliases"] = set(geonames_loc.get("aliases"))
        geonames_loc["aliases"].update(carmen_loc.get("aliases", []))
        geonames_loc["radius"] = carmen_loc.get("radius", 0)
        geonames_loc["postal"] = carmen_loc.get("postal", "")
        geonames_loc["uzip"] = carmen_loc.get("uzip", "")
        if geonames_loc["country"] == "":
            geonames_loc["country"] = carmen_loc.get("country", "")
        if geonames_loc["state"] == "":
            geonames_loc["state"] = carmen_loc.get("state", "")
        if geonames_loc["county"] == "":
            geonames_loc["county"] = carmen_loc.get("county", "")

        if not geonames_loc["latitude"]:
            geonames_loc["latitude"] = carmen_loc.get("latitude", "")
        if not geonames_loc["longitude"]:
            geonames_loc["longitude"] = carmen_loc.get("longitude", "")

        # Get the new parent ID
        c_parent = carmen_loc.get("parent_id")
        if c_parent in mapped_locations:
            parent = mapped_locations[c_parent]
            parent_id = parent.get("id", "-1")
            geonames_loc["parent_id"] = str(parent_id)
        else:
            geonames_loc["parent_id"] = "-1"

        for loc in ["city", "county", "state"]:
            if carmen_loc[loc] != "" and carmen_loc[loc] != geonames_loc[loc]:
                geonames_loc["aliases"].add(carmen_loc[loc])
        combined_entries.append(geonames_loc)
    combined_entries = pd.DataFrame(combined_entries)
    combined_entries.fillna("", inplace=True)

    # Add in the rest of the geonames entries
    unmapped_geonames = geonames_locations_df[~geonames_locations_df.id.isin(combined_entries.id)]
    combined_entries = pd.concat([combined_entries, unmapped_geonames])

    # Write out to file
    combined_entries.to_json(outfile, lines=True, orient="records")
