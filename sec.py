#!/usr/bin/python
import os, sys
import requests
import pandas as pd
from bs4 import BeautifulSoup
import dateparser
from timesetter import *

# Determine either the given time is within the specified 'news_interval' days
def sec_time_filter(news_interval, dtg):
  today = dateparser.parse(datetime.today().astimezone(nyc).strftime('%Y-%m-%d'))
  td = (today - dateparser.parse(dtg))
  if td <= timedelta(days=news_interval):
    return True
  else:
    return False

def update_sec(ticker, days_interval):
	endpoint = r"https://www.sec.gov/cgi-bin/browse-edgar"
	e = r"https://www.sec.gov/edgar/searchedgar/companysearch.html"
	#endpoint = r"https://www.sec.gov/cgi-bin/browse-edgar?CIK={}&owner=exclude&action=getcompany&Find=Search

	param_dict = {
	  'CIK': ticker,
	  'action': 'getcompany',
	  'owner': 'exclude',
	}

	response = requests.get(url = endpoint, params = param_dict)
	soup = BeautifulSoup(response.content, 'html.parser')

	doc_table = soup.find_all('table', class_='tableFile2')
	base_url_sec = r"https://www.sec.gov"

	master_list =[]
	first_index = 0
	last_index = 10

	# create and store data in the dictionary
	df_list=[]

	if len(doc_table) != 0:
		for row in doc_table[0].find_all('tr')[first_index:last_index]:
			cols = row.find_all('td')

			if len(cols) != 0:
				filing_date = cols[3].text.strip()
				dtg = dateparser.parse(filing_date).strftime('%Y-%m-%d')

				if sec_time_filter(days_interval, dtg) == True:

					filing_type = cols[0].text.strip()
					filing_numb = cols[4].text.strip()

					filing_doc_href = cols[1].find('a', {'href':True, 'id': 'documentsbutton'})
					filing_int_href = cols[1].find('a', {'href':True, 'id': 'interactiveDataBtn'})
					filing_num_href = cols[4].find('a')

					# grab the first href
					if filing_doc_href != None:
						filing_doc_link = base_url_sec + filing_doc_href['href']
					else:
						filing_doc_link = 'no link'

					# grab the second href
					if filing_int_href != None:
						filing_int_link = base_url_sec + filing_int_href['href']
					else:
						filing_int_link = 'no link'

					# grab the third href
					if filing_num_href != None:
						filing_num_link = base_url_sec + filing_num_href['href']
					else:
						filing_num_link = 'no link'

					# create and store data in the dictionary
					file_dict={
						'file_type': filing_type,
						'file_number': filing_numb,
						'file_date': dateparser.parse(filing_date).strftime("%d %b"),
						'links': {
							'documents': filing_doc_link,
							'interactive_data': filing_int_link,
							'filing_number': filing_num_link
						}
					}
					r = list(file_dict.keys())

					df_list.append([file_dict['file_type'], file_dict['file_date'], file_dict['links']['documents']])
	
		df = pd.DataFrame(df_list)
		if not df.empty:
			df.columns=['Type', 'Date', 'Links']

	else:
		df = pd.DataFrame()

	#pd.set_option('display.max_colwidth', -1)					# For dev purpuoses

	return (df)

def main():
  update_sec(ticker, days_interval)

if __name__ == '__main__':
  ticker = sys.argv[1]
  ticker = ticker.upper()
  days_interval = int(sys.argv[2])
  main()