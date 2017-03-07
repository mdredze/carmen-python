import json
import psycopg2
import sys


# Connect to the database
conn = psycopg2.connect("dbname='carmen' user='hhan' password=''")


def country_to_country_id():
    """
    Returns a mapping from country name to Geoname country code
    """
    mapping = {}

    countries_file = open('../data/dump/countryInfo.txt', 'r')
    for line in countries_file:
        data       = line.split('\t')
        country_id = data[0]
        country    = data[4]
        mapping[country] = country_id
    countries_file.close()

    return mapping


def main():
    cur = conn.cursor()

    # Retrieve a mapping from country name to Geoname country codes
    country_ids = country_to_country_id()

    carmen_filename = '../data/locations.json'
    carmen_data = open(carmen_filename)

    num_success           = 0
    invalid_country_names = 0
    nonexistent_names     = 0

    for line in carmen_data:
        data = json.loads(line)

        if ( data['city'] == '' and (
                (data['county'] == '' and data['state'] != '') or 
                (data['county'] != '' and data['state'] == '')
            )
        ):
            carmen_id    = data['id']
            if data['state'] != '':
                name = data['state']
            else:
                name = data['county']

            # first check if this has a country code
            if 'countrycode' in data:
                country_code = data['countrycode']
            else:
                # otherwise, we can try to look up the country code
                country = data['country']
                if country in country_ids:
                    country_code = country_ids[country]
                else:
                    # if the country code does not exist in Geonames, then we have a problem
                    sys.stderr.write("%s does not have a valid country_code in Geonames\n" % (country))
                    invalid_country_names += 1
                    continue

            # now try to find the Geoname ID of the state/county that we're looking at
            cur.execute("SELECT id FROM admin1_codes WHERE name = %s AND country_code = %s;", (name, country_code))
            x = cur.fetchone()

            # if we couldn't find it, then obviously it doesn't exist in Geonames. Otherwise write it to STDOUT
            if (x == None):
                sys.stderr.write("%s, %s does not exist in Geonames\n" % (name, country_code))
                nonexistent_names += 1
            else:
                geonames_id = x[0]
                sys.stdout.write("%s -> %d    (%s, %s)\n" % (carmen_id, geonames_id, name, country_code))
                num_success += 1

    carmen_data.close()

    # Print out statistics
    sys.stderr.write("invalid country names          : %d\n" % (invalid_country_names))
    sys.stderr.write("nonexistent Geonames locations : %d\n" % (nonexistent_names))
    sys.stderr.write("successful mappings            : %d\n" % (num_success))


if __name__ == '__main__':
    main()