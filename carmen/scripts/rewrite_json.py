import json
import sys


carmen_filename  = '../data/locations.json'
new_filename     = '../data/new.json'
cities_filename  = '../mappings/cities.txt'
regions_filename = '../mappings/regions.txt'


def rewrite_json(old_filename, new_filename, cities_mapping, regions_mapping):
    old_file = open(old_filename, "r")
    new_file = open(new_filename, "w")

    num_success = 0
    num_errors  = 0
    for line in old_file:
        data      = json.loads(line)   # get the data from the JSON file, and
        carmen_id = data['id']         # retrieve its carmen ID and its parent
        parent_id = data['parent_id']  # ID

        if ( data['city'] != '' ):
            try:
                if data['id'] == "-1":
                    pass
                else:
                    data['id'] = cities_mapping[carmen_id]
            except KeyError:
                num_errors += 1
                sys.stderr.write(
                    "%s (%s, %s, %s) is not a valid Geonames ID\n" 
                    % (data['id'], data['city'], data['state'], data['country'])
                )
                continue
        else:
            try:
                if data['id'] == "-1":
                    pass
                else:
                    data['id'] = regions_mapping[carmen_id]
            except KeyError:
                num_errors += 1
                if ( data['county'] != '' ):
                    sys.stderr.write(
                        "%s (%s, %s) is not a valid Geonames ID\n" 
                        % (data['id'], data['county'], data['country'])
                    )
                elif ( data['state'] != '' ):
                    sys.stderr.write(
                        "%s (%s, %s) is not a valid Geonames ID\n" 
                        % (data['id'], data['state'], data['country'])
                    )
                else:
                    sys.stderr.write(
                        "%s (%s) is not a valid Geonames ID\n" 
                        % (data['id'], data['country'])
                    )
                continue

        try:
            if data['parent_id'] == "-1":
                pass
            else:
                data['parent_id'] = regions_mapping[parent_id] # their Geonames IDs
        except KeyError:
            num_errors += 1
            sys.stderr.write("parent ID " + data['parent_id'] + " is not a valid Geonames ID\n")
            continue

        json.dump(data, new_file)               # write result to file
        new_file.write("\n")
        num_success += 1

    old_file.close()
    new_file.close()

    sys.stderr.write("num success : %d\n" % num_success)
    sys.stderr.write("num errors  : %d\n" % num_errors)


def main():
    cities_file     = open(cities_filename, "r")
    regions_file    = open(regions_filename, "r")
    cities_mapping  = {}
    regions_mapping = {}
    for line in cities_file:
        components = "".join(line.split()).split("(")[0].split("->")
        cities_mapping[components[0]] = components[1]
    for line in regions_file:
        components = "".join(line.split()).split("(")[0].split("->")
        regions_mapping[components[0]] = components[1]
    cities_file.close()
    regions_file.close()
    
    rewrite_json(carmen_filename, new_filename, cities_mapping, regions_mapping)


if __name__ == '__main__':
    main()