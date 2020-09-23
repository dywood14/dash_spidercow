# -*- coding: utf-8 -*-
import os, sys, csv, base64
import json
import requests
from bs4 import BeautifulSoup
import dash_dangerously_set_inner_html
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc #
from dash.dependencies import Input, Output
import dash_table
import dash_table.FormatTemplate as FormatTemplate
import plotly
import pandas as pd
from datetime import datetime, timedelta
from pytz import timezone
import dateparser
import stats, pertable, news, sec, delist
from config import *
from timesetter import *

app = dash.Dash(__name__, assets_folder='assets')
server = app.server
app.config.suppress_callback_exceptions = True

pink='rgb(249, 36, 94)'
cyan = 'rgb(96, 216, 239)'
green = 'rgb(0, 209, 96)'
highlight_color = 'rgb(239, 158, 48)'
bar_color = 'rgb(20, 20, 20)'
table_cell_color = 'rgb(20, 20, 20)'
table_header_color = 'rgb(50, 50, 50)'



def generate_title_box(str_text, timestamp):
	return html.Div(
				className='row',
				children=[
					html.H6(children=str_text, style={'color': 'white', 'padding': '0.3vmin', 'margin': '0.2vmin'}), # 'font-weight': 'bold', 
					html.P(children='',style={'padding':'0.1vmin', 'margin': '0vmin', 'backgroundColor': highlight_color}),
					html.P(
						children='Last Updated: {}'.format(timestamp),
						style={'padding-bottom': '1vmin','color':'grey', 'font-size': '1.2vmin', 'text-align':'right'}),
				]
			)

@app.callback(
	Output('entry-meter', 'children'),
	[Input('adjuster', 'value')]
)	
def adjusted_percent(adj):
	return (html.P(
		children=[r'Entry % for No News Stock: {}%'.format(-16+adj)],
		style = {'padding': '0', 'padding-left': '1.5vmin', 'font-size': '1.2vmin'})
		)

@app.callback(
	Output('profit-meter', 'children'),
	[Input('marginer', 'value')]
)	
def adjusted_percent(mar):
	return (html.P(
		children=[r'Profit margin: {}%'.format(mar)],
		style = {'padding': '0', 'padding-left': '1.5vmin', 'font-size': '1.2vmin'}),
	)

app.layout = html.Div(
	className='container',
	id='style-4',
	children=[
		html.Header(html.Link(href="https://fonts.googleapis.com/css2?family=Open+Sans&display=swap", rel="stylesheet")),
		html.Header(html.Link(href="https://fonts.googleapis.com/css2?family=Raleway&display=swap", rel="stylesheet")),
		html.Div(
			className='row',
			id='header',
			children=[

				html.H3(children='SpiderCow',
						style = {'font-size': '3.0vmin', 'color':bar_color, 'margin': '1vmin', 'padding': '0.5vmin', 'padding-left': '3vmin', 'backgroundColor': highlight_color}),

				html.P(children='', style = {'padding': '1vmin', 'backgroundColor': bar_color}),

				html.Div(
					className='row',
					id='top-search-dashboard',
					children=[
						html.Div(
							className='three columns',
							style={'height': '10vh'},
							children=[
								dcc.Input(
									id='ticker', placeholder='Enter Symbol', type='text',
									style={
									'width':'15vw', 'height': '5vh', 'margin-left': '2vmin',
									'margin-top':'2.5vmin', 'margin-bottom':'2.5vmin',
									'font-size': '1.8vmin','color':'grey'
									}
								),
								
							],
						),

						html.Div(
							className='three columns',
							style={'height': '10vh'},
							children=[
								html.P(r'Entry % Adjuster:', style={'padding':'0', 'padding-bottom': '1vmin', 'padding-left': '1.5vmin', 'margin':'0', 'font-size': '1.4vmin'}),
								html.Div(
									style={},
									children=[dcc.Slider(
									id='adjuster',
									min=-10,
									max=10,
									step=1,
									marks={
										-10: {'label': '-10'}, -9: {'label': '-9'}, -8: {'label': '-8'}, -7: {'label': '-7'},
										-6: {'label': '-6'}, -5: {'label': '-5'}, -4: {'label': '-4'}, -3: {'label': '-3'},
										-2: {'label': '-2'}, -1: {'label': '-1'}, 0: {'label': '0'}, 1: {'label': '1'},
										2: {'label': '2'}, 3: {'label': '3'}, 4: {'label': '4'}, 5: {'label': '5'},
										6: {'label': '6'}, 7: {'label': '7'}, 8: {'label': '8'}, 9: {'label': '9'}, 10: {'label': '10'}
									},
									value=0)]
								),
								html.Div(id='entry-meter'),
							]
						),

						html.Div(
							className='three columns',
							style={'height': '10vh'},
							children=[
								html.P(r'Margin % Adjuster:', style={'padding':'0', 'padding-bottom': '1vmin', 'padding-left': '1.5vmin', 'margin':'0', 'font-size': '1.4vmin'}),
								html.Div(
									style={},
									children=[dcc.Slider(
									id='marginer',
									min=1,
									max=10,
									step=1,
									marks={
										1: {'label': '1'}, 2: {'label': '2'}, 3: {'label': '3'}, 4: {'label': '4'}, 5: {'label': '5'},
										6: {'label': '6'}, 7: {'label': '7'}, 8: {'label': '8'}, 9: {'label': '9'}, 10: {'label': '10'}
									},
									value=5)]
								),
								html.Div(id='profit-meter'),
							]
						),

						html.Div(
							className='three columns',
							style={'height': '10vh'},
							children=[
								html.P('News/SEC Days Interval Adjuster:', style={'padding':'0', 'padding-bottom': '1vmin', 'padding-left': '1.5vmin', 'margin':'0', 'font-size': '1.4vmin'}),
								html.Div(
									style={},
									children=[dcc.Slider(
									id='slider-ns',
									min=1,
									max=7,
									step=1,
									marks={
										1: {'label': '1', 'style': {'color': 'rgb(0, 170, 76)'}},
										2: {'label': '2', 'style': {'font-weight': 'bold', 'color': 'rgb(0, 190, 96)'}},
										3: {'label': '3', 'style': {'font-weight': 'bold', 'color': 'rgb(9, 216, 120)'}},
										4: {'label': '4', 'style': {'color': 'rgb(9, 120, 150)'}},
										5: {'label': '5', 'style': {'color': 'rgb(9, 110, 130)'}},
										6: {'label': '6', 'style': {'color': 'rgb(9, 100, 110)'}},
										7: {'label': '7', 'style': {'color': 'rgb(9, 80, 94)'}},
									},
									value=2)]
								),

								html.P(
									children=["* 3d interval recommended if trading on Monday to cover Friday news."],
									style = {'padding': '0', 'padding-left': '1.5vmin', 'color':'grey', 'font-size': '1.2vmin'}),
							]
						),
					]
				),
					
				html.P(children='', style = {'padding': '1vmin', 'backgroundColor': bar_color}),
			],
		),
		
		html.Div(id='hidden-stats-value', style={'display': 'none'}),

		html.Div(
			className='row',
			id='body-contents',
			children=[
				html.Div(
					className='three columns',
					children=[html.Div(id='stock')],
				),

				html.Div(
					className='three columns',
					children=[html.Div(id='percent')],
				),
				
				html.Div(
					className='six columns',
					children=[
						#html.Div(id='slider-news-secs'),
						html.Div(id='news'),
						html.Div(id='secs')
					],
				),

			],
		),

		html.Div(
			className='row',
			id='footer',
			children=[
				html.Div(
					children=[
						html.P(children='',
								style = {'padding': '1vmin', 'backgroundColor': bar_color}
							),
						html.P(children=['COPYRIGHTS AND WARNING NOTICE: All rights reserved to David Yoon-Ho Wood (the developer).',
							html.Br(),html.Br(),
							"""This web service, 'SpiderCow, is originally developed to fit the developer's personal needs. SpiderCow is designed to provide useful information for Day Traders in the US stock markets.
							However, the provider of SpiderCow does not guarantee the complete accurancy of the infomration provided by this website as the data/information are aggregated from other external sources.
							SpiderCow utilizes the following web services/platforms in order to pull news and stock profile data/information: Yahoo Finances, MorningStar, E-Trade, and SEC Edgar API.""",
							html.Br(),html.Br(),
							'The provider of SpiderCow is not responsible for any legal implications and/or losses (financial, property, etc) casued by using the SpiderCow services.',
							'Please use the services with caution at your own risks.'],
								style = {'padding': '3vmin', 'color':'grey'}
							),
						]
				)
			],
		),
		dcc.Interval(
            id='interval-stats',
            interval=stats_refresh_interval*1000, # in milliseconds
            n_intervals=0
        ),
        dcc.Interval(
            id='interval-nwsecs',
            interval=nwsecs_refresh_interval*1000, # in milliseconds
            n_intervals=0
        ),

])

@app.callback(
	Output('hidden-stats-value', 'children'),
	[Input('ticker', 'value'),
	Input('adjuster', 'value'),
	Input('marginer', 'value'),
	Input('interval-stats', 'n_intervals')
	]
)
def hidden_stats(ticker, adj, mar, n):

	## Checking delist.csv
	file = os.getcwd()+'\\data\\delist.csv'
	dlf = pd.read_csv(file)

	delist_date = dlf.columns[0]
	td = (dateparser.parse(str(today)) - dateparser.parse(delist_date))

	# If delist.csv has not been updated since yesterday, then update.
	if td > timedelta(days=1):
		print ('Retrieving a new list of delisted stocks...')
		delist.update_delist()

	# Adjusting values based on slider from the top dashboard
	st= stats.update_stats(ticker)
	if st != None and st != 'NoneType':
		if adj != 0 or mar != 5:
			st['parsed']['Entry Point (Decimal)'] = st['parsed']['Entry Point (Decimal)'] + (adj/100)
			st['parsed']['Entry Point'] = '{}%'.format(st['parsed']['Entry Point (Decimal)'] * 100)
			st['notes']['Engage?'] = '{} ({})'.format(st['parsed']['Engage?'], st['parsed']['Entry Point'])

		st = json.dumps(st, indent=4)
		return (st)

@app.callback(
	Output('stock', 'children'),
	[Input('ticker', 'value'),
	Input('hidden-stats-value', 'children'),
	Input('interval-stats', 'n_intervals')
	]
)
def stock_tables(ticker, st, n):
	if st != None and st != 'NoneType':
		st = str(st)
		st = json.loads(st)
		if st['notes']['BigCharts Image URL'] != None:
			bc_img_url = str(st['notes']['BigCharts Image URL'])
		
		cdf = pd.DataFrame(pd.Series(st['notes']['Comments'], name='comments'))
		pdf = pd.DataFrame(pd.Series(st['profile'], name='profile')).transpose()
		badf = pd.DataFrame(pd.Series(st['ba'], name='bid-ask')).transpose()
		vdf = pd.DataFrame(pd.Series(st['vstats'], name='Volume Stats')).reset_index()

		gor_change=''
		gor_engage=''

		if st['parsed']['Engage?'] == True:
			gor_engage = green
		else:
			gor_engage = pink

		if '+' in str(st['profile']['Change']):
			gor_change = green
		else:
			gor_change = pink

		if pdf.empty:
			return html.Div(
						className='box',
							children=[
								generate_title_box(st['notes']['Symbol'], st['basic']['Timestamp']),
								html.P('ERROR: failed to retrieve data. Please refresh the page or try again...',
									style = {'padding': '1vmin', 'top-margin': '0vmin', 'text-align': 'center'})
					      	]
			      		)
			
		if not pdf.empty:
			return html.Div(
						className='box',
							children=[
									generate_title_box(st['notes']['Symbol'], st['basic']['Timestamp']),
									html.Div(
										className='boxcontent',
										children=[
											html.P(
												children=st['notes']['Exchange'],
												#style={'color':'white', 'padding':'0vmin', 'margin':'0vmin'}
												),

											dash_table.DataTable(
												id='table-comments',
												columns=[{"name": 'Engage? {}'.format(st['notes']['Engage?']), "id": i} for i in cdf.columns],
												data=cdf.to_dict('records'),
												style_as_list_view=True,
												style_header ={'backgroundColor': gor_engage},
												style_table={'max-width': '100%', 'overflowX':'auto'},
												style_cell={
												'border': 'none',
												'backgroundColor':table_cell_color,
												'text-align':'left',
												},

											),
											html.P(''),


								      		html.Div([
								      			dash_dangerously_set_inner_html.DangerouslySetInnerHTML('''
								      			{}{}
								      			'''.format(bc_img_url, '" scrolling="no" style="width:100%; height:100%; overflow:hidden">')),
								      		]),

									      	html.P(''),

											dash_table.DataTable(
												id='table-profile',
												columns=[{"name": i, "id": i} for i in pdf.columns],
												data=pdf.to_dict('records'),
												style_as_list_view=True,
												style_table={'max-width': '100%', 'overflowX':'auto'},
												style_cell={
												'backgroundColor':table_cell_color,
												'text-align':'center',
												'max-width': '1vmin'
												},
												style_cell_conditional=[{
													'if': {'column_id':'Change'},
													'minWidth': '10vmin',
													'color':gor_change}],
												style_header ={'backgroundColor':table_header_color, 'text-align':'center', 'max-width': '100%', 'color':'white'},
											),

											html.P(''),

											dash_table.DataTable(
												id='table-bid-ask',
												columns=[{"name": i, "id": i} for i in badf.columns],
												data=badf.to_dict('records'),
												style_as_list_view=True,
												style_cell={
												'backgroundColor':table_cell_color,
												'text-align':'center',
												'max-width': '0.6vmin'
												},
												style_header ={'backgroundColor':table_header_color, 'text-align':'center','color':'white'},
											),

											dash_table.DataTable(
												id='table-volume',
												columns=[{"name": i, "id": i} for i in vdf.columns],
												data=vdf.to_dict('records'),
												style_as_list_view=True,
												style_header={'display': 'none'},
												style_cell={
												'backgroundColor':table_cell_color,
												'text-align':'center',
												'max-width': '0.6vmin'
												},
												style_table={'height': '50%'},
												style_data_conditional=[{
													'if': {'column_id':'index'},
													'fontWeight':'bold', 'text-align':'center'}],
											),
										],
									),
							]
		      		)

@app.callback(
	Output('percent', 'children'),
	[Input('ticker', 'value'),
	Input('hidden-stats-value', 'children'),
	Input('marginer', 'value'),
	Input('interval-stats', 'n_intervals')
	]
)
def percent_table(ticker, st, mar, n):
	if st != None and st != 'NoneType':
		st = str(st)
		st = json.loads(st)
		cur_percent = float(str(st['parsed']['Change (Percent)']).replace(',',''))
		cur_price = float(str(st['profile']['Last']).replace(',',''))
		perdf = pertable.PerTab(cur_percent, cur_price, mar)
		perdf = perdf.reset_index()

		if perdf.empty:
			return html.Div(
						className='box',
						children=[
							generate_title_box('Percent Table for {}'.format(st['basic']['Symbol']), st['basic']['Timestamp']),
						html.P('ERROR: failed to retrieve data. Please refresh the page or try again...',
							style = {'padding': '1vmin', 'top-margin': '0vmin'})
						]
			)


		if not perdf.empty:
			return html.Div(
						className='box',
						children=[
							generate_title_box('Percent Table for {}'.format(st['basic']['Symbol']), st['basic']['Timestamp']),
							html.Div(
								className='boxcontent',
								children=[
									dash_table.DataTable(
										id='table-percent',
										columns=[{"name": i, "id": i} for i in perdf.columns],
										data=perdf.to_dict('records'),
										style_as_list_view=True,
										style_header={'backgroundColor':table_header_color,'text-align':'center'},
										style_cell={
											'backgroundColor':table_cell_color,
											'text-align':'center',
											'width': '0.2vmin',
											'whiteSpace': 'no-wrap',
											
										},
										style_cell_conditional=[{
											'if': {'column_id': 'Tags'},
											'text-align':'left',
											'width': '2vmin',
											'white-space': 'initial'
										}],
										style_table={
										'overflow': 'auto',
										'width': '100%',
										'textOverflow': 'wrap'
										}
									),
								]
							)
				      	]
		      		)

@app.callback(
	Output('news', 'children'),
	[Input('ticker', 'value'),
	Input('hidden-stats-value', 'children'),
	Input('slider-ns', 'value'),
	Input('interval-nwsecs', 'n_intervals')]
)
def news_tables(ticker, st, news_interval, n):
	if st != None and st != 'NoneType':
		st = str(st)
		st = json.loads(st)
		ticker = ticker
		exchange = st['basic']['Exchange']
		nwdf = news.update_news(ticker, exchange, news_interval)
		try: nwdf = nwdf.drop(columns=['Summary'])
		except: pass
		if nwdf.empty:
			return html.Div(
						className='twoboxes',
						style={'minHeight': '55vh', 'height': '55vh'},
						children=[
							generate_title_box('News for {}'.format(st['basic']['Symbol']), st['basic']['Timestamp']),
							html.P('No news found within the specified parameter.',
								style = {'padding': '1vmin', 'top-margin': '0vmin', 'text-align': 'center'})
						]
					)

		if not nwdf.empty:
			source = (nwdf['Source'].tolist())
			time = (nwdf['Time'].tolist())
			headlines = (nwdf['Headlines'].tolist())
			l = (nwdf['Links'].tolist())
			links=[]
			analysis = (nwdf['Analysis (Test)'].tolist())
			for a in analysis:
				if len(a[2]) > 1:		# check and see if 'description' is not empty
					if a[1] == 'any':
						print ('News #{}: {} (entry: {})'.format((1+analysis.index(a)), a[2], a[0], a[1]))
					else:
						print ('News #{}: {} (entry: {} / similarity: {})'.format((1+analysis.index(a)), a[2], a[0], a[1]))

			for i in range(len(l)):
				links.append(html.A(html.P('Link'), href=l[i], target="_blank"))

			dic = {'Source': source, 'Time': time, 'Headlines':headlines, 'Links': links, 'Analysis (Test)': analysis} ## delete 'analysis' later
			
			df = pd.DataFrame(dic)
			df_num = len(df)

			return html.Div(
						className='twoboxes',
						style={'minHeight': '55vh', 'height': '55vh'},
						children=[
							generate_title_box('News for {} ({} articles)'.format(st['basic']['Symbol'], df_num), st['basic']['Timestamp']),
							html.Div(
								className='boxcontent',
								style={'height': '45vh'},
								children=[dbc.Table.from_dataframe(df)],
							)
				      	]
		      		)

@app.callback(
	Output('secs', 'children'),
	[Input('ticker', 'value'),
	Input('hidden-stats-value', 'children'),
	Input('slider-ns', 'value'),
	Input('interval-nwsecs', 'n_intervals')]
)
def sec_tables(ticker, st, days_interval, n):
	if st != None and st != 'NoneType':
		st = str(st)
		st = json.loads(st)
		ticker = ticker
		secdf = sec.update_sec(ticker, days_interval)

		if secdf.empty:
			return html.Div(
						className='twoboxes',
						#style={'height': '25vh'},
						style={'height': '21vh'},
						children=[
							generate_title_box('SEC Reports for {}'.format(st['basic']['Symbol']), st['basic']['Timestamp']),
							html.P('No SEC Reports found within the specified parameter.',
								style = {'padding': '1vmin', 'top-margin': '0vmin', 'text-align': 'center'})
				      	]
		      		)

		if not secdf.empty:
			typ= (secdf['Type'].tolist())
			date= (secdf['Date'].tolist())
			l= (secdf['Links'].tolist())
			links=[]

			for i in range(len(l)):
				links.append(html.A(html.P('Link'), href=l[i], target="_blank"))

			dic = {'Type': typ, 'Date': date, 'Links': links}
			df = pd.DataFrame(dic)
			df_num = len(df)

			return html.Div(
						className='twoboxes',
						#style={'height': '25vh'},
						style={'height': '21vh'},
						children=[
							generate_title_box('SEC Reports for {} ({} articles)'.format(st['basic']['Symbol'], df_num), st['basic']['Timestamp']),
							html.Div(
								className='boxcontent',
								style={'height': '11vh'},
								children=[dbc.Table.from_dataframe(df)],
							)
						]
					)

# Loading screen CSS
#app.css.append_css({"external_url": "style_loading_screen.css"})

if __name__ == '__main__':
	if os.name == 'nt':
		app.run_server(debug=True)

	else:
		app.run_server(host='0.0.0.0', port=8080, debug=True, use_reloader=False)
