# TODO:  Write docstring.


from .location import Location, EARTH


class LocationResolver(object):
    # TODO:  Write docstring.

    def __init__(self, resolvers=[]):
        self.resolvers = resolvers
        self.add_location(EARTH)

    def add_location(self, location):
        # TODO:  Write docstring.
        # Inform our child resolvers of this location.
        for resolver_ in self.resolvers:
            resolver_.add_location(location)

    def resolve_tweet(self, tweet):
        # TODO:  Write docstring.
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
