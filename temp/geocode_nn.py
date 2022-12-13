"""Resolvers based on geocodes."""


from collections import defaultdict
# import dill # fix pickling lambda error
import dill as pickle
import os
import warnings

from sklearn.neighbors import NearestNeighbors
from geopy import Point
from geopy.distance import distance as geopy_distance

from ..location import EARTH
from ..resolver import AbstractResolver, register

geocode_nn_storage = './geocode_nn.pkl'

@register('geocode_nn')
class GeocodeResolver(AbstractResolver):
    """A resolver that locates a tweet by finding the known location
    with the shortest geographic distance from the tweet's coordinates.
    """

    cell_size = 3.1

    def __init__(self, max_distance=25):
        self.max_distance = float(max_distance)
        self.id2obj = {}
        self.id_list = []
        self.distance_matrix = [] # N x 2 rows. Each row is (lat, long) pair. Corresponding id for index see self.id_list
        self.nn = None


    def add_location(self, location):
        if not location.latitude and location.longitude:
            return
        self.id2obj[location.id] = location
        self.id_list.append(location.id)
        self.distance_matrix.append([location.latitude, location.longitude])

    # def distance_func(self, x, y):
    #     return geopy_distance(x,y).miles

    def _build_nn(self):
        self.nn = NearestNeighbors(n_neighbors=1, metric=lambda x,y: geopy_distance(x,y).miles)
        self.nn.fit(self.distance_matrix)

        # save created object
        # problematic...
        with open(geocode_nn_storage, 'wb') as f:
            pickle.dump(self.nn, f)

    def _build_or_load_nn(self):
        if os.path.exists(geocode_nn_storage):
            with open(geocode_nn_storage, 'rb') as f:
                self.nn = pickle.load(f)
        else: self._build_nn()            

    def resolve_tweet(self, tweet):
        if self.nn is None:
            self._build_or_load_nn()

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
                coords = tweet.get('place', {}).get('bounding_box', {}).get('coordinates', None)
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

        closest_distance, idx = self.nn.kneighbors([[tweet_coordinates.latitude, tweet_coordinates.longitude]])
        closest_distance, idx = closest_distance.item(), idx.item()
        if closest_distance < self.max_distance:
            closest_candidate = self.id2obj[self.id_list[idx]]
            return (False, closest_candidate)
        return None
