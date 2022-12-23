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

### Carmen 2.0 Improvements
We are excited to release the improved Carmen Twitter geotagger, Carmen 2.0! We have implemented the following improvements:
- A new location database derived from the open-source [GeoNames](https://www.geonames.org/) geographical database. This multilingual database improves the coverage and robustness of Carmen as shown in our analysis paper "[Changes in Tweet Geolocation over Time: A Study with Carmen 2.0](https://aclanthology.org/2022.wnut-1.1/)".
- Compatibility with Twitter API V2.
- An up to 10x faster geocode resolver.

### GeoNames Mapping

We provide two different location databases.
- `carmen/data/geonames_locations_combined.json` is the new GeoNames database introduced in Carmen 2.0. It is derived by swapping out to use GeoNames IDs instead of arbitrary IDs used in the original version of Carmen. This database will be used by default.
- `carmen/data/locations.json` is the default database in original carmen. This is faster but less powerful compared to our new database. You can use the `--locations` flag to switch to this version of database for backward compatibility.

We refer reader to the Carmen 2.0 paper repo for more details of GeoNames mapping: https://github.com/AADeLucia/carmen-wnut22-submission

### Building for Release

1. In the repo root folder, `python setup.py sdist bdist_wheel` to create the wheels in `dist/` directory
2. `python -m twine upload --repository testpypi dist/*` to upload to testpypi
3. **Create a brand new environment**, and do `pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple carmen` to make sure it can be installed correctly from testpypi
4. After checking correctness, use `python -m twine upload dist/*` to publish on actual pypi

### Reference
If you use the Carmen 2.0 package, please cite the following work:
```
@inproceedings{zhang-etal-2022-changes,
    title = "Changes in Tweet Geolocation over Time: A Study with Carmen 2.0",
    author = "Zhang, Jingyu  and
      DeLucia, Alexandra  and
      Dredze, Mark",
    booktitle = "Proceedings of the Eighth Workshop on Noisy User-generated Text (W-NUT 2022)",
    month = oct,
    year = "2022",
    address = "Gyeongju, Republic of Korea",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2022.wnut-1.1",
    pages = "1--14",
    abstract = "Researchers across disciplines use Twitter geolocation tools to filter data for desired locations. These tools have largely been trained and tested on English tweets, often originating in the United States from almost a decade ago. Despite the importance of these tools for data curation, the impact of tweet language, country of origin, and creation date on tool performance remains largely unknown. We explore these issues with Carmen, a popular tool for Twitter geolocation. To support this study we introduce Carmen 2.0, a major update which includes the incorporation of GeoNames, a gazetteer that provides much broader coverage of locations. We evaluate using two new Twitter datasets, one for multilingual, multiyear geolocation evaluation, and another for usage trends over time. We found that language, country origin, and time does impact geolocation tool performance.",
}
```