import psycopg2


# Connect to the database
conn = psycopg2.connect("dbname='carmen' user='alexandra' password='alexandra'")
cur = conn.cursor()


def fetch_id_from_region_country(region, country_code):
    cur.execute(
        f"SELECT id FROM cities "
        f"WHERE name = '{region}' AND country_code = '{country_code}';"
    )
    return cur.fetchall()


a = fetch_id_from_region_country("Dale", "TX")
print(a)