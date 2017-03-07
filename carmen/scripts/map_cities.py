import json
import psycopg2
import sys


# Connect to the database
conn = psycopg2.connect("dbname='carmen' user='hhan' password=''")


def main():
    cur = conn.cursor()

    carmen_filename = '../data/locations.json'
    carmen_data = open(carmen_filename)

    num_success           = 0
    invalid_country_names = 0
    nonexistent_names     = 0

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
                cur.execute("SELECT iso FROM country_info WHERE country = %s;", (country,))
                x = cur.fetchone()

                if x == None:
                    # if the country code does not exist in Geonames, then we have a problem
                    sys.stderr.write("%s does not have a valid country_code in Geonames\n" % (country))
                    invalid_country_names += 1
                    continue
                else:
                    country_code = x[0]
            
            if data['state'] != '':
                region = data['state']
            else:
                region = data['county']

            cur.execute(
                "SELECT admin1_code FROM admin1_codes "
                "WHERE name = %s AND country_code = %s;", (region, country_code)
            );
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
    
            # if we couldn't find it, then obviously it doesn't exist in Geonames. Otherwise write it to STDOUT
            if (x == None):
                sys.stderr.write(
                    "%s, %s (%s), %s does not exist in Geonames\n" 
                    % (city, region, admin1_code, country_code)
                )
                nonexistent_names += 1
            else:
                geonames_id = x[0]
                sys.stdout.write(
                    "%s -> %d    (%s, %s, %s)\n" 
                    % (carmen_id, geonames_id, city, region, country_code)
                )
                num_success += 1

    carmen_data.close()

    # Print out statistics
    sys.stderr.write("invalid country names          : %d\n" % (invalid_country_names))
    sys.stderr.write("nonexistent Geonames locations : %d\n" % (nonexistent_names))
    sys.stderr.write("successful mappings            : %d\n" % (num_success))


if __name__ == '__main__':
    main()