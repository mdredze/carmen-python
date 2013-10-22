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
