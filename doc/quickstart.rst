Quick start
===========

The easiest way to install Carmen is with the built-in setup script::

    $ python setup.py install

This installs the ``carmen`` package and associated data files
into the active Python environment.


Using the frontend
``````````````````

Carmen comes with a simple frontend to demonstrate its capabilities.
Once Carmen is installed, you can run the frontend with::

    $ python -m carmen.cli [options] [input_file] [output_file]

The input file should contain one JSON-serialized tweet per line,
as returned by the Twitter API.
If it is not specified, standard input is assumed.
Carmen will output these tweets as JSON,
with location information added in the ``location`` key,
to the given output file, or standard output if none is specified.
Both the input and output filenames may end in ``.gz``
to specify that Carmen should treat the files as gzipped text.

If the ``-s`` (``--statistics``) option is passed,
Carmen will print summary statistics when it finishes processing,
detailing the number of tweets that were successfully resolved,
and the resolution methods that were used to do so.
For information on other options, use the ``-h`` (``--help``) option.


Using the Python API
````````````````````

Python applications can use the Carmen API
to directly retrieve location information for tweets::

    import json
    import carmen

    tweet = json.loads(tweet_json)
    resolver = carmen.get_resolver()
    resolver.load_locations()
    location = resolver.resolve_tweet(tweet)

The resolver's :py:meth:`.resolve_tweet` method is the central API call:

.. automethod:: carmen.resolver.AbstractResolver.resolve_tweet

.. class:: carmen.Location

   Contains information about a location and how it was identified.

   .. attribute:: latitude
                  longitude

      The coordinates of this location's geographic center.

   .. attribute:: country
                  state
                  county
                  city

      Basic location information.  A value of ``None`` for a particular
      field indicates that it does not apply for that specific location.

   .. attribute:: aliases

      An iterable containing alternative names for this location.

   .. attribute:: resolution_method

      The name of the method used to resolve this location's data from
      the tweet that originally contained it.

   .. attribute:: known

      True if this location appears in the database, False otherwise.

   .. attribute:: id

      For known locations, the database ID.  For other locations, a
      unique ID is arbitrarily assigned for each run.

   .. attribute:: twitter_url
                  twitter_id

      For locations with information based solely on Twitter Place
      information, the URL and ID of the associated Place.

The resolver's default location database can be added to or overridden
using its :py:meth:`.add_location` and :py:meth:`.load_locations` methods:

.. automethod:: carmen.resolver.AbstractResolver.add_location
.. automethod:: carmen.resolver.AbstractResolver.load_locations

Finally, the behavior of the resolver itself can be customized:

.. autofunction:: carmen.get_resolver
