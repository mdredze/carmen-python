"""Resolvers based on geocodes."""


from collections import defaultdict
import warnings

from geopy import Point
from geopy.distance import distance as geopy_distance

from ..location import EARTH
from ..resolver import AbstractResolver, register

def safe_get(dic, key):
    temp = dic.get(key)
    return {} if temp is None else temp

@register('geocode')
class GeocodeResolver(AbstractResolver):
    """A resolver that locates a tweet by finding the known location
    with the shortest geographic distance from the tweet's coordinates.
    """

    def __init__(self, max_distance=25, cell_size=0.5):
        self.max_distance = float(max_distance)
        self.cell_size = float(cell_size)
        self.location_map = defaultdict(dict)

    def round_func(self, x):
        return round(x / self.cell_size)

    def _cell_for(self, latitude, longitude):
        '''Return the corresponding cell (based on cell_size) for location at *latitude* and *longitude*'''
        return (self.round_func(latitude), self.round_func(longitude))

    def _neighbors(self, cell):
        x,y = cell
        for i in [x-1,x,x+1]:
            for j in [y-1,y,y+1]:
                yield (i,j)

    def add_location(self, location):
        if not location.latitude and location.longitude:
            return
        for cell in self._neighbors(self._cell_for(location.latitude,location.longitude)):
            self.location_map[cell][location.id] = location

    def resolve_tweet(self, tweet):
        # 
        # Update for APIv2: the coordinates are in the field
        #       data->geo->coordinates->coordinates
        # if they exist. The coordinates is a list with size 2.
        # 
        # The Twitter API allows tweet['coordinates'] to both be absent
        # and None, such that the key exists but has a None value.
        # "tweet.get('coordinates', {})" would return None in the latter
        # case, with None.get() in turn causing an AttributeError. (None
        # or {}), on the other hand, is {}, and {}.get() is okay.
        data = tweet.get('data')
        if data is None:
            # API v1
            v2 = False
            tweet_coordinates = (tweet.get('coordinates') or {}).get('coordinates')
        else:
            # API v2
            v2 = True
            geo = data.get('geo') or {}
            tweet_coordinates = (geo.get('coordinates') or {}).get('coordinates')

        if not tweet_coordinates:
            if v2:
                # Works in v2
                # Enhancement (Jack 09/15/21): another way to get coordinates is from 
                #       includes->places->[0]->geo->bbox
                # the bbox is a list of four coordinates. 
                # Avg 0 and 2 to get 1st coord, and avg 1 & 3 to get the 2nd 
                places = tweet.get('includes', {}).get('places', None)
                if not places:
                    return None
                place = places[0]
                bbox = place.get('geo', {}).get('bbox')
                if not bbox:
                    return None
                float_coords = [
                    (float(bbox[0])+float(bbox[2]))/2,
                    (float(bbox[1])+float(bbox[3]))/2
                ]
                tweet_coordinates = [
                    float(f"{float_coords[0]:.7f}"), 
                    float(f"{float_coords[1]:.7f}")
                ]
            else:
                # v1:
                #       place->bounding_box->coordinates->[0]->a list of lists of len 2 (long, lat)
                coords = safe_get(safe_get(tweet, 'place'), 'bounding_box').get('coordinates')
                # coords = tweet.get('place', {}).get('bounding_box', {}).get('coordinates', None)
                if not coords:
                    return None
                coords = coords[0]
                coords = [[float(el) for el in ls] for ls in coords]
                # list(zip(*[[1,2],[3,4],[5,6]])) -> [(1, 3, 5), (2, 4, 6)]
                coords_transform = list(zip(*coords))
                coords_avg = [sum(el)/len(el) for el in coords_transform]
                assert len(coords_avg) == 2
        if tweet_coordinates is None: return
        tweet_coordinates = Point(longitude=tweet_coordinates[0],
                                  latitude=tweet_coordinates[1])
        closest_candidate = None
        closest_distance = float('inf')
        for candidate in self.location_map[self._cell_for(tweet_coordinates.latitude,tweet_coordinates.longitude)].values():
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
