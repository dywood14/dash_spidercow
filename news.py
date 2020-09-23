#!/usr/bin/python
import os, sys, csv, re
import html
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup            # HTML data structure
from urllib.request import urlopen        # Web client
import feedparser
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import dateparser
import numpy as np
from collections import OrderedDict
import heapq
from newspaper import Article
from multiprocessing import Pool

from config import *
from timesetter import *
import na


html_unescape_table = {
  ">": "&gt;",
  "<": "&lt;",
  "'": "&apos;",
  "'": "&#39;",
  '"': "&quot;",
  "&": "&amp;",
}

def html_unescape(s):
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

# Collecting News
def update_news(ticker, news_interval):
  articles_list=[]
  news={
  'yfnews': [],
  'bcnews': [],
  'msnews': []
  }
  r = list(news.keys())

  # Beautifulsoup load

  yahoo_url = r'https://finance.yahoo.com/quote/' + ticker
  try:
    yahoo_res = requests.get(yahoo_url)
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
    ['Yahoo Finance', "http://finance.yahoo.com/rss/headline?s={}".format(ticker)],
    ['BigCharts', "https://bigcharts.marketwatch.com/quickchart/quickchart.asp?symb={}&insttype=Stock&freq=1&show=&time=4".format(ticker)],
    ['MorningStar', "https://www.morningstar.com/stocks/{}/{}/news".format(exchange, ticker.lower())],
  ]

# Yahoo Finance News from RSS Feed

  feed = feedparser.parse(url[0][1])

  if feed:
    for entry in feed.entries:
      dtg = dateparser.parse(entry.published).astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M (%Z)')
      if time_filter(news_interval, dtg) == True:
        dtg = dateparser.parse(dtg).strftime("%d %b %H:%M")
        headline = html_unescape(entry.title)
        link = entry.link
        #article_text = get_full_article(link)
        pool = Pool(processes=4)
        article_text=(pool.map(get_full_article, link))
        pool.terminate()
        pool.join()
        
        # Stripping the company introduction in the article
        try:
          after_about = article_text.split('About ')[1]

          # comparing only the first two words
          if str(company[:2]).lower() or ticker.lower() in str(after_about.split()[:2]).lower():
            article_text = article_text.split('About ')[0]

        except: pass

        news['yfnews'].append([url[0][0], dtg, headline, link, na.news_analyzer(headline, article_text, link)])

# BigCharts News
  """
  try:
    res = requests.get(url[2][1])
    #res.encoding = "utf-8"
    rhtml = res.text
    soup = BeautifulSoup(rhtml, "html.parser")

  except requests.exceptions.ConnectionError:
    requests.status_code = "Connection refused"

  tag = soup.select('ol > li')
  for t in tag:
    ndate = t.select('p[class=understated]')
    ntime = t.select('ol > li')
    for n in ndate:
      if not len(n) ==0:
        for h in ntime:
          dtg = ('{},{}'.format(n.text, h.select('p.fright.understated')[0].text))
          dtg = dateparser.parse(dtg).astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M (%Z)')
          if time_filter(news_interval, dtg) == True:
            headline = h.select('p.headline')[0]
            link = find_substring(str(headline), 'href="', '" target=')
            headline = headline.text
            if not len(link)==0:
              dtg = dateparser.parse(dtg).strftime("%d %b %H:%M")
              news['bcnews'].append([url[1][0], dtg, headline, link, '-']) ## add summary here!!
  """

# Morningstar News (in lieu of E-Trade News)
  try:
    res = requests.get(url[2][1])
    #res.encoding = "utf-8"
    rhtml = res.text
    soup = BeautifulSoup(rhtml, "html.parser")

  except requests.exceptions.ConnectionError:
    requests.status_code = "Connection refused"

  s1='section.stock__news'
  tag = soup.select(s1)
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
        article_text = get_full_article(link)
        
        news['msnews'].append([url[2][0], dtg, headline, link, na.news_analyzer(headline, article_text, link)])

  remove_dup_headlines(news, 'yfnews', 'msnews')


# filters news articles based on keywords on 'blacklist.csv'
  if os.name == 'nt':
    csv_path = os.getcwd()+'\\data\\blacklist.csv'
  
  else:
    csv_path = os.path.join('data/blacklist.csv')
  
  rf = pd.read_csv(csv_path, encoding='utf-8')
  rf = list(rf[rf.columns[0]])
  df = pd.DataFrame()
  for i in range(len(url)): df = df.append(news[r[i]])
  if not df.empty:
    df.columns = ['Source', 'Time', 'Headlines', 'Links', 'Analysis']
    df = df[~df["Headlines"].str.lower().str.contains('|'.join(rf))]      # deleting all headlines containing blacklist words
    df = df[~df["Headlines"].duplicated(keep='first')]                    # deleting duplicate headlines
    df.index = pd.RangeIndex(len(df.index))

  #pd.set_option('display.max_colwidth', -1)                          # For dev purpuoses
  #print (df[['Source', 'Headlines', 'Analysis']])

  return (df)

if __name__ == '__main__':
  ticker = sys.argv[1]
  ticker = ticker.upper()
  news_interval = int(sys.argv[2])
  main()