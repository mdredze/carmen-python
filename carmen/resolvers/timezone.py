"""Resolvers based on Twitter tweet time-zone data."""

import sys
import re
import warnings

from ..names import *
from ..resolver import AbstractResolver, register


timezone_to_location_id = {
    'Abu Dhabi'    : 292969,   # county
    'Adelaide'     : 2078025,  # city
    'Alaska'       : 5558599,  # state
    'Almaty'       : 1526384,  # city
    'Amsterdam'    : 2759794,  # city
    'Arizona'      : 5551752,  # state
    'Athens'       : 264371,   # city
    'Auckland'     : 2193734,  # state
    'Baghdad'      : 98180,    # state
    'Baku'         : 587084,   # city
    'Bangkok'      : 1609348,  # state
    'Beijing'      : 2038349,  # state
    'Belgrade'     : 792680,   # city
    'Berlin'       : 2950157,  # state
    'Bogota'       : 3688689,  # city
    'Bratislava'   : 3060972,  # city
    'Brasilia'     : 3469058,  # city
    'Brisbane'     : 7839562,  # county
    'Brussels'     : 2800866,  # city
    'Bucharest'    : 683506,   # city
    'Budapest'     : 3054638,  # county
    'Buenos Aires' : 3427833,  # county
    'Cairo'        : 360630,   # city
    'Canberra'     : 2172517,  # city
    'Cape Verde'   : 3374766,  # country
    'Caracas'      : 3646738,  # city
    'Casablanca'   : 2553604,  # city
    'Chennai'      : 1264527,  # city
    'Chihuahua'    : 4014336,  # state
    'Copenhagen'   : 2618425,  # city
    'Darwin'       : 2073124,  # city
    'Dhaka'        : 1337179,  # state
    'Dublin'       : 2964574,  # city
    'Edinburgh'    : 2650225,  # city
    'Fiji'         : 2205272,  # country
    'Georgetown'   : 3378644,  # city
    'Greenland'    : 3425505,  # country
    'Guadalajara'  : 5433959,  # county
    'Hanoi'        : 1581130,  # city
    'Hawaii'       : 5855797,  # state
    'Hobart'       : 2163355,  # city
    'Hong Kong'    : 1819730,  # country
    'Indiana'      : 4921868,  # state
    'Islamabad'    : 1176615,  # city
    'Istanbul'     : 745042,   # county
    'Jakarta'      : 1642911,  # city
    'Jerusalem'    : 293198,   # state
    'Karachi'      : 1174872,  # city
    'Kolkata'      : 1275004,  # city
    'Kuala Lumpur' : 1733046,  # state
    'Kuwait'       : 285570,   # country
    'La Paz'       : 3911924,  # state
    'Lima'         : 3936451,  # county
    'Lisbon'       : 2267057,  # city
    'London'       : 2648110,  # county
    'Madrid'       : 3117732,  # county
    'Melbourne'    : 2158177,  # city
    'Mexico City'  : 3530597,  # city
    'Minsk'        : 625142,   # county
    'Monrovia'     : 5374175,  # city
    'Monterrey'    : 3995465,  # city
    'Moscow'       : 524894,   # county
    'Mumbai'       : 1275339,  # city
    'Muscat'       : 411740,   # state
    'Nairobi'      : 184745,   # city
    'Newfoundland' : 6354959,  # state
    'Paris'        : 2968815,  # county
    'Perth'        : 2063523,  # city
    'Prague'       : 3067696,  # city
    'Quito'        : 3652462,  # county
    'Riga'         : 456172,   # city
    'Riyadh'       : 108410,   # city
    'Rome'         : 3169070,  # city
    'Saskatchewan' : 6141242,  # state
    'Seoul'        : 1835847,  # state
    'Singapore'    : 1880251,  # country
    'Skopje'       : 785842,   # city
    'Sofia'        : 727012,   # county
    'Stockholm'    : 2673730,  # city
    'Sydney'       : 2147714,  # city
    'Tashkent'     : 1512569,  # city
    'Tbilisi'      : 611717,   # city
    'Tehran'       : 112931,   # city
    'Tokyo'        : 1850147,  # city
    'Vienna'       : 2761367,  # state
    'Vilnius'      : 593116,   # city
    'Warsaw'       : 756135,   # city
    'Wellington'   : 2179538,  # state
    'Yerevan'      : 616051,   # state
}


@register('timezone')
class TimezoneResolver(AbstractResolver):
    """
    A resolver that locates a tweet by using the tweet's time-zone to infer
    a location from a list of known locations.
    """

    name = 'timezone'

    def __init__(self):
        self.timezone_to_location = {}

    def add_location(self, location):
        pass

    def resolve_tweet(self, tweet):
        timezone = tweet.get('user', {}).get('time_zone')
        if not timezone:
            return None
        if timezone not in timezone_to_location_id:
            return None

        location_id = timezone_to_location_id[timezone]
        location = self.get_location_by_id(location_id)
        return (False, location)
        