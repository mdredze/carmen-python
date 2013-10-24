# TODO:  Write docstring.


from collections import defaultdict

from geopy import Point
from geopy.distance import distance as geopy_distance


class GeocodeResolver(object):
    # TODO:  Write docstring.

    name = 'geocode'
    cell_size = 100.0

    def __init__(self, max_distance=25):
        self.max_distance = max_distance
        self.location_map = defaultdict(list)

    def _cells_for(self, latitude, longitude):
        """Return a list of cells containing the location at *latitude*
        and *longitude*."""
        latitude = latitude * self.cell_size
        longitude = longitude * self.cell_size
        shift_size = self.cell_size / 2
        for latitude_cell in (latitude - shift_size,
                              latitude, latitude + shift_size):
            for longitude_cell in (longitude - shift_size,
                                   longitude, longitude + shift_size):
                yield (int(latitude_cell / self.cell_size),
                       int(longitude_cell / self.cell_size))

    def add_location(self, location):
        """Add a known location to the resolver."""
        if not (location.latitude and location.longitude):
            # TODO:  Should we warn here?
            return
        for cell in self._cells_for(location.latitude, location.longitude):
            self.location_map[cell].append(location)

    def resolve_tweet(self, tweet):
        # TODO:  Write docstring.
        tweet_coordinates = tweet.get('coordinates', {}).get('coordinates')
        if not tweet_coordinates:
            return None
        tweet_coordinates = Point(longitude=tweet_coordinates[0],
                                  latitude=tweet_coordinates[1])
        closest_candidate = None
        closest_distance = float('inf')
        for cell in self._cells_for(tweet_coordinates.latitude,
                                    tweet_coordinates.longitude):
            for candidate in self.location_map[cell]:
                candidate_coordinates = Point(
                    candidate.latitude, candidate.longitude)
                distance = geopy_distance(
                    tweet_coordinates, candidate_coordinates).miles
                if closest_distance > distance:
                    closest_candidate = candidate
                    closest_distance = distance
        if closest_distance < self.max_distance:
            return (9, closest_candidate)
        return None
