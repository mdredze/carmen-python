"""Resolvers based on Twitter Places."""
from collections import defaultdict
from itertools import count
import re
import warnings

from ..location import Location, EARTH
from ..names import ALTERNATIVE_COUNTRY_NAMES, US_STATE_ABBREVIATIONS, COUNTRY_CODES
from ..resolver import AbstractResolver, register


STATE_RE = re.compile(r'.+,\s*(\w+)')


@register('place')
class PlaceResolver(AbstractResolver):
    """A resolver that locates a tweet by matching Twitter Place
    information with a known location.  If *allow_unknown_locations* is
    True, unknown Places are added as new locations.  Otherwise, if
    *resolve_to_known_ancestor* is True, tweets with unknown Places will
    be resolved to the nearest known location containing that Place."""

    _unknown_id_start = 1000000

    def __init__(self,
                 allow_unknown_locations=False,
                 resolve_to_known_ancestor=False):
        self.allow_unknown_locations = allow_unknown_locations
        self.resolve_to_known_ancestor = resolve_to_known_ancestor
        self._locations_by_name = {}
        self._unknown_ids = count(self._unknown_id_start)
        self._valid_names = {'country': set(), 'state': set(), 'county': set(), 'city': set(), 'countrycode': set()}
        self.s2s_names = set()

    def _find_by_location(self, location):
        return self._locations_by_name.get(location.canonical())

    def _find_by_name(self, **kwargs):
        return self._locations_by_name.get(Location(**kwargs).canonical())

    def add_location(self, location):
        self._locations_by_name[location.canonical()] = location
        # jack added 11/13/22
        for name_type, name in zip(['country', 'state', 'county', 'city'], list(location.canonical())):
            self._valid_names[name_type].add(name)
        if location.countrycode is not None:
            self._valid_names['countrycode'].add(location.countrycode.lower())
        self.s2s_names.update(location.s2s_name())

        # jack added 11/6/22
        # country, state, county, city = location.canonical()
        # canonical_wo_state = (country, '', county, city)
        # self._locations_by_name[canonical_wo_state] = location
        # end 11/6/22

    def resolve_tweet(self, tweet):
        apiv2 = 'data' in tweet
        if apiv2:
            # API v2
            places = tweet.get('includes', {}).get('places', None)
            if not places:
                return
            place = places[0]
        else:
            # API v1
            place = tweet.get('place', None)
            if not place:
                return
        place_type = place['place_type'].lower()
        if place_type != 'seq2seq':
            # only infer country here if not using seq2seq
            country = place.get('country', None)
            if not country:
                warnings.warn('Tweet has Place with no country')
                return None
            country = ALTERNATIVE_COUNTRY_NAMES.get(country.lower(), country)

            name = {'country': country}

        if place_type == 'seq2seq':
            # special type: formatted place object string used by carmen seq2seq
            name = {}
            constituents = [el.strip().lower() for el in place['full_name'].split(', ')]
            if len(constituents) != 3:
                # invalid generation
                return None
            city, admin, countrycode = constituents

            if countrycode != '<country>':
                country = COUNTRY_CODES.get(countrycode, countrycode)
                name['country'] = country
            if admin != '<admin>':
                name['state'] = US_STATE_ABBREVIATIONS.get(admin, admin)
            if city != '<city>':
                name['city'] = city
        elif place_type in ('neighborhood', 'poi'):
            full_name = place['full_name']
            if full_name:
                split_full_name = full_name.split(',')
                if len(split_full_name) > 1:
                    name['city'] = split_full_name[-1]
            else:
                warnings.warn('Tweet has Place with no neighborhood or '
                              'point of interest full name')
        elif place_type == 'city':
            name['city'] = place['name']
            if country.lower() == 'united states':
                full_name = place['full_name']
                if full_name:
                    # Attempt to extract a state name from the full_name.
                    match = STATE_RE.search(full_name)
                    if match:
                        state = match.group(1).lower()
                        name['state'] = US_STATE_ABBREVIATIONS.get(state)
                else:
                    warnings.warn('Tweet has Place with no city full name')
        elif place_type == 'admin':
            name['state'] = place['name']
        elif place_type == 'country':
            pass
        else:
            warnings.warn('Tweet has unknown place type "%s"' % place_type)
            return None

        location = self._find_by_name(**name)
        if location:
            return (False, location)
        
        # try without city
        name['city'] = ''
        location = self._find_by_name(**name)
        if location:
            return (False, location)

        # try without city and state
        name['state'] = ''
        location = self._find_by_name(**name)
        if location:
            return (False, location)
        # breakpoint()
        if apiv2:
            # NOTE: In APIv2, places don't have an url anymore
            location = Location(
                id=next(self._unknown_ids),twitter_id=place['id'],
                **name)
        else:
            location = Location(
                id=next(self._unknown_ids),
                twitter_url=place['url'], twitter_id=place['id'],
                **name)

        # TODO: don't need this anymore. Test to make sure no error
        if self.allow_unknown_locations:
            # Remember this location for future lookups.
            self.add_location(location)
            return (False, location)

        # TODO: get rid of this
        if self.resolve_to_known_ancestor:
            ancestor = location
            while True:
                ancestor = ancestor.parent()
                if ancestor == EARTH:
                    break
                known_ancestor = self._find_by_location(ancestor)
                if known_ancestor:
                    return (True, known_ancestor)
        return None

        # TODO: try to find state or country if can't find city
