"""Main location resolution classes and methods."""


from abc import ABCMeta, abstractmethod
import json
import pkgutil

from .location import Location, EARTH


class AbstractResolver(object):
    """An abstract base class for *resolvers* that match tweets to known
    locations."""
    __metaclass__ = ABCMeta

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
            locations = contents.split('\n')
        else:
            locations = location_file
        for location in locations:
            if location.strip():
                self.add_location(Location(known=True, **json.loads(location)))

    @abstractmethod
    def resolve_tweet(self, tweet):
        """Find the best known location for the given *tweet*, which
        is provided as a deserialized JSON object, and return a tuple
        containing a confidence value and a :py:class:`.Location`
        object.  If no suitable locations are found, ``None`` may be
        returned."""
        pass


class ResolverCollection(AbstractResolver):
    """A "supervising" resolver that attempts to resolve a tweet's
    location by using multiple child resolvers and returning the
    resolution with the highest priority."""

    def __init__(self, resolvers=None):
        self.resolvers = resolvers if resolvers else {}
        self.add_location(EARTH)

    def add_location(self, location):
        # Inform our child resolvers of this location.
        for resolver in self.resolvers.itervalues():
            resolver.add_location(location)

    def resolve_tweet(self, tweet):
        best_resolution = (-1, None)
        best_resolver_name = None
        for resolver_name, resolver in self.resolvers.iteritems():
            resolution = resolver.resolve_tweet(tweet)
            if resolution > best_resolution:
                best_resolution = resolution
                best_resolver_name = resolver_name
        location = best_resolution[1]
        if location:
            location.resolution_method = best_resolver_name
        return best_resolution


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


def get_resolver(include=None, exclude=None, options=None, modules=None):
    """Return an object implementing :py:class:`.AbstractResolver` whose
    :py:meth:`.resolve_tweet` method returns the best resolution found
    by any available resolver.  Only one of the *include* and *exclude*
    arguments may be given; they should be lists of resolver names.  If
    *include* is given, only the named resolvers are used; if *exclude*
    is given, all resolvers except for the ones named are used.  The
    *options* argument should be a dictionary mapping resolver names to
    keyword arguments; for instance::

        {'geocode': {'max_distance': 50}}

    The *modules* argument can be used to specify a list of additional
    modules to look for resolvers in.  See :doc:`/develop` for details.
    """
    if include and exclude:
        raise ValueError('cannot specify both include and exclude arguments')
    if not known_resolvers:
        from . import resolvers as carmen_resolvers
        modules = [carmen_resolvers] + (modules or [])
        for module in modules:
            for loader, name, _ in pkgutil.iter_modules(module.__path__):
                full_name = module.__name__ + '.' + name
                loader.find_module(name).load_module(full_name)
    if include:
        resolver_names = include
    else:
        resolver_names = set(known_resolvers.keys()).difference(exclude or [])
    if options is None:
        options = {}
    resolvers = {}
    for resolver_name in resolver_names:
        if resolver_name not in known_resolvers:
            raise ValueError('unknown resolver name "%s"' % resolver_name)
        resolvers[resolver_name] = \
            known_resolvers[resolver_name](**options.get(resolver_name, {}))
    return ResolverCollection(resolvers)
