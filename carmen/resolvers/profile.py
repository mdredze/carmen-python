# TODO:  Write docstring.


import re

from ..names import *


STATE_RE = re.compile(r'.+,\s*(\w+)')
NORMALIZATION_RE = re.compile(r'\s+|\W')


def normalize(location_name, preserve_commas=False):
    def replace(match):
        if preserve_commas and ',' in match.group(0):
            return ','
        return ' '
    return NORMALIZATION_RE.sub(replace, location_name).strip().lower()


class ProfileResolver(object):
    # TODO:  Write docstring.

    name = 'profile'

    def __init__(self):
        self.location_name_to_location = {}

    def add_location(self, location):
        aliases = list(location.aliases)
        aliases_already_added = set()
        for alias in aliases:
            if alias in aliases_already_added:
                continue
            if alias in self.location_name_to_location:
                # TODO:  Warn about duplicate location name.
                pass
            else:
                self.location_name_to_location[alias] = location
            # Additionally add a normalized version of the alias
            # stripped of punctuation, and with runs of whitespace
            # reduced to single spaces.
            normalized = normalize(alias)
            if normalized != alias:
                aliases.append(normalized)
            aliases_already_added.add(alias)

    def resolve_tweet(self, tweet):
        # TODO:  Write docstring.
        location_string = tweet.get('user', {}).get('location', '')
        if not location_string:
            return None
        normalized = normalize(location_string)
        if normalized in self.location_name_to_location:
            return (8, self.location_name_to_location[normalized])
        # Try again with commas.
        normalized = normalize(location_string, preserve_commas=True)
        match = STATE_RE.search(normalized)
        if match:
            after_comma = match.group(1)
            location_name = None
            if after_comma in US_STATES or after_comma in COUNTRIES:
                location_name = after_comma
            elif after_comma in US_STATE_ABBREVIATIONS:
                location_name = US_STATE_ABBREVIATIONS[after_comma]
            elif after_comma in COUNTRY_CODES:
                location_name = COUNTRY_CODES[after_comma]
            if location_name in self.location_name_to_location:
                return (8, self.location_name_to_location[location_name])
        return None
