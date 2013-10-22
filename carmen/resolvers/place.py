# TODO:  Write docstring.


from collections import defaultdict
from itertools import count
import re

from ..location import Location, EARTH
from ..names import ALTERNATIVE_COUNTRY_NAMES, US_STATE_ABBREVIATIONS


STATE_RE = re.compile(r'.+,\s*(\w+)')


class PlaceResolver(object):
    # TODO:  Write docstring.

    name = 'place'

    unknown_id_start = 1000000

    def __init__(self, allow_unknown_locations=True,
                       resolve_to_known_ancestor=False):
        self.allow_unknown_locations = allow_unknown_locations
        self.resolve_to_known_ancestor = resolve_to_known_ancestor
        # Lookup tables.
        self.id_to_location = {}
        self.location_to_id = {}
        self.location_to_children = defaultdict(list)
        self.location_to_parent = {}
        self.unknown_id_counter = count(self.unknown_id_start)

    def add_location(self, location):
        self.id_to_location[location.id] = location
        self.location_to_id[location] = location.id
        # Let's hope the parents are always added before their children.
        parent = self.id_to_location.get(location.parent_id)
        if parent:
            self.location_to_parent[location] = parent
            self.location_to_children[parent].append(location)

    def resolve_tweet(self, tweet):
        # TODO:  Write docstring.

        place = tweet['place']
        if not place:
            return
        country = place['country']
        if not country:
            # TODO:  Warn about this.
            return None
        country = ALTERNATIVE_COUNTRY_NAMES.get(country.lower(), country)

        location_kwargs = {
            'url': place['url'],
            'country': country
        }

        place_type = place['place_type'].lower()
        if place_type in ('neighborhood', 'poi'):
            full_name = place['full_name']
            if full_name:
                split_full_name = full_name.split(',')
                if len(split_full_name) > 1:
                    location_kwargs['city'] = split_full_name[-1]
            else:
                # TODO:  Warn about finding a place with no full_name.
                pass
        elif place_type == 'city':
            location_kwargs['city'] = place['name']
            if country.lower() == 'united states':
                full_name = place['full_name']
                if full_name:
                    # Attempt to extract a state name from the full_name.
                    match = STATE_RE.search(full_name)
                    if match:
                        state = match.group(1).lower()
                        location_kwargs['state'] = \
                            US_STATE_ABBREVIATIONS.get(state)
                else:
                    # TODO:  Warn about finding a place with no full_name.
                    pass
        elif place_type == 'admin':
            location_kwargs['state'] = place['name']
        else:
            # TODO:  Warn about unknown place type.
            pass

        location = Location(**location_kwargs)
        known_location = self.id_to_location.get(
            self.location_to_id.get(location))
        if known_location:
            return (10, known_location)
        if self.allow_unknown_locations:
            # Remember this location for future lookups.
            location.id = next(self.unknown_id_counter)
            location.twitter_url = place['url']
            location.twitter_id = place['id']
            # TODO:  This is from a version different from the
            # version add_location was ported from.
            self.add_location(location)
            return (10, location)
        if self.resolve_to_known_ancestor:
            ancestor = location
            while True:
                ancestor = ancestor.parent()
                if ancestor == EARTH:
                    break
                known_ancestor = self.id_to_location.get(
                    self.location_to_id.get(ancestor))
                if known_ancestor:
                    return (1, known_ancestor)
        return None
