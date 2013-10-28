Built-in resolvers
==================

By default, Carmen attempts to resolve tweet locations by three methods,
in the following order:

#.  Using the ``place`` resolver, which matches Twitter Places to known
    locations by name.
    This resolver takes two options:

    *   *allow_unknown_locations* determines whether unknown Places are
        converted to locations that may be returned from resolution.
        By default, this option is False.
    *   *resolve_to_known_ancestor* determines whether tweets with
        unknown Places are resolved to the nearest known ancestor
        location containing that Place.
        For example, an unknown city may be resolved to a known state-
        or provincial-level location.
        Such a backed-off location, unlike others returned from this
        resolver, may be superseded by more confident estimates from
        other resolvers.
        This option is only effective if *allow_unknown_locations* is
        False, and itself defaults to False.

#.  Using the ``geocode`` resolver, which finds the known location
    nearest the tweet's geographic coordinates.
    This resolver takes a single option, *max_distance*,
    which specifies the maximum distance away from the coordinates,
    in miles, that the resolver will look for matching locations.

#.  Using the ``profile`` resolver, which matches the "location" fields
    of tweet authors' user profiles to known locations by name.
    This resolver takes no options.

The :py:attr:`.resolution_method` attribute of each :py:class:`.Location`
object, and the corresponding ``resolution_method`` key in the resulting
JSON output, contain a string specifying the name of the resolver used
to determine a tweet's location.
