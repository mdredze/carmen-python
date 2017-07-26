import json
import psycopg2


CONN = psycopg2.connect("dbname='carmen' user='hhan' password=''")
CUR = CONN.cursor()


def get_parent_id(child_id):
    """
    Returns the parent ID associated with a Geonames location, given the ID of that particular
    location.
    """
    CUR.execute("SELECT parent_id FROM hierarchy "
                "WHERE child_id = %s;",
                (child_id,))
    parent_query = CUR.fetchone()
    return parent_query[0] if parent_query else -1


def get_county(admin2_code, country_code):
    """
    Returns the county associated with a Geonames location, given the admin2 code and country code
    of that particular location.
    """
    CUR.execute("SELECT name, id FROM admin2_codes "
                "WHERE admin2_code = %s AND country_code = %s;",
                (admin2_code, country_code))
    result = CUR.fetchone()
    return (result[0], result[1]) if result else ('', '')


def get_state(admin1_code, country_code):
    """
    Returns the state associated with a Geonames location, given the admin2 code and admin1 code
    of that particular location.
    """
    CUR.execute("SELECT name, id FROM admin1_codes "
                "WHERE admin1_code = %s AND country_code = %s;",
                (admin1_code, country_code))
    result = CUR.fetchone()
    return (result[0], result[1]) if result else ('', '')


def get_country(iso):
    """
    Returns the country associated with a Geonames location, given the iso code of that particular
    location.
    """
    CUR.execute("SELECT country, geoname_id FROM country_info "
                "WHERE iso = %s;",
                (iso,))
    result = CUR.fetchone()
    return (result[0], result[1]) if result else ('', '')


def write_cities(json_file):
    """
    Writes each city contained in the cities_file as a JSON object to the provided json_file
    argument.
    """

    cities_file = open('../data/dump/cities15000.txt', 'r')

    for line in cities_file:

        details = line.split('\t')
        geonames_id = details[0]
        name = details[2]
        alternative_names = details[3].split(',')
        latitude = details[4]
        longitude = details[5]
        country_code = details[8]
        admin1_code = details[10]
        admin2_code = details[11]

        country, country_id = get_country(country_code)
        state, state_id = get_state(admin1_code, country_code)
        county, county_id = get_county(admin2_code, country_code)

        if county_id:
            parent_id = county_id
        elif state_id:
            parent_id = state_id
        elif country_id:
            parent_id = country_id
        else:
            parent_id = -1
        
        output = {
            'city'        : name,
            'county'      : county,
            'state'       : state,
            'country'     : country,
            'countycode'  : admin2_code,
            'statecode'   : admin1_code,
            'countrycode' : country_code,
            'latitude'    : latitude,
            'longitude'   : longitude,
            'id'          : int(geonames_id),
            'parent_id'   : int(parent_id),
            'aliases'     : alternative_names
        }
        json.dump(output, json_file, ensure_ascii=False)
        json_file.write('\n')

    cities_file.close()
    print('write_cities done')


def write_counties(json_file):
    """
    Writes each county contained in the counties_file as a JSON object to the provided json_file
    argument.
    """

    counties_file = open('../data/dump/admin2Codes.txt', 'r')

    for line in counties_file:

        details = line.split('\t')

        geonames_id = int(details[4].strip())
        name = details[3]
        alternative_names = [ details[2] ]

        country_code = details[0]
        country, country_id = get_country(country_code)

        state_code = details[1]
        state, state_id = get_state(state_code, country_code)

        parent_id = state_id
        if parent_id == '':
            parent_id = -1

        latitude = ''
        longitude = ''

        output = {
            'city'        : '',
            'county'      : name,
            'state'       : state,
            'country'     : country,
            'countycode'  : int(geonames_id),
            'statecode'   : state_code,
            'countrycode' : country_code,
            'latitude'    : '',
            'longitude'   : '',
            'id'          : int(geonames_id),
            'parent_id'   : int(parent_id),
            'aliases'     : alternative_names
        }
        json.dump(output, json_file, ensure_ascii=False)
        json_file.write('\n')

    counties_file.close()
    print("write_counties done")


def write_states(json_file):
    """
    Writes each state contained in the states_file as a JSON object to the provided json_file
    argument.
    """
    
    states_file = open('../data/dump/admin1Codes.txt', 'r')

    for line in states_file:

        details = line.split('\t')

        geonames_id = int(details[4].strip())
        name = details[3]
        alternative_names = [ details[2] ]

        country_code = details[0]
        country, country_id = get_country(country_code)

        state_code = details[1]
        state, state_id = get_state(state_code, country_code)

        parent_id = country_id
        if parent_id == '':
            parent_id = -1

        output = {
            'city'        : '',
            'county'      : '',
            'state'       : state,
            'country'     : country,
            'countycode'  : '',
            'statecode'   : state_code,
            'countrycode' : country_code,
            'latitude'    : '',
            'longitude'   : '',
            'id'          : int(geonames_id),
            'parent_id'   : int(parent_id),
            'aliases'     : alternative_names
        }
        json.dump(output, json_file, ensure_ascii=False)
        json_file.write('\n')

    states_file.close()
    print("write_states done")


def write_countries(json_file):
    """
    Writes each state contained in the states_file as a JSON object to the provided json_file
    argument.
    """
    
    countries_file = open('../data/dump/country_info.txt', 'r')

    for line in countries_file:

        details = line.split('\t')

        geonames_id = int(details[16])
        name = details[4]

        country_code = details[0]

        output = {
            'city'        : '',
            'county'      : '',
            'state'       : '',
            'country'     : name,
            'countycode'  : '',
            'statecode'   : '',
            'countrycode' : country_code,
            'latitude'    : '',
            'longitude'   : '',
            'id'          : int(geonames_id),
            'parent_id'   : -1,
            'aliases'     : []
        }
        json.dump(output, json_file, ensure_ascii=False)
        json_file.write('\n')

    countries_file.close()
    print("write_countries done")


def main():

    json_file = open('../data/newnew.json', 'w')
    write_cities(json_file)
    write_counties(json_file)
    write_states(json_file)
    write_countries(json_file)


if __name__ == '__main__':
    main()
