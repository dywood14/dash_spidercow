#!/usr/bin/python
import os, sys
from datetime import datetime, timedelta
from pytz import timezone
import itertools
from dateutil import parser


# Get when the market opens or opened today
nyc = timezone('America/New_York')
today = datetime.today().astimezone(nyc)
today_date = today.date()
today_str = datetime.today().astimezone(nyc).strftime('%Y-%m-%d')
  
tz_noon = today.replace(hour=12, minute=0, second=0, microsecond=0)

# Time Blocks (Start Time)
tz_st=[
  today.replace(hour=9, minute=30, second=1, microsecond=0),  #0
  today.replace(hour=10, minute=0, second=1, microsecond=0),  #1
  today.replace(hour=10, minute=45, second=1, microsecond=0), #2
  today.replace(hour=11, minute=30, second=1, microsecond=0), #3
  today.replace(hour=12, minute=15, second=1, microsecond=0), #4
  today.replace(hour=13, minute=0, second=1, microsecond=0),  #5
  today.replace(hour=13, minute=45, second=1, microsecond=0), #6
]

# Time Blocks (End Time)
tz_ed=[
  today.replace(hour=10, minute=0, second=0, microsecond=0),  #0
  today.replace(hour=10, minute=45, second=0, microsecond=0), #1
  today.replace(hour=11, minute=30, second=0, microsecond=0), #2
  today.replace(hour=12, minute=15, second=0, microsecond=0), #3 
  today.replace(hour=13, minute=0, second=0, microsecond=0),  #4
  today.replace(hour=13, minute=45, second=0, microsecond=0), #5
  today.replace(hour=14, minute=30, second=0, microsecond=0)  #6
]

jumpwords = set(parser.parserinfo.JUMP)
keywords = set(kw.lower() for kw in itertools.chain(
    parser.parserinfo.UTCZONE,
    parser.parserinfo.PERTAIN,
    (x for s in parser.parserinfo.WEEKDAYS for x in s),
    (x for s in parser.parserinfo.MONTHS for x in s),
    (x for s in parser.parserinfo.HMS for x in s),
    (x for s in parser.parserinfo.AMPM for x in s),
))

def parse_multiple_dates(s):
    def is_valid_kw(s):
        try:  # is it a number?
            float(s)
            return True
        except ValueError:
            return s.lower() in keywords

    def _split(s):
        kw_found = False
        tokens = parser._timelex.split(s)
        for i in range(len(tokens)):
            if tokens[i] in jumpwords:
                continue 
            if not kw_found and is_valid_kw(tokens[i]):
                kw_found = True
                start = i
            elif kw_found and not is_valid_kw(tokens[i]):
                kw_found = False
                yield "".join(tokens[start:i])
        # handle date at end of input str
        if kw_found:
            yield "".join(tokens[start:])

    return [parser.parse(x) for x in _split(s)]

if __name__ == '__main__':
  s = sys.argv[1]
  dtg=parse_multiple_dates(s)
