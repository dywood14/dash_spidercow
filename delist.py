#!/usr/bin/python
import os, sys, json, re
import csv
import base64
import requests
from bs4 import BeautifulSoup
import pandas as pd

from config import *
from timesetter import *

def update_delist():
	nd_url = r'https://listingcenter.nasdaq.com/noncompliantcompanylist.aspx'
	
	try:
		nd_res = requests.get(nd_url)
		nd_html = nd_res.text
		soup = BeautifulSoup(nd_html, "html.parser")
	except requests.exceptions.ConnectionError:
		requests.status_code = "Connection refused"

	## Pulling list from NASDAQ
	soup = soup.select('table.rgMasterTable')

	lst = []
	list_names = []
	list_from=[]
	a_split=[]

	#### Retrieving NASDAQ Delisted Stocks
	for s in soup:
		soup = s.select('p')
		for i in range(0, len(soup)):
			lst.append(soup[i].text.split(',')[0])

	for i in range(0, len(lst)):
		n = len(lst[i].split(' '))
		list_from.append('NASDAQ')

		a=lst[i].strip()
		a = re.sub(r"\s+$", "", a, flags=re.UNICODE)	# removing white spaces at the end
		a = " ".join(a.split())
		list_names.append(a)

		a_split=a.replace(' ', '+')

	today = datetime.today().astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M:%S (%Z)')
	file = os.getcwd()+'\\data\\delist.csv'

	f = open(file, "w+")
	f.close()

	d = {today: list_names, 'Delisted From': list_from}
	df = pd.DataFrame(data=d)
	df.to_csv(file, index=False)

if __name__ == '__main__':
	update_delist()
