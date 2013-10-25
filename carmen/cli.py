#!/usr/bin/env python

import argparse
import collections
import gzip
import json
import sys
import warnings

from .location import Location, LocationEncoder
from .resolver import Resolver
from .resolvers import *


class MaybeGzipFileType(argparse.FileType):
    """A factory for creating file object types.  Filenames that end in
    ".gz" are treated as if they were gzipped; otherwise, this class
    behaves the same as argparse.FileType."""

    def __call__(self, filename):
        f = super(MaybeGzipFileType, self).__call__(filename)
        if filename.endswith('.gz'):
            return gzip.GzipFile(fileobj=f)
        return f


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resolve tweet locations.',
        epilog='Paths ending in ".gz" are treated as gzipped files.')
    parser.add_argument('-s', '--statistics',
        action='store_true',
        help='show summary statistics')
    parser.add_argument('--ignore-geocodes',
        action='store_false', dest='use_geocodes',
        help="don't use tweet geographic coordinates")
    parser.add_argument('--ignore-places',
        action='store_false', dest='use_places',
        help="don't use tweet place fields")
    parser.add_argument('--ignore-user-profile',
        action='store_false', dest='use_user_profile',
        help="don't use location field of tweet author's profile")
    parser.add_argument('--allow-unknown-locations',
        action='store_true',
        help='allow resolution to unknown locations')
    parser.add_argument('--resolve-to-known-ancestor',
        action='store_true',
        help='attempt to find a known ancestor for unknown locations '
             'when --disallow-unknown-locations is specified')
    parser.add_argument('--max-distance',
        type=float, metavar='MILES', default=25,
        help='maximum distance to look from the position specified by '
             'a geographic coordinate pair for matching locations')
    parser.add_argument('locations_file', metavar='locations_path',
        type=MaybeGzipFileType('r'),
        help='file containing location database')
    parser.add_argument('input_file', metavar='input_path',
        nargs='?', type=MaybeGzipFileType('r'), default=sys.stdin,
        help='file containing tweets to locate with geolocation field '
             '(defaults to standard input)')
    parser.add_argument('output_file', metavar='output_path',
        nargs='?', type=MaybeGzipFileType('w'), default=sys.stdout,
        help='file to write geolocated tweets to (defaults to standard '
             'output)')
    return parser.parse_args()


def main():
    args = parse_args()
    warnings.simplefilter('always')
    resolvers = []
    if args.use_places:
        resolvers.append(PlaceResolver(
            args.allow_unknown_locations, args.resolve_to_known_ancestor))
    if args.use_geocodes:
        resolvers.append(GeocodeResolver(args.max_distance))
    if args.use_user_profile:
        resolvers.append(ProfileResolver())
    resolver = Resolver(resolvers)
    for i, location_line in enumerate(args.locations_file):
        def showwarning(message, category, filename, lineno,
                        file=sys.stderr, line=None):
            sys.stderr.write(warnings.formatwarning(
                message, category, args.locations_file.name, i+1,
                line=''))
        warnings.showwarning = showwarning
        resolver.add_location(
            Location(known=True, **json.loads(location_line)))
    # Variables for statistics.
    city_found = county_found = state_found = country_found = 0
    has_place = has_coordinates = has_geo = has_profile_location = 0
    resolution_method_counts = collections.defaultdict(int)
    skipped_tweets = resolved_tweets = total_tweets = 0
    for i, input_line in enumerate(args.input_file):
        # Show warnings from the input file, not the Python source code.
        def showwarning(message, category, filename, lineno,
                        file=sys.stderr, line=None):
            sys.stderr.write(warnings.formatwarning(
                message, category, args.input_file.name, i+1,
                line=''))
        warnings.showwarning = showwarning
        try:
            tweet = json.loads(input_line)
        except ValueError:
            warnings.warn('Invalid JSON object')
            skipped_tweets += 1
            continue
        # Collect statistics on the tweet.
        if tweet.get('place'):
            has_place += 1
        if tweet.get('coordinates'):
            has_coordinates += 1
        if tweet.get('geo'):
            has_geo += 1
        if tweet.get('user', {}).get('location', ''):
            has_profile_location += 1
        # Perform the actual resolution.
        location = resolver.resolve_tweet(tweet)
        if location:
            tweet['location'] = location
            # More statistics.
            resolution_method_counts[location.resolution_method] += 1
            if location.city:
                city_found += 1
            elif location.county:
                county_found += 1
            elif location.state:
                state_found += 1
            elif location.country:
                country_found += 1
            resolved_tweets += 1
        print >> args.output_file, json.dumps(tweet, cls=LocationEncoder)
        total_tweets += 1
    if args.statistics:
        print >> sys.stderr, 'Skipped %d tweets.' % skipped_tweets
        print >> sys.stderr, ('Tweets with "place" key: %d; '
                              '"coordinates" key: %d; '
                              '"geo" key: %d.' % (
                                has_place, has_coordinates, has_geo))
        print >> sys.stderr, ('Resolved %d tweets to a city, '
                              '%d to a county, %d to a state, '
                              'and %d to a country.' % (
                                city_found, county_found,
                                state_found, country_found))
        print >> sys.stderr, ('Tweet resolution methods: %s.' % (
            ', '.join('%d by %s' % (v, k)
                for (k, v) in resolution_method_counts.iteritems())))
    print >> sys.stderr, 'Resolved locations for %d of %d tweets.' % (
        resolved_tweets, total_tweets)


if __name__ == '__main__':
    main()
