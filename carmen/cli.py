#!/usr/bin/env python
from __future__ import print_function

import argparse
import collections
import gzip
import json
import jsonlines
import sys
import warnings


from . import get_resolver
from .location import Location, LocationEncoder


def parse_args():
    parser = argparse.ArgumentParser(
        description='Resolve tweet locations.',
        epilog='Paths ending in ".gz" are treated as gzipped files.')
    parser.add_argument('-s', '--statistics',
        action='store_true',
        help='show summary statistics')
    parser.add_argument('--order',
        metavar='RESOLVERS',
        help='preferred resolver order (comma-separated)')
    parser.add_argument('--options',
        default='{}',
        help='JSON dictionary of resolver options')
    parser.add_argument('--locations',
        metavar='PATH', dest='location_file',
        help='path to alternative location database')
    parser.add_argument('input_file', metavar='input_path',
        nargs='?', default=sys.stdin,
        help='file containing tweets to locate with geolocation field '
             '(defaults to standard input)')
    parser.add_argument('output_file', metavar='output_path',
        nargs='?', default=sys.stdout,
        help='file to write geolocated tweets to (defaults to standard '
             'output)')
    parser.add_argument('--debug', '-d', 
        action='store_true',
        help='turn on debug (verbose) mode')
    return parser.parse_args()


def open_file(filename, mode):
    # Check for stdin/stdout case
    if "_io.TextIOWrapper" in str(filename.__class__):
        return filename
    # GZIP case
    if filename.endswith('.gz'):
        return gzip.open(filename, mode)
    else:
        return open(filename, mode)


def main():
    args = parse_args()
    warnings.simplefilter('always')
    resolver_kwargs = {}
    if args.order is not None:
        resolver_kwargs['order'] = args.order.split(',')
    if args.options is not None:
        resolver_kwargs['options'] = json.loads(args.options)
    resolver = get_resolver(**resolver_kwargs)
    
    resolver.load_locations(location_file=args.location_file)
    # Variables for statistics.
    city_found = county_found = state_found = country_found = 0
    has_place = has_coordinates = has_geo = has_profile_location = 0
    resolution_method_counts = collections.defaultdict(int)
    skipped_tweets = resolved_tweets = total_tweets = 0

    fi = open_file(args.input_file, "rb")
    fo = open_file(args.output_file, 'wb')
    with jsonlines.Writer(fo) as writer:
        with jsonlines.Reader(fi) as reader:
            for i, tweet in enumerate(reader.iter(skip_invalid=True, skip_empty=True)):
                total_tweets += 1
                if args.debug:
                    # DEBUGGING
                    print('-'*70)
                    print(json.dumps(tweet, indent=4, sort_keys=True))
                    print(type(tweet))
                    data = tweet.get("data")
                    includes = tweet.get("includes")
                    geo = tweet.get("data", {}).get("geo")
                    print("\ndata")
                    print(data)
                    print("\nincludes")
                    print(includes)
                    print("\ngeo")
                    print(geo)
                    # break
                    # END DEBUGGING

                # Show warnings from the input file, not the Python source code.
                def showwarning(message, category, filename, lineno, file=sys.stderr, line=None):
                    sys.stderr.write(
                        warnings.formatwarning(message, category, args.input_file, i+1, line='')
                    )
                warnings.showwarning = showwarning
                # Skip deleted and status_withheld tweets
                if "delete" in tweet or "status_withheld" in tweet:
                    skipped_tweets += 1
                    continue

                # TODO: in APIv2, statistics can't work like before since fields are different.
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
                resolution = resolver.resolve_tweet(tweet)
                if resolution:
                    location = resolution[1]
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
                try:
                    json_output = json.dumps(tweet, cls=LocationEncoder).encode()
                    writer.write(json_output)
                except TypeError as err:
                    json_output = json.dumps(tweet, cls=LocationEncoder)
                    writer.write(json_output)
    fi.close()
    fo.close()

    if args.statistics:
        # TODO: change the statistics to correspond with the new API v2
        print('Skipped %d tweets.' % skipped_tweets, file=sys.stderr)
        print('Tweets with "place" key: %d; '
                                       '"coordinates" key: %d; '
                                       '"geo" key: %d.' % (
                                        has_place, has_coordinates, has_geo), file=sys.stderr)
        print('Resolved %d tweets to a city, '
                                       '%d to a county, %d to a state, '
                                       'and %d to a country.' % (
                                city_found, county_found,
                                state_found, country_found), file=sys.stderr)
        print('Tweet resolution methods: %s.' % (
            ', '.join('%d by %s' % (v, k)
                for (k, v) in resolution_method_counts.items())), file=sys.stderr)
    print('Resolved locations for %d of %d tweets.' % (
        resolved_tweets, total_tweets), file=sys.stderr)


if __name__ == '__main__':
    main()
