import json
import sys


profile_locations_filename = sys.argv[1]  # these are resolved from profile
true_locations_filename    = sys.argv[2]  # these are resolved from place/geo

profile_locations_file = open(profile_locations_filename)
true_locations_file    = open(true_locations_filename)

num_cities              = 0  # These variables represent the total number of
num_counties            = 0  # true locations of each kind. For example, if the
num_states              = 0  # geotag and place resolvers found 20 cities, then
num_countries           = 0  # we would have num_cities = 20.

num_predicted_cities    = 0  # These variables represent the number of
num_predicted_states    = 0  # prediction attempts made by the profile
num_predicted_counties  = 0  # resolver, regardless if those predictions were
num_predicted_countries = 0  # correct or not.

num_correct_cities      = 0  # These variables represent the number of correct
num_correct_counties    = 0  # predictions made by the profile resolver.
num_correct_states      = 0
num_correct_countries   = 0

num_locations           = 0
num_resolved            = 0

for profile_line, true_line in zip(profile_locations_file, true_locations_file):

    true_data = json.loads(true_line)
    if 'location' not in true_data:
        continue
    
    num_locations += 1
    
    profile_data = json.loads(profile_line)
    if 'location' not in profile_data:
        continue
    
    num_resolved += 1
    
    true_location    = true_data['location']
    profile_location = profile_data['location']

    if 'city' in true_location:
        if 'city' in profile_location: 
            if profile_location['city'] == true_location['city']:
                num_correct_cities += 1
            num_predicted_cities += 1
        num_cities += 1

    if 'county' in true_location:
        if 'county' in profile_location: 
            if profile_location['county'] == true_location['county']:
                num_correct_counties += 1
            num_predicted_counties += 1
        num_counties += 1

    if 'state' in true_location:
        if 'state' in profile_location: 
            if profile_location['state'] == true_location['state']:
                num_correct_states += 1
            num_predicted_states += 1
        num_states += 1

    if 'country' in true_location:
        if 'country' in profile_location: 
            if profile_location['country'] == true_location['country']:
                num_correct_countries += 1
            num_predicted_countries += 1
        num_countries += 1


sys.stdout.write(
    """
    ======================== STATISTICS ========================
    (ACC = accuracy, PRC = precision, COV = coverage)

    CITIES    ACC, num_correct_cities    / num_cities    : %d / %d (%.2f%%)
    COUNTIES  ACC, num_correct_counties  / num_counties  : %d / %d (%.2f%%)
    STATES    ACC, num_correct_states    / num_states    : %d / %d (%.2f%%)
    COUNTRIES ACC, num_correct_countries / num_countries : %d / %d (%.2f%%)

    CITIES    PRC, num_correct_cities    / num_predicted_cities    : %d / %d (%.2f%%)
    COUNTIES  PRC, num_correct_counties  / num_predicted_counties  : %d / %d (%.2f%%)
    STATES    PRC, num_correct_states    / num_predicted_states    : %d / %d (%.2f%%)
    COUNTRIES PRC, num_correct_countries / num_predicted_countries : %d / %d (%.2f%%)

    CITIES    COV, num_predicted_cities    / num_cities    : %d / %d (%.2f%%)
    COUNTIES  COV, num_predicted_counties  / num_counties  : %d / %d (%.2f%%)
    STATES    COV, num_predicted_states    / num_states    : %d / %d (%.2f%%)
    COUNTRIES COV, num_predicted_countries / num_countries : %d / %d (%.2f%%)
    
    num_resolved          / num_locations : %d / %d (%.2f%%)
    ============================================================
    """ 
    % (
        # ACCURACY
        num_correct_cities, num_cities, 
            100*float(num_correct_cities)/float(num_cities),
        num_correct_counties, num_counties, 
            100*float(num_correct_counties)/float(num_counties),
        num_correct_states, num_states, 
            100*float(num_correct_states)/float(num_states),
        num_correct_countries, num_countries, 
            100*float(num_correct_countries)/float(num_countries),
        
        # PRECISION
        num_correct_cities, num_predicted_cities, 
            100*float(num_correct_cities)/float(num_predicted_cities),
        num_correct_counties, num_predicted_counties, 
            100*float(num_correct_counties)/float(num_predicted_counties),
        num_correct_states, num_predicted_states, 
            100*float(num_correct_states)/float(num_predicted_states),
        num_correct_countries, num_predicted_countries, 
            100*float(num_correct_countries)/float(num_predicted_countries),

        # COVERAGE
        num_predicted_cities, num_cities, 
            100*float(num_predicted_cities)/float(num_cities),
        num_predicted_counties, num_counties, 
            100*float(num_predicted_counties)/float(num_counties),
        num_predicted_states, num_states, 
            100*float(num_predicted_states)/float(num_states),
        num_predicted_countries, num_countries, 
            100*float(num_predicted_countries)/float(num_countries),

        # TOTAL
        num_resolved, num_locations, 
            100*float(num_resolved)/float(num_locations)
    )
)