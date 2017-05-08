import json
import sys


profile_locations_filename = sys.argv[1]  # these are resolved from profile
true_locations_filename    = sys.argv[2]  # these are resolved from place/geo

profile_locations_file = open(profile_locations_filename)
true_locations_file    = open(true_locations_filename)

num_cities            = 0
num_counties          = 0
num_states            = 0
num_countries         = 0 

num_correct_cities    = 0
num_correct_counties  = 0
num_correct_states    = 0
num_correct_countries = 0

num_locations         = 0
num_resolved          = 0

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
        if 'city' in profile_location and profile_location['city'] == true_location['city']:
            num_correct_cities += 1
        num_cities += 1

    if 'county' in true_location:
        if 'county' in profile_location and profile_location['county'] == true_location['county']:
            num_correct_counties += 1
        num_counties += 1

    if 'state' in true_location:
        if 'state' in profile_location and profile_location['state'] == true_location['state']:
            num_correct_states += 1
        num_states += 1

    if 'country' in true_location:
        if 'country' in profile_location and profile_location['country'] == true_location['country']:
            num_correct_countries += 1
        num_countries += 1


sys.stdout.write(
    """
        num_correct_cities    / num_cities    : %d / %d (%.2f%%)
        num_correct_states    / num_states    : %d / %d (%.2f%%)
        num_correct_counties  / num_counties  : %d / %d (%.2f%%)
        num_correct_countries / num_countries : %d / %d (%.2f%%)
        num_resolved          / num_locations : %d / %d (%.2f%%)
    """ 
    % (
        num_correct_cities, num_cities, 
            float(num_correct_cities)/float(num_cities),
        num_correct_counties, num_counties, 
            float(num_correct_counties)/float(num_counties),
        num_correct_states, num_states, 
            float(num_correct_states)/float(num_states),
        num_correct_countries, num_countries, 
            float(num_correct_countries)/float(num_countries),
        num_resolved, num_locations, 
            float(num_resolved)/float(num_locations)
    )
)