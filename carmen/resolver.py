"""Main location resolution classes and methods."""


from abc import ABCMeta, abstractmethod
import json
import pkgutil

from .location import Location, EARTH

ABC = ABCMeta('ABC', (object,), {}) # compatible with Python 2 *and* 3 

class AbstractResolver(ABC):
    """An abstract base class for *resolvers* that match tweets to known
    locations."""
    location_id_to_location = {}
    @abstractmethod
    def add_location(self, location):
        """Add an individual :py:class:`.Location` object to this
        resolver's set of known locations."""
        pass

    def load_locations(self, location_file=None):
        """Load locations into this resolver from the given
        *location_file*, which should contain one JSON object per line
        representing a location.  If *location_file* is not specified,
        an internal location database is used."""
        if location_file is None:
            contents = pkgutil.get_data(__package__, 'data/locations.json')
            contents_string = contents.decode("ascii")
            locations = contents_string.split('\n')
        else:
            from .cli import open_file
            with open_file(location_file, 'rb') as input:
                locations = input.readlines()
        
        for location_string in locations:
            if location_string.strip():
                location = Location(known=True, **json.loads(location_string))
                self.location_id_to_location[location.id] = location
                self.add_location(location)

    @abstractmethod
    def resolve_tweet(self, tweet):
        """Find the best known location for the given *tweet*, which is
        provided as a deserialized JSON object, and return a tuple
        containing two elements: a boolean indicating whether the
        resolution is *provisional*, and a :py:class:`.Location` object.
        Provisional resolutions may be overridden by non-provisional
        resolutions returned by a less preferred resolver (i.e., one
        that comes later in the resolver order), and should be used when
        returning locations with low confidence, such as those found by
        using larger "backed-off" administrative units.

        If no suitable locations are found, ``None`` may be returned.
        """
        pass

    def get_location_by_id(self, location_id):
        return self.location_id_to_location[location_id]


class ResolverCollection(AbstractResolver):
    """A "supervising" resolver that attempts to resolve a tweet's
    location by using multiple child resolvers and returning the
    resolution with the highest priority."""

    def __init__(self, resolvers=None):
        self.resolvers = resolvers if resolvers else []
        self.add_location(EARTH)


    def add_location(self, location):
        # Inform our child resolvers of this location.
        for resolver_name, resolver in self.resolvers:
            resolver.add_location(location)


    def resolve_tweet(self, tweet):
        provisional_resolution = None
        for resolver_name, resolver in self.resolvers:
            resolution = resolver.resolve_tweet(tweet)
            if resolution is None:
                continue
            is_provisional, location = resolution
            location.resolution_method = resolver_name
            # If we only got a provisional resolution, hold on to it
            # as long as we don't already have a more preferred one,
            # and see if we get a non-provisional one later.
            if is_provisional:
                if provisional_resolution is None:
                    provisional_resolution = resolution
            else:
                return resolution
        # We didn't find any non-provisional resolutions; return the
        # best provisional resolution.  This will be None if we didn't
        # find any provisional resolutions, either.
        return provisional_resolution


### Resolver importation functions.
#
known_resolvers = {}


def register(name):
    """Return a decorator that registers the decorated class as a
    resolver with the given *name*."""
    def decorator(class_):
        if name in known_resolvers:
            raise ValueError('duplicate resolver name "%s"' % name)
        known_resolvers[name] = class_
    return decorator


def get_resolver(order=None, options=None, modules=None):
    """Return a location resolver.  The *order* argument, if given,
    should be a list of resolver names; results from resolvers named
    earlier in the list are preferred over later ones.  For a list of
    built-in resolver names, see :doc:`/resolvers`.  The *options*
    argument can be used to pass configuration options to individual
    resolvers, in the form of a dictionary mapping resolver names to
    keyword arguments::

        {'geocode': {'max_distance': 50}}

    The *modules* argument can be used to specify a list of additional
    modules to look for resolvers in.  See :doc:`/develop` for details.
    """
    if not known_resolvers:
        from . import resolvers as carmen_resolvers
        modules = [carmen_resolvers] + (modules or [])
        for module in modules:
            for loader, name, _ in pkgutil.iter_modules(module.__path__):
                full_name = module.__name__ + '.' + name
                loader.find_module(full_name).load_module(full_name)
    if order is None:
        order = ('place', 'geocode', 'profile')
    else:
        order = tuple(order)
    if options is None:
        options = {}
    resolvers = []
    for resolver_name in order:
        if resolver_name not in known_resolvers:
            raise ValueError('unknown resolver name "%s"' % resolver_name)
        resolvers.append((
            resolver_name,
            known_resolvers[resolver_name](**options.get(resolver_name, {}))))
    return ResolverCollection(resolvers)
