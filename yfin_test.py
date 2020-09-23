#!/usr/bin/env python
"""
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen

import json

api_key = '29019bd9e98c586fc5d20a41467d7052'

def get_jsonparsed_data(url):
    
    Receive the content of ``url``, parse it as JSON and return the object.

    Parameters
    ----------
    url : str

    Returns
    -------
    dict

    response = urlopen(url)
    data = response.read().decode("utf-8")
    return json.loads(data)

url = ("https://financialmodelingprep.com/api/v3/stock/losers?apikey={}".format(api_key))
print(get_jsonparsed_data(url))

#from yahoo_fin import stock_info as si

# get worst performers
#losers_df = si.get_day_losers()
#losers_df.to_csv('losers.csv')

#print ('losers.csv complete!')

"""
import requests

url = "https://app.quotemedia.com/auth/p/authenticate/v0/"

querystring = {
"wmId":"501",
"username":"jeongji418",
"password":"!@Kiguj13571141@!"
}

headers = "Content-Type: application/json"

r = requests.post(url, headers=headers, data=querystring)

print(r.text)
