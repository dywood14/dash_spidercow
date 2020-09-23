import re
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime, timedelta
from pytz import timezone
import dateparser
import dateutil.parser as dparser
from timesetter import *
import news

en_news=['0%', '0%', '']
sim_percent=''

# Compare and list the matching words between 'words' list and 's' headline
def list_matching_words(words, s):
	words = words[:]
	found = []

	for match in re.finditer('\w+', s):
		word = match.group()
		if word in words:
			if len(word) != 0:
				found.append(word)
				words.remove(word)
			if len(words) == 0: break

	return (found)

# Calculating the similarity percentage of lists 
def find_similarity_percentage(list1, list2):
	res = len(set(list1) & set(list2)) / float(len(set(list1) | set(list2))) * 100
	return (res)

def text_include_any(en_news, keywords_list, text, min_percent, description):
	# compare the current en_percent with the suggested en_percent
	if not '$' in en_news[0]:
		previous_en_percent = round(float(en_news[0].strip('%')),2)
		comparing_en_percent = round(float(min_percent.strip('%')),2)

		if comparing_en_percent < previous_en_percent:
			text = text.lower()
			for word in keywords_list:
				if word in text:
					en_news = [min_percent, 'any', description]

	return (en_news)

def text_include_any_unconditional(en_news, keywords_list, text, min_percent, description):
	text = text.lower()
	for word in keywords_list:
		if word in text:
			en_news = [min_percent, 'any', description]

	return (en_news)

def text_include_all(en_news, keywords_list, text, min_percent, description):
	# compare the current en_percent with the suggested en_percent
	if not '$' in en_news[0]:
		previous_en_percent = round(float(en_news[0].strip('%')),2)
		comparing_en_percent = round(float(min_percent.strip('%')),2)

		if comparing_en_percent < previous_en_percent:
			text = text.lower()
			list_matched = list_matching_words(keywords_list, text)
			#print ('matched: {}'.format(list_matched))
			min_percent=int(min_percent.split('%')[0])
			sim_percent = round(find_similarity_percentage(keywords_list, list_matched),2)		# simliarity by percentage
			
			if len(keywords_list) > 2:
				target_percent = round(100*(len(keywords_list)-1)/len(keywords_list), 2)	# If the majority is simliar to the keywords_list, then True.
				#print ('tar: {}, sim: {}'.format(target_percent, sim_percent))
			else: target_percent = 100
						
			if target_percent <= sim_percent:
				en_news = ['{}%'.format(min_percent), '{}%'.format(sim_percent), description]

	return (en_news)

def text_include_all_unconditional(en_news, keywords_list, text, min_percent, description):
	text = text.lower()
	list_matched = list_matching_words(keywords_list, text)
	#print ('matched: {}'.format(list_matched))
	min_percent=int(min_percent.split('%')[0])
	sim_percent = round(find_similarity_percentage(keywords_list, list_matched),2)		# simliarity by percentage
	
	if len(keywords_list) > 2:
		target_percent = round(100*(len(keywords_list)-1)/len(keywords_list), 2)	# If the majority is simliar to the keywords_list, then True.
		#print ('tar: {}, sim: {}'.format(target_percent, sim_percent))
	else: target_percent = 100
				
	if target_percent <= sim_percent:
		en_news = ['{}%'.format(min_percent), '{}%'.format(sim_percent), description]

	return (en_news)

# Returning the list of sentences that has matches with any words in the given list
def sentences_match_keywords(article_sentences, keywords_list):
	sentences_list=[]
	for keyword in keywords_list:
		sentences_list.append([s for s in article_sentences if keyword in s])

	# Flattening the list, in case of the unintended nesting...
	flat_list=[]
	for sublist in sentences_list:
		for item in sublist:
			flat_list.append(item)

	return (flat_list)

def senti_analyzer(sentences_list):
	eval_dataset = []
	compound=''
	compound_scores=[]
	sentences_str=''
	sentiment=''

	if len(sentences_list) != 0:
		try:
			senti = SentimentIntensityAnalyzer()
		except LookupError:
			print ('Downloading nltk vader_lexicon packages for the first time...')
			nltk.download('vader_lexicon')

		try:
			sentences_str = '. '.join(sentences_list)
			kvp = senti.polarity_scores(sentences_str)
			compound = kvp['compound']

			# compound score: -1 = extremely negative / +1 = extrmely positive
			if compound <= -0.05: sentiment = 'negative'
			if 0.05 < compound > -0.05: sentiment = 'neutral'
			if compound >= 0.05: sentiment = 'positive'

		except:
			pass
	else:
		sentiment = 'N/A'

	return (sentiment)

def news_analyzer(headline, article_text, article_url):
	en_news=['0%', '0%', '']
	headline = headline.lower()
	headline_list = [headline.split(' ')]
	#article_text = article_text.lower()

	# First, make a list for every sentence in the article_text
	article_sentences = [t for t in article_text.split('. ')]
	sentences_list =[]
	sentiment = 'N/A'

	######################### Executives News Group! ##########################
	# For Executive News, narrow down sentences that have verbs and executive position names
	execwords_list = ['ceo', 'cfo', 'cbo', 'coo', 'cmo' 'cio', 'executive', 'chairman', 'chairperson', 'president', 'secretary', 'treasurer', 'chief', 'officer', 'director']
	execverbs_list = ['elects', 'elected' 'appoint', 'departure', 'departs', 'departed', 'leave', 'terminate', 'resign', 'fires', 'fired', 'removed', 'removes']
	ignore_list = ['select', 'electric']

	# First, inspecting the headlines
	exec_headline_words = []

	# checking if the headline contains any words from execverbs_list (action verbs appointing/firing executives)
	for item in execverbs_list:
		if item in headline:
			exec_headline_words.append(item)

			# then check if it has any words from execwords_list (executive titles)
			# If matched, then append to the empty list for further inspections
			if len(exec_headline_words) > 0:
				for word in execwords_list:
					if word in headline:
						exec_headline_words.append(word)


	# remove words from ignore_list
	if len(exec_headline_words) > 2:
		for w in exec_headline_words:
			for i in ignore_list:
				if w in i:
					if i in headline:
						exec_headline_words.remove(i)

	if len(exec_headline_words) > 2:
		description = 'Executive Departure'		# If it passed the len test, at least we know that this is exec news.
		min_percent = '-18%'

		for h in exec_headline_words:
			if 'ceo' in h:
				description = 'CEO Departure'
				min_percent = '-18%'

			if 'cfo' in h:
				description = 'CFO Departure'
				min_percent = '-23%'

		en_news=[min_percent, 'any', description]

	# Now, inspecting the news article sentneces
	# In the arrival/replacement, the sentence should include the word 'as'
	# In the departure, the sentence should include the negative words like 'depart'
	if not 'Departure' in en_news[2]:
		exec_sentences = None
		try: 
			exec_sentences = sentences_match_keywords(sentences_match_keywords(article_sentences, execwords_list), ignore_list).reverse()
			exect_sentences = sentences_match_keywords(exec_sentences, execverbs_list)

		except:
			exec_sentences = []

		#exec_sentences = sentences_match_keywords(sentences_match_keywords(article_sentences, execwords_list), execverbs_list)

		if len(exec_sentences) > 0:
			description = 'Executive Departure'
			min_percent = '-18%'
			for e in exec_sentences:
				if 'ceo' in e:
					description = 'CEO Departure'
					min_percent = '-18%'

				if 'cfo' in e:
					description = 'CFO Departure'
					min_percent = '-23%'

			en_news=[min_percent, 'any', description]
	
	##############################################################################

	description = 'Downgrade'
	keywords_list = ['downgrade']
	min_percent = '-20%'
	en_news=text_include_any(en_news, keywords_list, headline, min_percent, description)
	if not description in en_news[2]:
		en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)

	description = 'Pink Sheet (Early)'
	keywords_list = ['pink', 'otc', 'otcbb', 'over-the-counter']
	min_percent = '-85%'
	en_news=text_include_any(en_news, keywords_list, article_text.lower(), min_percent, description)

	# If it is any time after 11:30 AM, then it is considered 'non-early' time block.
	if description in en_news[2]:
		if tz_ed[2] < datetime.today().astimezone(nyc):
			description = 'Pink Sheet (After 11:30 AM)'
			en_news = [min_percent, 'any, x', description]

	description = 'Business Update'
	keywords_list = ['business update', 'corporate update', 'announce', 'investigat' 'bankrupt', 'class action', 'law', 'merge', 'agreement', 'sold', 'sells', 'buys', 'bought']
	min_percent = '-35%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)

	description = 'Lost Customers'
	keywords_list = ['customer-loss', 'lost customer', 'customer loss', 'client-loss', 'client loss', 'lost client']
	min_percent = '-40%'
	en_news=text_include_any(en_news, keywords_list, headline, min_percent, description)
	if not description in en_news[2]:
		en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)


	######################### Profit Related News Group! ##########################

	# First, check and see if the news contains the words related to 'profit'
	# Based on the sentiment analysis, it determines whether the news is for profit or loss
	reportwords_list = ['profit', 'revenue', 'sales', 'income']
	gainwords_list = ['gain', 'tops', 'topped', 'increased', 'improved', 'positive']
	losswords_list = ['loss', 'decreased', 'miss', 'lost', 'negative']
	qtrwords_list = ['q1', 'q2', 'q3', 'q4', 'quarter', 'qtr']

	report_sentences = sentences_match_keywords(headline_list, reportwords_list)
	

	# First, inspecting the headlines
	gain_headline_words = []
	loss_headline_words = []

	if len(report_sentences) != 0:
		for item in reportwords_list:
			if item in headline:
				gain_headline_words.append(item)

				if len(gain_headline_words) > 0:
					# compare with gain words list
					for word in gainwords_list:
						if word in headline:
							gain_headline_words.append(word)

					# compare with loss words list
					for word in losswords_list:
						if word in headline:
							loss_headline_words.append(word)

		if len(gain_headline_words) > 0 and len(loss_headline_words) > 0:
			if len(gain_headline_words) > len(loss_headline_words):
				description = 'Profit Reported (Early)'
				min_percent = '-35%'

			# If the len is the same, we will assume that it is a loss news,
			# so that we can have a lower entry point
			if len(gain_headline_words) <= len(loss_headline_words):
				description = 'Loss Reported (Early)'
				min_percent = '-50%'

			en_news=[min_percent, 'any', description]

	## Now inspecting Articles...
	report_sentences = sentences_match_keywords(article_sentences, reportwords_list)
	gain_sentences = sentences_match_keywords(report_sentences, gainwords_list)
	loss_sentences = sentences_match_keywords(report_sentences, losswords_list)

	if not 'Reported' in en_news[2]:
		if len(report_sentences) > 1:
			if len(gain_sentences) > 0 and len(loss_sentences) > 0:
				sentiment = senti_analyzer(report_sentences)

		if sentiment != 'N/A':
			if sentiment == 'positive' or len(gain_sentences) >= len(loss_sentences):
				description = 'Profit Reported (Early)'
				min_percent = '-35%'
				en_news=[min_percent, 'senti', description]

			# Here, if len loss is higher, we overwrite the previous evaluations...
			# even if the result was positive before...
			if sentiment == 'negative' or len(loss_sentences) >= len(gain_sentences):
				description = 'Loss Reported (Early)'
				min_percent = '-50%'
				en_news=[min_percent, 'any, senti', description]

	# If it is a profit news, then check and see if it is for quarterly
	if 'Profit Reported (Early)' in en_news[2]:
		description = 'QTR Profit Reported'
		min_percent = '-35%'
		en_news=text_include_any_unconditional(en_news, qtrwords_list, headline, min_percent, description)
			
		if not 'QTR Profit Reported' in en_news[2]:
			qtr_sentences = sentences_match_keywords(report_sentences, qtrwords_list)
			if len(qtr_sentences) > 0:
				en_news=[min_percent, 'any', description]

		if 'QTR Profit Reported' in en_news[2]:
		# Test and see if the article text contains 'lowered guidance'
			description = 'Profitable Quarter w/ Lowered Guidance'
			keywords_list = ['lower guidance']
			min_percent = '-40%'
			en_news=text_include_all_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)

	### Loss Reports
	if 'Loss Reported' in en_news[2]:
		description = 'QTR Loss (Early)'
		min_percent = '-50%'
		en_news=text_include_any_unconditional(en_news, qtrwords_list, headline, min_percent, description)

		if not 'QTR Loss (Early)' in en_news[2]:
			qtr_sentences = sentences_match_keywords(loss_sentences, qtrwords_list)
			if len(qtr_sentences) > 0:
				en_news=[min_percent, 'any', description]

	### Re-adjust based on the current time
	# If it is not 'early' news, then apply lower entry points
	if tz_ed[2] < datetime.today().astimezone(nyc):
		if 'Profit Reported (Early)' in en_news[2]:
			min_percent = '-50%'
			description = 'Profit Reported (After 11:30 AM)'
			en_news=[min_percent, 'time', description]

		if 'Loss Reported (Early)' in en_news[2]:
			min_percent = '-50%'
			description = 'Loss Reported (After 11:30 AM)'
			en_news=[min_percent, 'time', description]
			
		if 'QTR Loss (Early)' in en_news[2]:
			min_percent = '-65%'
			description = 'QTR Loss (After 11:30 AM)'
			en_news=[min_percent, 'time', description]

	############################################################################

	description = 'Reverse Split'
	keywords_list = ['reverse', 'split']
	min_percent = '-40%'
	en_news=text_include_all_unconditional(en_news, keywords_list, headline, min_percent, description)
	
	if not 'Reverse Split' in en_news[2]:
		rsplit_sentences = sentences_match_keywords(article_sentences, keywords_list)
		if len(rsplit_sentences) > 0:
			en_news=[min_percent, 'any', description]

	# Checking if the day of split is today td < 1. If true, then adjust 'min_percent'
	# must check the article_text and see when the reverse split date is.
	if 'Reverse Split' in en_news[2]:
		# Find the sentence with the word 'open'. Then, delimit by '.', and find the first date in the string.
		for s in article_sentences:
			if 'open' in s:
				try: search_str_open = s.split('open')[1].split('.')[0].split(' ')[-1]
				except Exception: search_str_open = ''

			if 'effective' in s:
				try: search_str_open = s.split('effective')[1].split('.')[0].split(' ')[-1]
				except Exception: search_str_open = ''

		try:
			list_dtg = parse_multiple_dates(search_str_open)
		except Exception: list_dtg=[]

		if len(list_dtg) > 2:
			for i in range(len(list_dtg)):
				if i <= len(list_dtg):
					# comparing each date and see which one is larger...
					if list_dtg[i] > list_dtg[i-1]:
						dtg = list_dtg[i]
		if len(list_dtg) == 1:
			dtg = list_dtg[0]
		else:
			dtg = None

		if dtg != None:
			if dateparser.parse(str(today_date)) == dateparser.parse(str(dtg)):
				description = 'On the Day of Reverse Split'
				min_percent = '-25%'
				en_news=text_include_all_unconditional(en_news, keywords_list, headline, min_percent, description)

	description = 'Public Offering'
	keywords_list = ['public offer', 'direct offer', 'stock offer', 'warrants']
	min_percent = '-40%'
	en_news=text_include_any_unconditional(en_news, ['offer', 'deal'], headline, min_percent, description)

	if not description in en_news[2]:
		offer_sentences = sentences_match_keywords(article_sentences, keywords_list)
		if len(offer_sentences) > 0:
			en_news=[min_percent, 'any', description]

	price_list=[]
	exclude_list=['hundred', 'thousand', 'million', 'billion', 'trillion']
	price=None
	# Checking the article and see if it contains the price of public offering
	# if headline pass the test against keywords_list, then execute:
	if 'Public Offering' in en_news[2]:
		try:
			sentences = sentences_match_keywords(article_sentences, [' per '])
			for s in sentences:
				if '$' and 'per' in s:
					for e in exclude_list:
						if not e in s.split('$')[1]:
							s = s.split('$')[1].split(' per ')[0]

							if re.match(r'^-?\d+(?:\.\d+)?$', s) is not None:
								price_list.append(s)

		except IndexError: price = None

		if len(price_list) != 0:
			price_list = [float(i) for i in price_list]
			price = min(price_list, default=None)

		if price != None:
			#Stock offering:  20% under the price of the new shares of dollar stocks
			if price >= 1: price = round((price-(price*0.20)),2)
			#Stock offering:  35%+ under the price of the new shares of penny stocks
			elif price < 1: price = round((price-(price*0.35)),2)

			description = 'Public Offering w/ New Price'
			en_news = ['${}'.format(price), 'price', description]

	description = 'Delisting Notice'
	keywords_list = ['delist']
	min_percent = '-40%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)

	if not description in en_news[2]:
		en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)

	# If the title contains 'volunteer' or 'voluntary' AND 'delist', then bring the min_percent lower
	if 'Delist' in en_news[2]:
		description = 'Voluntary Delisting'
		keywords_list = ['volunteer', 'voluntary']
		min_percent = '-75%'
		en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)

		if not description in en_news[2]:
			en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)

	# Checking if the delisting is imminent (today). If true, then it will be commented with 'x'
	# Note: If the comment is noted with 'x' character, it will then trigger the app.py to change
	# engage variable to False, resulting in the stock not being recommended to engage! 
	if 'Delisting Notice' in en_news[2]:
		if news.time_filter(1, datetime.today().astimezone(nyc)) == True:
			description = 'Delisting Imminent'
			en_news = [min_percent, 'any, x', description]

	############################################################################
	description = 'Phase 1 News/Failure'
	keywords_list = ['phase i', 'phase-i', 'phase-1', 'phase 1']
	min_percent = '-50%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)
		
	if not description in en_news[2]:
		en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)

	description = 'Phase 2 News'
	keywords_list = ['phase ii', 'phase-ii', 'phase-2', 'phase 2']
	min_percent = '-55%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)
		
	if not description in en_news[2]:
		sentiment = senti_analyzer(sentences_match_keywords(article_sentences, keywords_list))
		if sentiment == 'positive':
			en_news=[min_percent, 'senti', description]
		if sentiment == 'negative':
			min_percent = '-60%'
			description = 'Phase 2 Failure News'
			en_news=[min_percent, 'senti', description]

	"""
	if description in en_news[2]:
		p2_fail=''
		sentence = [t for t in article_text.lower().split('. ') if 'phase' in t]
		for s in sentence:
			if 'fail' in s:
				p2_fail = True

		if p2_fail == True:
			min_percent = '-60%'
			description = 'Phase 2 Failure News'
			en_news=text_include_any_unconditional(en_news, ['fail'], article_text.lower(), min_percent, description)
	"""

	description = 'Phase 3 News'
	keywords_list = ['phase iii', 'phase-iii', 'phase-3', 'phase 3']
	min_percent = '-80%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)
		
	if not description in en_news[2]:
		sentiment = senti_analyzer(sentences_match_keywords(article_sentences, keywords_list))
		if sentiment == 'positive':
			en_news=[min_percent, 'senti', description]
		if sentiment == 'negative':
			min_percent = '-85%'
			description = 'Phase 3 Failure News'
			en_news=[min_percent, 'senti', description]

	description = 'Chapter 11 News'
	keywords_list = ['ch11', 'ch 11', 'chapter 11', 'chapter-11']
	min_percent = '-70%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)
		
	if not description in en_news[2]:
		en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)

	description = 'Chapter 7 News'
	keywords_list = ['ch7', 'ch 7', 'chapter 7', 'chapter-7']
	min_percent = '-85%'
	en_news=text_include_any_unconditional(en_news, keywords_list, headline, min_percent, description)
		
	if not description in en_news[2]:
		en_news=text_include_any_unconditional(en_news, keywords_list, article_text.lower(), min_percent, description)


	############################################################################

	# If the article does not match any criteria, then it wiil classify it as 'business update' article
	# Also, if 'Report/Earnings Call Transcript' exists at this point, then it is classified falsely.
	# It needs to be corrected as 'Business Update' news

	if en_news[0] == '0%':
		description = 'Business Update (null)'
		min_percent = '-35%'
		en_news = [min_percent, 'none', description]

	return (en_news)

if __name__ == '__main__':
	news_analyzer(headline, article_text, article_url)
	