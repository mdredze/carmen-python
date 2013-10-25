"""Main location resolution classes and methods."""


from abc import ABCMeta, abstractmethod

from .location import Location, EARTH


class AbstractResolver(object):
    """An abstract base class for *resolvers* that match tweets to known
    locations."""
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_location(self, location):
        """Add *location* to this resolver's set of known locations.
        Resolvers may create lookup tables or other caches depending on
        how they resolve individual tweets."""
        pass

    @abstractmethod
    def resolve_tweet(self, tweet):
        """Find the best known location for the given *tweet*, which
        is provided as a deserialized JSON object, and return a tuple
        containing a confidence value and the location object.  If no
        suitable locations are found, None may be returned."""
        pass


class Resolver(AbstractResolver):
    """A "supervising" resolver that attempts to resolve a tweet's
    location by using multiple child resolvers and returning the
    resolution with the highest priority."""

    def __init__(self, resolvers=[]):
        self.resolvers = resolvers
        self.add_location(EARTH)

    def add_location(self, location):
        # Inform our child resolvers of this location.
        for resolver_ in self.resolvers:
            resolver_.add_location(location)

    def resolve_tweet(self, tweet):
        best_resolution = (-1, None)
        best_resolver_name = None
        for resolver_ in self.resolvers:
            resolution = resolver_.resolve_tweet(tweet)
            if resolution > best_resolution:
                best_resolution = resolution
                best_resolver_name = resolver_.name
        location = best_resolution[1]
        if location:
            location.resolution_method = best_resolver_name
        return location
