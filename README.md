# Carmen

A Python version of [Carmen](https://github.com/mdredze/carmen),
a library for geolocating tweets.

Given a tweet, Carmen will return `Location` objects that represent a
physical location.
Carmen uses both coordinates and other information in a tweet to make
geolocation decisions.
It's not perfect, but this greatly increases the number of geolocated
tweets over what Twitter provides.

To install, simply run:

    $ python setup.py install

To run the Carmen frontend, see:

    $ python -m carmen.cli --help

### Geonames Mapping

Alternatively, `locations.json` can be swapped out to use Geonames IDs
instead of arbitrary IDs used in the original version of Carmen. This
JSON file can be found in `carmen/data/new.json`.

Below are instructions on how mappings can be generated.

First, we need to get the data. This can be found at 
http://download.geonames.org/export/dump/. The required files are 
`countryInfo.txt`, `admin1CodesASCII.txt`, `admin2Codes.txt`, and
`cities1000.txt`. Download these files and move them into
`carmen/data/dump/`.

Next, we need to format our data. We can simply delete the comments in
`countryInfo.txt`. Afterwards, run the following.

    $ python3 format_admin1_codes.py
    $ python3 format_admin2_codes.py

Then, we need to set up a PostgreSQL database, as this allows finding
relations between the original Carmen IDs and Geonames IDs significantly
easier. To set up the database, create a PostgreSQL database named `carmen` 
and reun the following SQL script:

    $ psql -f carmen/sql/populate_db.sql carmen
    
Now we can begin constructing the mappings from Carmen IDs to
Geonames IDs. Run the following scripts.

    $ python3 map_cities.py > ../mappings/cities.txt
    $ python3 map_regions.py > ../mappings/regions.txt
    
With the mappings constructed, we can finally attempt to convert the
`locations.json` file into one that uses Geonames IDs. To do this, run
the following.

    $ python3 rewrite_json.py

### building for release

1. In the repo root folder, `python setup.py sdist bdist_wheel` to create the wheels in `dist/` directory
2. `python -m twine upload --repository testpypi dist/*` to upload to testpypi
3. **Create a brand new environment**, and do `pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple carmen` to make sure it can be installed correctly from testpypi
4. After checking correctness, use `python -m twine upload dist/*` to publish on actual pypi
