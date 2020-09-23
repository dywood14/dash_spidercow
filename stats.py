#!/usr/bin/python
import os, sys, json, re, statistics
import csv
import base64
import requests
#import alpaca_trade_api as tradeapi
import numpy
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import dateparser
import delist
from config import *
from timesetter import *

def remove_dups(lst):
  res = [] 
  for i in lst: 
    if i not in res: 
      res.append(i)
  return res

def update_stats(ticker):
  if ticker != None and ticker != 'NoneType':

    # Prepping URL BeautifulSoups for parsing
    yahoo_url = r'https://finance.yahoo.com/quote/' + ticker
    yahoo_profile_url = r'https://finance.yahoo.com/quote/' + ticker + r'/profile?p=' +ticker  
    yahoo_his_url = r'https://finance.yahoo.com/quote/'+ ticker + r'/history?p=' +ticker
    bc_url = 'https://bigcharts.marketwatch.com/quickchart/quickchart.asp?symb=' + ticker +'&insttype=&freq=1&show=&time=4'

    ########### Stock stats
    ticker = ticker.upper()
    engage = False

    # Beautifulsoup load
    try:
      yahoo_res = requests.get(yahoo_url)
      yahoo_html = yahoo_res.text
      soup = BeautifulSoup(yahoo_html, "html.parser")
    except requests.exceptions.ConnectionError:
      requests.status_code = "Connection refused"

    try:
      yahoo_profile_res = requests.get(yahoo_profile_url)
      yahoo_profile_html = yahoo_profile_res.text
      pro_soup = BeautifulSoup( yahoo_profile_html, "html.parser")
    except requests.exceptions.ConnectionError:
      requests.status_code = "Connection refused"

    try:
      yahoo_his_res = requests.get(yahoo_his_url)
      yahoo_his_html = yahoo_his_res.text
      his_soup = BeautifulSoup( yahoo_his_html, "html.parser")
    except requests.exceptions.ConnectionError:
      requests.status_code = "Connection refused"

    try:
      bc_res = requests.get(bc_url)
      bc_html = bc_res.text
      bcsoup = BeautifulSoup(bc_html, "html.parser")
    except requests.exceptions.ConnectionError:
      requests.status_code = "Connection refused"

    # Yahoo finance data
    stats={}
    location = pro_soup.find("div", {"class": "Mb(25px)"})
    if location is not None:
      location = location.text
      if "United States" in location:
        location='US'
      else:
        location='INT'
    else:
        location ='ERROR: NOT FOUND'

    # ***This value should be from EXCHANGE PLATFORM...
    last = soup.find("div", {"class": "My(6px) Pos(r) smartphone_Mt(6px)"}).select('span')[0]
    change= soup.find("div", {"class": "My(6px) Pos(r) smartphone_Mt(6px)"}).select('span')[1]

    if last is not None:
        last = last.text.replace(',', '')
        change = change.text
        change_price = change.split(' (')[0]
        change_percent = change.split(' (')[1].split(')')[0]
    else:
        last, change, change_price, change_percent = 0

    # Pulling exchange info from Yahoo page
    exchange_long = (soup.select('div.Mt\(15px\) > div.D\(ib\).Mt\(-5px\).Mend\(20px\).Maw\(56\%\)--tab768.Maw\(52\%\).Ov\(h\).smartphone_Maw\(85\%\).smartphone_Mend\(0px\) > div.C\(\$tertiaryColor\).Fz\(12px\) > span'))
    exchange_long = exchange_long[0].text
    exchange = exchange_long.split(' - ')[0]

    if 'NASDAQ' in exchange.upper(): exchange = 'NASDAQ'
    if 'NYSE -' in exchange_long.upper(): exchange = 'NYSE'
    if 'AMEX' in exchange.upper(): exchange = 'AMEX'
    if 'NYSE AMERICAN -' in exchange_long.upper(): exchange = 'AMEX'
    if 'OTC' in exchange.upper(): exchange = 'OTC'
    if 'ARCA' in exchange.upper(): exchange = 'ARCA'

    company = soup.select('div.Mt\(15px\) > div.D\(ib\).Mt\(-5px\).Mend\(20px\).Maw\(56\%\)--tab768.Maw\(52\%\).Ov\(h\).smartphone_Maw\(85\%\).smartphone_Mend\(0px\) > div.D\(ib\) > h1')
    company = company[0].text
    if '-' in company:
      try: company = company.split(' - ')[1]
      except: pass
    if '(' in company:
      try: company = company.split(' (')[0]
      except: pass

    s={}
    for sibling in soup.find("table", {"class": "W(100%)"}).tr.next_siblings:
      key = sibling.span.text
      value = sibling.text
      value = value.replace(key, '')
      s[key] = value

    s['Close'] = soup.find("table", {"class": "W(100%)"}).tr.text.split('Close')[1]
    
    try:
      s['Volume']=(int(s['Volume'].replace(',', '')))
      s['Avg. Volume']=(int(s['Avg. Volume'].replace(',', '')))
      s['Dollar Volume']= (round(s['Volume'] * float(last)))
      s['Avg3Vol']= (s['Avg. Volume'] * 3)
      s['Vol. Aggregation Rate']= str('{}%'.format(round((100*(s['Volume']/s['Avg. Volume'])),2)))
      s['Vol. Aggregation Rate (Decimal)']= round((s['Volume']/s['Avg. Volume']),4)

    except ValueError:
      s['Volume']=0
      s['Avg. Volume']=0
      s['Dollar Volume']=0
      s['Avg3Vol']=0
      s['Vol. Aggregation Rate']=0
      s['Vol. Aggregation Rate (Decimal)']=0

    en_comments = []

    stats= {
      'basic': {
        'Timestamp': datetime.today().astimezone(nyc).strftime('%a, %Y-%m-%d %H:%M:%S (%Z)'),
        'Symbol': ticker,
        'Company': company,           #'Company': asset.name,
        'Exchange': exchange,         #'Exchange': asset.exchange,
        'Location': location,
        'P/D': '',
      },
      
      'profile': { 
        'Last': float(last),
        'Change': change,
        'Low': s["Day's Range"].split(' - ')[0].replace(',', ''),
        'High':s["Day's Range"].split(' - ')[1].replace(',', ''),
        'Open': (float(s['Open'].replace(',', ''))),
        'Close': round((float(s['Close'])),2),
      },

      'ba': {
        'Bid': s['Bid'],
        'Ask': s['Ask'],
      },

      'parsed': {
          'Change (Price)': float(change_price.strip(',')),
          'Change (Percent)': float(change_percent.strip('%')),
          'Change (Percent Decimal)': float(change_percent.strip('%'))/100,
          'Engage?': '',
          'Entry Point (Decimal)': '',
          'Entry Point': '',
          "Day's Range": s["Day's Range"],
          'Vol. Aggregation Rate (Decimal)': s['Vol. Aggregation Rate (Decimal)'],
      },

      'notes': {},

      'vstats': {
          'Vol. Condition': '',
          'Vol. Aggregation Rate': s['Vol. Aggregation Rate'],
          'Volume': s['Volume'],
          'Avg. Volume': s['Avg. Volume'],
          'Dollar Volume': s['Dollar Volume'],
          'Avg3Vol': s['Avg3Vol'],        
      },

    }

    ## Penny or Dollar?
    if float(stats['profile']['Last']) >= 1.00:
      stats['basic']['P/D'] = 'Dollar'
    else:
      stats['basic']['P/D'] = 'Penny'

    #Volume Analysis Stats
    if stats['vstats']['Dollar Volume'] >= stats['vstats']['Avg3Vol']:
      stats['vstats']['Vol. Condition'] = 'OFF'
      en_comments.append('\u274C Volume: Too High')

    elif 35000 > stats['vstats']['Dollar Volume']:
      stats['vstats']['Vol. Condition'] = 'OFF'
      en_comments.append('\u274C Volume: Too Low')

    elif 35000 <= stats['vstats']['Dollar Volume'] < 75000:
      stats['vstats']['Vol. Condition'] = 'LOW'

    elif 75000 <= stats['vstats']['Dollar Volume'] <= stats['vstats']['Avg3Vol']:
      stats['vstats']['Vol. Condition'] = 'MID'

    elif 75000 < stats['vstats']['Dollar Volume'] <= stats['vstats']['Avg3Vol']:
      stats['vstats']['Vol. Condition'] = 'HIGH'

    else:
      stats['vstats']['Vol. Condition'] = 'ERROR: OFF'
      en_comments.append('\u274C Volume: Error--Value Out of Range')

    ## Getting Historical prices and volumes for the last 30 days
    vol_spike_engage = True
    list_his_dates=[]
    list_his_open=[]
    list_his_high=[]
    list_his_low=[]
    list_his_close=[]
    list_his_adjclose=[]
    list_his_volume=[]
    list_diff_vol_ratio=[]
    list_check_vol_spikes=[]

    his_soup = his_soup.select('section > div.Pb\(10px\).Ovx\(a\).W\(100\%\) > table > tbody > tr')
    if len(his_soup) < 21: y=len(his_soup)
    else: y = 21

    """
    dtg=his_soup[0].select('span')[0].text      # checking the first date on the table
    td = (dateparser.parse(str(today.replace(tzinfo=None))) - dateparser.parse(str(dtg)))

    if td >= timedelta(days=1):                 # If the date is yesterday/before, start collect from there.
      x = 0

    else:
      x = 1                                     # If not, collect from the day before.
      y = 22
    """

    for i in range (1,22): # accumulating data for 21 days except today
      try:
        his_soup_next = his_soup[i].select('span')
        list_his_dates.append(his_soup_next[0].text)                          # Date
        list_his_open.append(his_soup_next[1].text)                           # Open
        list_his_high.append(his_soup_next[2].text)                           # High
        list_his_low.append(his_soup_next[3].text)                            # Low
        list_his_close.append(his_soup_next[4].text)                          # Close
        list_his_adjclose.append(his_soup_next[5].text)                       # Adj Close
        list_his_volume.append(int(his_soup_next[6].text.replace(',', '')))   # Volume
      except:  en_comments.append('\u274C ** Not Included 21 Day Historical Data')

    if len(list_his_dates) != 0:
      threewk_avgv=(statistics.mean(list_his_volume))
      for i in range(len(list_his_volume)-1):
        diff_ratio = (list_his_volume[i]-threewk_avgv)/list_his_volume[i]*100
        #diff_ratio = (list_his_volume[i]-list_his_volume[i+1])/list_his_volume[i]*100
        list_diff_vol_ratio.append(diff_ratio)
        #list_check_vol_spikes.append(diff_ratio > 70)

      for j in range(1):
        if list_diff_vol_ratio[j] > 70:
          en_comments.append('\u274C Volume: Spike(s) on {}'.format(list_his_dates[j].split(',')[0]))
          vol_spike_engage = False
        elif list_diff_vol_ratio[j] > 40:
          en_comments.append('\U0001F7E8 Volume: 40% ↑ than 21d avg({})'.format(list_his_dates[j].split(',')[0]))

    percent_adj = 0.00 
    percent_base = -0.16                        
    percent_engage = -1 * (percent_base + percent_adj)
    ideal_rate = 0.50

    # Adjust Ideal Volume Rate based on the time AND engage percentage
    for i in range(1,len(tz_st)):
      #if tz_st[i] <= today <= tz_ed[i]:
      if tz_st[i] <= datetime.today().astimezone(nyc) <= tz_ed[i]:
        percent_adj += (i * -0.01)
        en_comments.append('\U0001F7E8 Time: Adjusted by -{}%'.format(i))

        if i <= 3:
          ideal_rate = 0.50
        if i > 3:
          ideal_rate = 0.70

    if tz_ed[6] < datetime.today().astimezone(nyc) < today.replace(hour=17, minute=0, second=0, microsecond=0):
      percent_adj += -0.08
      en_comments.append('\U0001F7E8 Time: Adjusted by -8%')
      ideal_rate = 0.70


    if stats['basic']['Location'] == 'INT':
      percent_adj += -0.05
      en_comments.append('\U0001F7E8 Company: International')
                  
    if stats['basic']['P/D'] == 'Penny':
      percent_adj += -0.07
      en_comments.append('\U0001F7E8 Price: Penny Stock')

    if stats['vstats']['Vol. Condition'] == 'LOW':
      percent_base = -0.25  # -25% ~ -35%
      en_comments.append('\U0001F7E8 Volume: Low (Adjusting Min Entry to -20%*)')

    if stats['vstats']['Vol. Condition'] == 'HIGH':
      percent_base = -0.20
      en_comments.append('\U0001F7E8 Volume: High (Adjusting Min Entry to -20%*)')

    if stats['basic']['Exchange'] == 'OTC' and stats['basic']['P/D'] == 'Penny':
      percent_base = -0.75
      percent_adj = 0.00
      en_comments.append('\U0001F7E8 OTC and Penny (Adjusting Min Entry to -75%*)')

    if stats['basic']['P/D'] == 'Dollar':
      percent_adj += 0.00

    if stats['basic']['Exchange'] == 'OTC' and stats['basic']['P/D'] == 'Dollar':
      percent_base = -0.50
      en_comments.append('\U0001F7E8 OTC and Dollar (Adjusting Min Entry to -50%*)')

    #if stats['basic']['Exchange'] == 'OTCBB' and stats['vstats']['Vol. Condition'] =='MID' and market_open <= today < tz_noon:
    if stats['basic']['Exchange'] == 'OTCBB' and stats['vstats']['Vol. Condition'] =='MID' and market_open <= datetime.today().astimezone(nyc) < tz_noon:
      percent_base = -0.35  # -35 ~ -40%
      percent_adj = 0.00
      en_comments.append('\U0001F7E8 OTCBB (Min Entry -37%)')

    percent_engage = round((percent_base + percent_adj),4)

  ########## Checking Volume consistency

  ########## Recommending engagement based on volume

    if stats['vstats']['Vol. Condition'] =='LOW' or stats['vstats']['Vol. Condition'] == 'MID' or stats['vstats']['Vol. Condition'] == 'HIGH':
      engage = True
      en_comments.append('\u2705 Volume: Amount is Good')

    if stats['parsed']['Vol. Aggregation Rate (Decimal)'] <= ideal_rate:
      engage = True
      en_comments.append('\u2705 Volume: Increasing at Acceptable Rate')

    if ideal_rate < stats['parsed']['Vol. Aggregation Rate (Decimal)'] < 1:
      engage = True
      en_comments.append('\U0001F7E8 Volume: Increasing Fast')

    if stats['parsed']['Vol. Aggregation Rate (Decimal)'] > 1:
      engage = False
      en_comments.append('\u274C Volume: Increasing Extremely Fast')

    if 'OFF' in stats['vstats']['Vol. Condition']:
      engage = False

    if vol_spike_engage == False:
      engage = False

    ## compare company names to delisted list
    file = os.getcwd()+'\\data\\delist.csv'
    dlf = pd.read_csv(file)
    delist=[]

    for index, row in dlf.iterrows():
      delist.append(row[0])

    for word in delist:
      word = re.sub('\W+',' ', word )                             # stripping all special characters

      if word in re.sub('\W+',' ', stats['basic']['Company']):    # stripping all special characters
        en_comments.append('\u274C Noncompliant Issuer (NASDAQ)')
        engage = False

    bcsoup = bcsoup.select('#quickchart > table')[0].select('td.maincontent > div.customchart.acenter.bedonkbottom > table')
    if bcsoup != None:
      bc_img_url = str(str(bcsoup[0].select('img')[0])).split('"/>')[0]
      #bc_img_url = str(str(bcsoup[0].select('img')[0]).split('src="')[1].split('"/>')[0])
      #print(bc_img_url)

    else: bc_img_url = None

    stats['parsed']['Engage?'] = engage
    stats['parsed']['Entry Point (Decimal)'] = percent_engage
    stats['parsed']['Entry Point'] = '{}%'.format(round(percent_engage * 100), 4)

    # Parsing data to create a nicer title data
    stats['notes'] = {
      'Symbol': '({}) {}'.format(stats['basic']['Symbol'], stats['basic']['Company']),
      'Exchange': '{} / {}'.format(stats['basic']['Exchange'], stats['basic']['Location']),
      'Engage?': '{} ({})'.format(stats['parsed']['Engage?'], stats['parsed']['Entry Point']),
      'BigCharts Image URL': bc_img_url,
      'Comments': remove_dups(en_comments[::-1])
    }

    stats['profile']['Last'] = f"{float(stats['profile']['Last']):,}"
    stats['profile']['Open'] = f"{float(stats['profile']['Open']):,}"
    stats['profile']['Low'] = f"{float(stats['profile']['Low']):,}"
    stats['profile']['High'] = f"{float(stats['profile']['High']):,}"
    stats['parsed']['Last'] = f"{float(stats['parsed']['Change (Price)']):,}"
    stats['vstats']['Volume'] = f"{int(stats['vstats']['Volume']):,}"
    stats['vstats']['Avg. Volume'] = f"{int(stats['vstats']['Avg. Volume']):,}"
    stats['vstats']['Dollar Volume'] = f"{int(stats['vstats']['Dollar Volume']):,}"
    stats['vstats']['Avg3Vol'] = f"{int(stats['vstats']['Avg3Vol']):,}"

    return (stats)

if __name__ == '__main__':
  ticker = sys.argv[1]
  update_stats(ticker)

