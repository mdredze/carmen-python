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
from difflib import SequenceMatcher

# Config logging for debugging
logging.basicConfig(filename="geoname_mapping.log", filemode='w', level=logging.DEBUG, format='%(levelname)s: %(message)s')

# Load and format Carmen locations
carmen_filename = "../data/locations.json"
logging.info(f"Reading locations from {carmen_filename}")
carmen_locations_df = pd.read_json(carmen_filename, lines=True)
carmen_locations_df.fillna("", inplace=True)
carmen_locations_df["coordinates"] = carmen_locations_df.apply(
    lambda x: (x.latitude, x.longitude) if not pd.isna(x.latitude) else None,
    axis="columns")

# Load and format Geonames data
geonames_data_dir = "Geonames"
geonames_countries_df = pd.read_csv(
    f"{geonames_data_dir}/countryInfo.txt",
    delimiter="\t",
    header=0
)
geonames_cities_df = pd.read_csv(
    f"{geonames_data_dir}/cities15000.txt",
    delimiter="\t",
    header=0
)
geonames_cities_df["admin1 code"].fillna("", inplace=True)
geonames_cities_df["coordinates"] = geonames_cities_df.apply(lambda x: (x.latitude, x.longitude), axis="columns")
geonames_counties_df = pd.read_csv(
        f"{geonames_data_dir}/admin2Codes.txt",
        delimiter="\t",
        header=0
    )
geonames_counties_df[["country code", "admin1 code", "admin2 code"]] = geonames_counties_df.apply(
    lambda x: x["concatenated codes"].split("."),
    axis="columns",
    result_type="expand")
geonames_states_df = pd.read_csv(
        f"{geonames_data_dir}/admin1CodesASCII.txt",
        delimiter="\t",
        header=0
    )
geonames_states_df[["country code", "admin1 code"]] = geonames_states_df.apply(
    lambda x: x["code"].split("."),
    axis="columns",
    result_type="expand")

# Create master country name to code lookup
country_name_to_code = carmen_locations_df[~carmen_locations_df.countrycode.isna()].set_index("country")["countrycode"].to_dict()
geoname_country_to_code = geonames_countries_df[~geonames_countries_df.ISO.isna()].set_index("Country")["ISO"].to_dict()
country_name_to_code.update(geoname_country_to_code)

# Create master statecode (admin1 code) lookup with a state, country code pair
state_name_to_code = carmen_locations_df[carmen_locations_df.statecode!=""].set_index(["state", "countrycode"])["statecode"].to_dict()
geoname_state_to_code = geonames_states_df[~geonames_states_df["admin1 code"].isna()].set_index(["name ascii", "country code"])["admin1 code"].to_dict()
for state, code in geoname_state_to_code.items():
    if state not in state_name_to_code:
        state_name_to_code[state] = code

# Other settings
DISTANCE_THRESHOLD = 5.0  # Miles
NAME_THRESHOLD = 0.9
mapping_file = "mapped_locations_dict.pkl"
outfile = "../data/geonames_locations.json"


def name_similarity(a, b):
    """
    Graciously from StackOverflow
    https://stackoverflow.com/questions/17388213/find-the-similarity-metric-between-two-strings
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

# TODO: try with / wo county / city / state
def name_sim_with_alts(a, b, alts_a, alts_b):
    a_list = [a] + alts_a
    b_list = [b] + alts_b
    maxsim = name_similarity(a, b)
    for aa in a_list:
        for bb in b_list:
            maxsim = max(maxsim, name_similarity(aa, bb))
    return maxsim

def map_city(carmen_obj):
    match = geonames_cities_df[
        geonames_cities_df.apply(
            lambda x: _city_match(x, carmen_obj.city, carmen_obj.statecode, carmen_obj.countrycode, carmen_obj.coordinates, carmen_obj.aliases),
            axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
            logging.info(f"{len(match)} hits for {carmen_obj.city},{carmen_obj.county},{carmen_obj.state},{carmen_obj.countrycode} ({carmen_obj.id}).")
            logging.info(f"{match[['asciiname', 'admin1 code', 'country code', 'coordinates']]}")
            return
    else:
        return


def map_county(carmen_obj):
    match = geonames_counties_df[
        geonames_counties_df.apply(lambda x: _county_match(x, carmen_obj), axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        # Check for exact name match
        match = geonames_counties_df[
            geonames_counties_df.apply(
                lambda x: _county_match(x, carmen_obj, exact_match=True),
                axis="columns")
        ]
        if len(match) == 1:
            return match.iloc[0]
        logging.warning(f"{len(match)} hits for {carmen_obj.county},{carmen_obj.state},{carmen_obj.countrycode} ({carmen_obj.id}) after exact search")
        logging.warning(f"{match[['asciiname','admin1 code', 'country code']]}")
        return
    else:
        return


def map_state(carmen_obj):
    match = geonames_states_df[
        geonames_states_df.apply(
            lambda x: _state_match(x, carmen_obj),
            axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        logging.info(f"{len(match)} hits for {carmen_obj.state},{carmen_obj.countrycode} ({carmen_obj.id}) after search")
        return
    else:
        return


def map_country(carmen_obj):
    match = geonames_countries_df[
        geonames_countries_df.apply(
            lambda x: x["ISO"]==carmen_obj.countrycode or x["Country"]==carmen_obj.country,
            axis="columns")
    ]
    if len(match) == 1:
        return match.iloc[0]
    if len(match) > 1:
        logging.info(f"{len(match)} hits for {carmen_obj.country}, ({carmen_obj.countrycode}) ({carmen_obj.id})")
    else:
        return

def get_x_alts(x):
    x_alts = x.alternatenames
    if (not x_alts) or (not isinstance(x_alts, str)):
        x_alts = []
    else:
        x_alts = x_alts.split(',')
    return x_alts

def _state_match(x, carmen_obj):
    # TODO do we really need these early terminations?
    if carmen_obj.countrycode and (x["country code"] != carmen_obj.countrycode):
        return False
    # TODO name_sim_with_alts
    name_sim = name_similarity(x["name ascii"], carmen_obj.state)
    if name_sim > NAME_THRESHOLD or x["admin1 code"] == carmen_obj.statecode:
        return True
    return False


def _city_match(x, city_name, statecode, countrycode, coord, aliases):
    if countrycode and (x["country code"] != countrycode):
        return False
    if statecode and (x["admin1 code"] != statecode):
        return False
    dist = coordinate_distance(x.coordinates, coord)
    name_sim = name_sim_with_alts(x.asciiname, city_name, get_x_alts(x), aliases)
    if (name_sim >= NAME_THRESHOLD) and dist < DISTANCE_THRESHOLD:
        return True
    return False


def _county_match(x, carmen_obj, exact_match=False):
    # Check country and state
    if carmen_obj.countrycode and (x["country code"] != carmen_obj.countrycode):
        return False
    if carmen_obj.countrycode and (x["admin1 code"] != carmen_obj.statecode):
        return False
    # Check for best match or exact match
    if exact_match:
        thresh = 1.0
    else:
        thresh = NAME_THRESHOLD
    # TODO name_sim_with_alts
    if name_similarity(x.asciiname, carmen_obj.county) >= thresh:
        return True
    return False


def coordinate_distance(coord1, coord2):
    """Distance between coordinates in miles"""
    return distance.distance(coord1, coord2).miles


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
    carmen_loc["id"] = str(geonames_entry.get("geonameid", geonames_entry.get("geonameId")))
    carmen_loc["countycode"] = geonames_entry.get("admin2 code") if not pd.isna(geonames_entry.get("admin2 code")) else ""
    carmen_loc["statecode"] = geonames_entry.get("admin1 code", "")
    carmen_loc["countrycode"] = geonames_entry.get("country code", "")
    carmen_loc["longitude"] = str(geonames_entry.get("longitude", ""))
    carmen_loc["latitude"] = str(geonames_entry.get("latitude", ""))
    carmen_loc["dem"] = geonames_entry.get("dem", 0)  # Radius?

    geonames_name = geonames_entry.get("asciiname", geonames_entry.get("ascii name", geonames_entry.get("name ascii")))
    if "code" in geonames_entry:
        carmen_loc["state"] = geonames_name
    elif "concatenated codes" in geonames_entry:
        carmen_loc["county"] = geonames_name
    else:
        carmen_loc["city"] = geonames_name
    return carmen_loc


if __name__ == "__main__":
    # Fill in missing Carmen country codes
    carmen_locations_df["countrycode"] = carmen_locations_df.apply(
        lambda x: x.countrycode if x.countrycode != "" else map_country_name_to_code(x.country),
        axis="columns"
    )
    carmen_locations_df["statecode"] = carmen_locations_df.apply(
        lambda x: x.statecode if x.statecode != "" else state_name_to_code.get((x.state, x.countrycode), ""),
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

    # NOTE: DEBUG USE
    # only do 10 examples
    # print(unmapped_carmen_locations_df)
    # unmapped_carmen_locations_df = unmapped_carmen_locations_df[:10]

    # Map the Carmen entries
    for i, obj in tqdm(unmapped_carmen_locations_df.iterrows(), desc="Locations", total=len(unmapped_carmen_locations_df)):
        # NOTE: DEBUG USE
        # print(obj)
        if obj.city != "":
            match = map_city(obj)
        elif obj.county != "":
            match = map_county(obj)
        elif obj.state != "":
            match = map_state(obj)
        elif obj.country != "":
            match = map_country(obj)
        else:
            logging.info(f"Skipping {obj}")
            continue
        if match is not None:
            mapped_locations[obj.id] = match.to_dict()
            # # NOTE: DEBUG USE
            # print("Y")
            # logging.debug(f"Match found for {match}")
        else:
            # # NOTE: DEBUG USE
            # print("N")
            logging.info(f"No match for {obj.id},{obj.city},{obj.county},{obj.state}({obj.statecode}),{obj.countrycode}")

    num_mapped = len(mapped_locations)
    logging.info(f"Writing {num_mapped:,} out of {total_num_locations:,} ({num_mapped/total_num_locations:.2%}) mapped locations to file.")
    with open(mapping_file, "wb") as f:
        pickle.dump(mapped_locations, f)
    output = ""
    for i, item in enumerate(mapped_locations.items()):
        output += f"{item}\n"
        if i > 30:
            break
    logging.info(output)

    # Combine the mapped locations with the Geonames entries
    combined_entries = []
    carmen_locations = carmen_locations_df.set_index("id").to_dict(orient="index")
    for carmen_id, geonames_loc in mapped_locations.items():
        new_entry = convert_geonames_to_carmen(geonames_loc)
        carmen_loc = carmen_locations.get(carmen_id)
        new_entry["old_id"] = str(carmen_id)
        new_entry.get("aliases").update(carmen_loc.get("aliases", []))
        new_entry["radius"] = carmen_loc.get("radius", 0)
        new_entry["postal"] = carmen_loc.get("postal", "")
        new_entry["uzip"] = carmen_loc.get("uzip", "")
        if new_entry["country"] == "":
            new_entry["country"] = carmen_loc.get("country", "")
        if new_entry["state"] == "":
            new_entry["state"] = carmen_loc.get("state", "")
        if new_entry["county"] == "":
            new_entry["county"] = carmen_loc.get("county", "")

        if not new_entry["latitude"]:
            new_entry["latitude"] = carmen_loc.get("latitude", "")
        if not new_entry["longitude"]:
            new_entry["longitude"] = carmen_loc.get("longitude", "")

        # Get the new parent ID
        c_parent = carmen_loc.get("parent_id")
        if c_parent in mapped_locations:
            parent = mapped_locations[c_parent]
            parent_id = parent.get("geonameid", parent.get("geonameId"))
            new_entry["parent_id"] = str(parent_id)
        else:
            new_entry["parent_id"] = "-1"

        for loc in ["city", "county", "state"]:
            if carmen_loc[loc] != "" and carmen_loc[loc] != new_entry[loc]:
                new_entry["aliases"].add(carmen_loc[loc])

        combined_entries.append(new_entry)

    # Add in the rest of the geonames entries

    # Write out to file
    combined_entries = pd.DataFrame(combined_entries)
    combined_entries.fillna("", inplace=True)
    combined_entries.to_json(outfile, lines=True, orient="records")
