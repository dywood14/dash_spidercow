import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup            # HTML data structure
from urllib.request import urlopen        # Web client
from itertools import chain
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import dateparser
import time
from newspaper import Article

from multiprocessing import Pool
import na
from config import *
from timesetter import *


ticker = 'TSLA'
ticker = ticker.lower()
#exchange = 'xnas'
news_interval = 5

news={
  'yfnews': [],
  'bcnews': [],
  'msnews': []
}
r = list(news.keys())

# Beautifulsoup load
try:
  yahoo_url = r'https://finance.yahoo.com/quote/' + ticker
  yahoo_res = requests.get(yahoo_url)   # 'Yahoo Finance (Web)'
  yahoo_html = yahoo_res.text
  soup = BeautifulSoup(yahoo_html, "html.parser")

except requests.exceptions.ConnectionError:
  requests.status_code = "Connection refused"

# Pulling exchange info from Yahoo page
exchange_long = (soup.select('div.Mt\(15px\) > div.D\(ib\).Mt\(-5px\).Mend\(20px\).Maw\(56\%\)--tab768.Maw\(52\%\).Ov\(h\).smartphone_Maw\(85\%\).smartphone_Mend\(0px\) > div.C\(\$tertiaryColor\).Fz\(12px\) > span'))
exchange_long = exchange_long[0].text
exchange = exchange_long.split(' - ')[0]

if 'NASDAQ' in exchange.upper(): exchange = 'xnas'
if 'NYSE -' in exchange_long.upper(): exchange = 'xnys'
if 'AMEX' in exchange.upper(): exchange = 'xase'
if 'NYSE AMERICAN -' in exchange_long.upper(): exchange = 'xase'
if 'OTC' in exchange.upper(): exchange = 'pinx'
if 'ARCA' in exchange.upper(): exchange = 'arcx'

company=None
try:
  company = soup.select('div.Mt\(15px\) > div.D\(ib\).Mt\(-5px\).Mend\(20px\).Maw\(56\%\)--tab768.Maw\(52\%\).Ov\(h\).smartphone_Maw\(85\%\).smartphone_Mend\(0px\) > div.D\(ib\) > h1')
  company = company[0].text
  if '-' in company:
    try: company = company.split(' - ')[1]
    except: pass

  if '(' in company:
    try: company = company.split(' (')[0]
    except: pass

except: pass

url = [
  ['Yahoo Finance (RSS)', "http://feeds.finance.yahoo.com/rss/2.0/headline?s={}&region=US&lang=en-US".format(ticker)],
  ['Yahoo Finance (Web)', 'https://finance.yahoo.com/quote/{}'.format(ticker)],
  ['BigCharts', "https://bigcharts.marketwatch.com/quickchart/quickchart.asp?symb={}&insttype=Stock&freq=1&show=&time=4".format(ticker)],
  ['MorningStar', "https://www.morningstar.com/stocks/{}/{}/news".format(exchange, ticker.lower())],
]


def html_unescape(s):
  html_unescape_table = {
  ">": "&gt;",
  "<": "&lt;",
  "'": "&apos;",
  "'": "&#39;",
  '"': "&quot;",
  "&": "&amp;",}

  for item in html_unescape_table:
    s = s.replace(html_unescape_table[item], item)

  return s

# finding substring between 'start' and 'end'
def find_substring(string, start, end):
    len_until_end_of_first_match = string.find(start) + len(start)
    after_start = string[len_until_end_of_first_match:]
    return string[string.find(start) + len(start):len_until_end_of_first_match + after_start.find(end)]

# Determine either the given time is within the specified 'news_interval' days
def time_filter(news_interval, dtg):
  today = datetime.today().astimezone(nyc)
  td = (dateparser.parse(str(today)) - dateparser.parse(dtg))
  if td <= timedelta(days=news_interval):
    return True
  else:
    return False

def remove_dup_headlines(news, h_key1, h_key2):
  try:
    for i in range(len(news[h_key1])):
      h_key1_headline = news[h_key1][i][2]
      h_key1_headline_parsed = re.sub('[^A-Za-z0-9]+', ' ', h_key1_headline)  # removing special chrs
      h_key1_headline_wordslist = ' '.join(h_key1_headline_parsed)        # creating list sep by space

      for j in range(len(news[h_key2])):
        h_key2_headline = news[h_key2][j][2]
        h_key2_headline_parsed = re.sub('[^A-Za-z0-9]+', ' ', h_key2_headline)
        h_key2_headline_wordslist = ' '.join(h_key2_headline_parsed)

        list1 = h_key1_headline_wordslist
        list2 = h_key2_headline_wordslist

        if len(list1) != 0 and len(list2) != 0:
          # Finding the similarity percentage between the two sentences
          sim_percent = len(set(list1) & set(list2)) / float(len(set(list1) | set(list2))) * 100

          if sim_percent >= 90:
            del news[h_key2][j]
  except:
    pass

def get_full_article(url):
  #Get the article
  article = Article(url)

  # Do some NLP
  article.download()      # Downloads the link’s HTML content
  article.parse()      # Parse the article
  return (article.text)

def morningstar_news():
  # Morningstar News (in lieu of E-Trade News)
	try:
	  res = requests.get(url[3][1])
	  #res.encoding = "utf-8"
	  rhtml = res.text
	  msoup = BeautifulSoup(rhtml, "html.parser")

	except requests.exceptions.ConnectionError:
	  requests.status_code = "Connection refused"

	s1='section.stock__news'
	tag = msoup.select(s1)
	for n in tag:
	  tag2 = n.select('article')
	  for t in tag2:
	    dtg = t.select('div.mdc-news-module__metadata > time')[0]
	    dtg = find_substring(str(dtg), 'datetime="', '">')
	    dtg = dateparser.parse(dtg).astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M (%Z)')
	      
	    if time_filter(news_interval, dtg) == True:
	      dtg = dateparser.parse(dtg).strftime("%d %b %H:%M")
	      headline = t.select('a')[1]
	      link = 'https://www.morningstar.com/{}'.format(find_substring(str(headline), 'href="/', '" tabindex='))
	      headline = headline.text.lstrip().rstrip()
	        
	      news['msnews'].append([url[3][0], dtg, headline, link])

def yahoo_news():
  # Yahoo Finance News from RSS Feed
  feed = feedparser.parse(url[0][1])

  if feed:
    for entry in feed.entries:
      dtg = dateparser.parse(entry.published).astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M (%Z)')
      if time_filter(news_interval, dtg) == True:
        dtg = dateparser.parse(dtg).strftime("%d %b %H:%M")
        headline = html_unescape(entry.title)
        link = entry.link   

        news['yfnews'].append([url[0][0], dtg, headline, link])



  soup1 = soup.find("div", {"id": "quoteNewsStream-0-Stream"})
  soup2 = soup1.find("ul", {"class": "My(0) Ov(h) P(0) Wow(bw)"})
  
  if soup2:    
    for n in soup2:
      headline_raw=n.find('a')
      headline = headline_raw.text
      #body=n.find('p').text # to review
      link = ("https://finance.yahoo.com" + headline_raw.get('href'))

      dtg_html=requests.get(link).text 
      dtg_soup=BeautifulSoup(dtg_html, "html.parser")
      d=dtg_soup.find("time").text
      dtg=dateparser.parse(d).astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M (%Z)')

      # If dtg is within the news_interval time, then...
      if time_filter(news_interval, dtg) == True:
        dtg = dateparser.parse(dtg).strftime("%d %b %H:%M")
        
        news['yfnews'].append([url[1][0], dtg, headline, link])


def main():
  start_time = time.time()
  yahoo_news()
  morningstar_news()
  remove_dup_headlines(news, 'yfnews', 'msnews')

  # filters news articles based on keywords on 'blacklist.csv'
  if os.name == 'nt':
    csv_path = os.getcwd()+'\\data\\blacklist.csv'
  
  else:
    csv_path = os.path.join('data/blacklist.csv')
  
  rf = pd.read_csv(csv_path, encoding='utf-8')
  rf = list(rf[rf.columns[0]])
  df = pd.DataFrame()
  for i in range(len(r)): df = df.append(news[r[i]])
  if not df.empty:
    df.columns = ['Source', 'Time', 'Headlines', 'Links']
    df = df[~df["Headlines"].str.lower().str.contains('|'.join(rf))]      # deleting all headlines containing blacklist words
    df = df[~df["Headlines"].duplicated(keep='first')]                    # deleting duplicate headlines
    #df = df[!is.na(df$Links), ]
    df.index = pd.RangeIndex(len(df.index))

    headlines = df['Headlines'].tolist()
    links = df['Links'].tolist()

  article_texts = []
  analysis = []

  pool = Pool(processes=6)
  article_texts=(pool.map(get_full_article, links))

  # Stripping the company introduction in the article
  new_article_texts = []
  for text in article_texts:
    try:
      after_about = text.split('About ')[1]

      # comparing only the first two words
      if str(company[:2]).lower() or ticker.lower() in str(after_about.split()[:2]).lower():
        text = text.split('About ')[0]
        new_article_texts.append(text)

    except: pass

  if len(new_article_texts) > 0:
    article_texts = new_article_texts

  for i in range(len(links)):
    analysis.append(list(chain.from_iterable(pool.starmap(na.news_analyzer, [(headlines[i], article_texts[i], links[i])]))))
  pool.terminate()
  pool.join()

  print (analysis)
  df['Analysis'] = pd.Series(analysis).values

  print("--- %s seconds ---" % (time.time() - start_time))
  print ('')
  pd.set_option('display.max_colwidth', -1)                          # For dev purpuoses
  print (df)

  #pd.set_option('display.max_colwidth', -1)                          # For dev purpuoses

  return (df)

if __name__ == '__main__':
  main()
