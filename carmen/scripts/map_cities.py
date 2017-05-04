import json
import psycopg2
import sys


# Connect to the database
conn = psycopg2.connect("dbname='carmen' user='hhan' password=''")
cur  = conn.cursor()

# This is the name of the Carmen data file
carmen_filename = '../data/africa_middle_east.json'


def find_countrycode(country_name):
    cur.execute(
        "SELECT iso FROM country_info "
        "WHERE country = %s;", 
        (country_name,)
    )
    x = cur.fetchone()
    country_code = x[0]
    return country_code


def search_alternatenames(data, country_code):
    city      = data['city']
    latitude  = data['latitude']                # If we couldn't find the name
    longitude = data['longitude']               # of our city in Geonames, then
                                                # perhaps we should try checking
    cur.execute(                                # the alternate names.
        "SELECT id, alternatenames "
        "FROM cities WHERE "                    # The 'aliases' attribute in the
        "latitude  >= %s AND "                  # Carmen data isn't too great, so
        "latitude  <  %s AND "                  # we will instead check Geonames'
        "longitude >= %s AND "                  # 'alternatenames' field, which
        "longitude <  %s AND "                  # returns a strings separated by
        "alternatenames IS NOT NULL AND "       # commas.
        "country_code = %s;",
        (                                       # We will query only on nearby
            str(float(latitude)-1),             # locations, of +/- 1 degree of
            str(float(latitude)+1),             # latitude/longitude, with the
            str(float(longitude)-1),            # same country code as the 
            str(float(longitude)+1),            # city we are searching for.
            country_code 
        )
    )
    possible_locations = cur.fetchall()
                                                # Now we iterate over all of the
    name_found = False                          # possible locations, and try to
    for t in possible_locations:                # find a match between our city
        alternatenames = t[1].split(',')        # name and one of the many
        for n in alternatenames:                # alternate names from Geonames
            if city == n:                       
                location = t                    # If we find the name, then we
                return location                 # can write our output. Otherwise
    return None                                 # we give up.


def write_output(carmen_id, geonames_id, city, region, country_code):
    sys.stdout.write(
        "%s -> %d    (%s, %s, %s)\n" 
        % (carmen_id, geonames_id, city, region, country_code)
    )


def main():

    carmen_data = open(carmen_filename)

    num_success           = 0  # these numbers are used to track
    invalid_country_names = 0  # statistics of how good our mapping
    nonexistent_names     = 0  # is

    for line in carmen_data:
        data = json.loads(line)

        if data['city'] != '':

            carmen_id = data['id']
            city      = data['city']

            # first check if this has a country code
            if 'countrycode' in data:
                country_code = data['countrycode']
            else:
                # otherwise, we can try to look up the country code
                country = data['country']
                country_code = find_countrycode(country)
            
            if data['state'] != '':       # we will attempt to use the Carmen 'state' field as
                region = data['state']    # the encapsulating region.
            else:                         # if it doesn't exist, then we use the 'county' field
                region = data['county']   # instead.

            cur.execute(
                "SELECT admin1_code FROM admin1_codes "
                "WHERE name = %s AND country_code = %s;", 
                (region, country_code)
            )
            x = cur.fetchone()
            if x == None:
                admin1_code = "N/A"
                cur.execute(
                    "SELECT id FROM cities WHERE "      # this is the case that we could not
                    "name = %s AND "                    # not find an actual region name
                    "country_code = %s;", 
                    (city, country_code)
                )
                x = cur.fetchone()
            else:
                admin1_code = x[0]
                cur.execute(
                    "SELECT id FROM cities WHERE "      # this is the case that we found a
                    "name = %s AND "                    # region name, and so we can use it
                    "admin1_code = %s AND "             # to locate the city
                    "country_code = %s;", 
                    (city, admin1_code, country_code)
                )
                x = cur.fetchone()
    
            # if we couldn't find it, then maybe we should try to check for alternative names.
            # if we STILL can't find it, then we will say it doesn't exist in Geonames.
            if (x == None):
    
                location = search_alternatenames(data, country_code)
                if location == None:
                    sys.stderr.write(
                        "%s, %s (%s), %s does not exist in Geonames\n" 
                        % (city, region, admin1_code, country_code)
                    )
                    nonexistent_names += 1
                else:
                    geonames_id = location[0]
                    write_output(carmen_id, geonames_id, city, region, country_code)
                    num_success += 1
            else:
                geonames_id = x[0]
                write_output(carmen_id, geonames_id, city, region, country_code)
                num_success += 1

    carmen_data.close()

    # Print out statistics
    sys.stderr.write("invalid country names          : %d\n" % (invalid_country_names))
    sys.stderr.write("nonexistent Geonames locations : %d\n" % (nonexistent_names))
    sys.stderr.write("successful mappings            : %d\n" % (num_success))


if __name__ == '__main__':
    main()
