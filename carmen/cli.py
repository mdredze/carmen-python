#!/usr/bin/env python

import argparse
import json
import sys

from .location import Location, LocationEncoder
from .resolver import LocationResolver
from .resolvers import *


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resolve tweet locations.')
    parser.add_argument('--ignore-geocodes',
        action='store_false', dest='use_geocodes',
        help="don't use tweet geographic coordinates")
    parser.add_argument('--ignore-places',
        action='store_false', dest='use_places',
        help="don't use tweet place fields")
    parser.add_argument('--ignore-user-profile',
        action='store_false', dest='use_user_profile',
        help="don't use location field of tweet author's profile")
    parser.add_argument('--disallow-unknown-locations',
        action='store_false', dest='allow_unknown_locations',
        help='disallow resolution to unknown locations')
    parser.add_argument('--resolve-to-known-ancestor',
        action='store_true',
        help='attempt to find a known ancestor for unknown locations '
             'when --disallow-unknown-locations is specified')
    parser.add_argument('--max-distance',
        type=float, metavar='MILES', default=25,
        help='maximum distance to look from the position specified by '
             'a geographic coordinate pair for matching locations')
    parser.add_argument('locations_file', metavar='locations_path',
        type=argparse.FileType('r'),
        help='file containing location database')
    parser.add_argument('input_file', metavar='input_path',
        nargs='?', type=argparse.FileType('r'), default=sys.stdin,
        help='file containing tweets to locate with geolocation field '
             '(defaults to standard input)')
    parser.add_argument('output_file', metavar='output_path',
        nargs='?', type=argparse.FileType('w'), default=sys.stdout,
        help='file to write geolocated tweets to (defaults to standard '
             'output)')
    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    resolvers = []
    if args.use_places:
        resolvers.append(PlaceResolver(
            args.allow_unknown_locations, args.resolve_to_known_ancestor))
    if args.use_geocodes:
        resolvers.append(GeocodeResolver(args.max_distance))
    if args.use_user_profile:
        resolvers.append(ProfileResolver())
    resolver = LocationResolver(resolvers)
    for line in args.locations_file:
        resolver.add_location(Location(**json.loads(line)))
    resolved_tweets = total_tweets = 0
    for line in args.input_file:
        tweet = json.loads(line)
        location = resolver.resolve_tweet(tweet)
        if location:
            tweet['location'] = location
            resolved_tweets += 1
        print >> args.output_file, json.dumps(tweet, cls=LocationEncoder)
        total_tweets += 1
    print >> sys.stderr, 'Resolved locations for %d of %d tweets.' % (
        resolved_tweets, total_tweets)
