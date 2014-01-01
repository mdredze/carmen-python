"""Resolvers based on geocodes."""


from collections import defaultdict
import warnings

from geopy import Point
from geopy.distance import distance as geopy_distance

from ..location import EARTH
from ..resolver import AbstractResolver, register


@register('geocode')
class GeocodeResolver(AbstractResolver):
    """A resolver that locates a tweet by finding the known location
    with the shortest geographic distance from the tweet's coordinates.
    """

    cell_size = 100.0

    def __init__(self, max_distance=25):
        self.max_distance = float(max_distance)
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
        if not location.latitude and location.longitude:
            return
        for cell in self._cells_for(location.latitude, location.longitude):
            self.location_map[cell].append(location)

    def resolve_tweet(self, tweet):
        # The Twitter API allows tweet['coordinates'] to both be absent
        # and None, such that the key exists but has a None value.
        # "tweet.get('coordinates', {})" would return None in the latter
        # case, with None.get() in turn causing an AttributeError. (None
        # or {}), on the other hand, is {}, and {}.get() is okay.
        tweet_coordinates = (tweet.get('coordinates') or {}).get('coordinates')
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
            return (False, closest_candidate)
        return None
