"""
Queries the Twitter API
"""

import argparse
import twitter
import multiprocessing as mp


# Set up Twitter authentication
api = twitter.Api(consumer_key="48MzKz7Dwu23iNgsNe76W2tnc",
                  consumer_secret="mBDT7qG3zhhy4L5YqewAnpVFfQknR3q962oy9yhtdnJYPMvRaI",
                  access_token_key="16019396-5z1EWfXuWGo7JipkOmKDiRYSUYvGPitNHsIx64UfV",
                  access_token_secret="vAp0kpczzohmk9iK9fkKtmSbF7VMQuJesTZ7Yo7KJWHKV")
global args


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("status-ids")
    parser.add_argument("output-file")
    return parser.parse_args()


def get_user(user_id):
    user = api.GetUser(user_id, return_json=True)
    with open(args.output_file, "a+") as f:
        f.write(user)
    return


def get_tweet(status_id):
    status = api.GetStatus(status_id)
    with open(args.output_file, "a+") as f:
        f.write(status)
    return


if __name__ == "__main__":
    # Get arguments
    args = parse_arguments()

    # Read in file with tweet/status ids
    with open(args.status_ids) as f:
        status_ids = [i.strip() for i in f.readlines()]

    with mp.Pool() as p:
        p.map(get_tweet, status_ids)
