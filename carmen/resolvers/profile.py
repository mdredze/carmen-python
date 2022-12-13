"""Resolvers based on Twitter user profile data."""


import re
import warnings

from ..names import *
from ..resolver import AbstractResolver, register


STATE_RE = re.compile(r'.+,\s*(\w+)')
NORMALIZATION_RE = re.compile(r'\s+|\W')


def normalize(location_name, preserve_commas=False):
    """Normalize *location_name* by stripping punctuation and collapsing
    runs of whitespace, and return the normalized name."""
    def replace(match):
        if preserve_commas and ',' in match.group(0):
            return ','
        return ' '
    return NORMALIZATION_RE.sub(replace, location_name).strip().lower()


@register('profile')
class ProfileResolver(AbstractResolver):
    """A resolver that locates a tweet by matching the tweet author's
    profile location against known locations."""

    name = 'profile'

    def __init__(self):
        self.location_name_to_location = {}

    def add_location(self, location):
        aliases = list(location.aliases)
        aliases_already_added = set()
        for alias in aliases:
            if alias in aliases_already_added:
                continue
            # NOTE: temprarily supress warning
            # if alias in self.location_name_to_location:
            #     warnings.warn(
            #         "Duplicate location name '{0}' for {1} and {2}".format(alias, location, self.location_name_to_location[alias])
            #     )
            else:
                self.location_name_to_location[alias] = location
            # Additionally add a normalized version of the alias
            # stripped of punctuation, and with runs of whitespace
            # reduced to single spaces.
            normalized = normalize(alias)
            if normalized != alias and normalized not in aliases:
                aliases.append(normalized)
            aliases_already_added.add(alias)

    def resolve_tweet(self, tweet):
        import sys
        location_string = tweet.get('user', {}).get('location', '')
            
        if not location_string:
            return None

        normalized = normalize(location_string)

        if normalized in self.location_name_to_location:
            return (False, self.location_name_to_location[normalized])
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
                return (False, self.location_name_to_location[location_name])
        return None
