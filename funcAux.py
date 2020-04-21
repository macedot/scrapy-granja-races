from flask import Flask, send_from_directory

import os, re, sys, time, sqlite3, logging, collections
import numpy, base64, htmlmin

from io import BytesIO
from statistics import median
from prettytable import from_db_cursor

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
from matplotlib import rcParams
from matplotlib.ticker import FormatStrFormatter

################################################################################
# STATIC DEF
################################################################################
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PATH_GRANJA_DB = os.path.join(BASE_DIR, "granjaResult.sqlite")

################################################################################
################################################################################
def getBestLaps(trackConfig):
	resultList = []
	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute(f'''
			SELECT bestLapTime FROM races
			WHERE raceId in (SELECT raceId FROM LAST_RACES)
				AND trackConfig = '{trackConfig}'
				AND bestLapTime is not null
		;''')
		for row in db_cur:
			resultList.append(row['bestLapTime'])
		con.close()
		resultList.sort()
	except sqlite3.Error as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])
	return resultList
################################################################################
################################################################################
def getKartBestLaps(kartNumber,trackConfig):
	resultList = []
	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute(f'''
			SELECT bestLapTime FROM races
			WHERE raceId in (SELECT raceId FROM LAST_RACES)
				AND kartNumber = '{kartNumber}'
				AND trackConfig = '{trackConfig}'
				AND bestLapTime is not null
		;''')
		for row in db_cur:
			resultList.append(row['bestLapTime'])
		con.close()
		resultList.sort()
	except sqlite3.Error as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])
	return resultList
################################################################################
################################################################################
def getTrackConfigModa():
	resultValue = '0101'
	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute(f'''
		SELECT trackConfig,COUNT(raceId) AS QT FROM races
		WHERE raceId in (SELECT raceId FROM LAST_RACES)
		AND bestLapTime is not null
		GROUP BY trackConfig
		ORDER BY QT DESC
		LIMIT 1
		;''')
		for row in db_cur:
			resultValue = row['trackConfig']
			break
		con.close()
	except sqlite3.Error as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])
	return resultValue
################################################################################
################################################################################
def getKartList(trackConfig):
	resultList = []
	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute(f'''
		-- SELECT * FROM (
			SELECT kartNumber,COUNT(raceId) AS QT FROM races
			WHERE raceId in (SELECT raceId FROM LAST_RACES)
			AND trackConfig = '{trackConfig}'
			AND bestLapTime is not null
			GROUP BY kartNumber
			ORDER BY kartNumber
		-- ) WHERE QT > 10
		;''')
		for row in db_cur:
			resultList.append(row['kartNumber'])
		con.close()
		resultList.sort()
	except sqlite3.Error as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])
	return resultList
################################################################################
################################################################################
def tableData2Html(tableName):
	htmlcode = """<html><head><title>%s</title><link href="/static/style.css" rel="stylesheet"></head>
	<body><div style="align:center; font:bold 10pt Verdana; width:100%%;">%s</div>""" % (tableName,tableName)
	htmlcodemin = ""
	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute('SELECT * FROM %s;' % (tableName))
		pt = from_db_cursor(db_cur)
		con.close()
		pt.float_format = 1.3
		htmlcode += pt.get_html_string(attributes = {"id": "sort", "class": "sort"})
		htmlcode += """<script src='/static/tablesort.min.js'></script><script src='/static/tablesort.number.js'></script><script>new Tablesort(document.getElementById('sort'));</script></body></html>"""
		htmlcodemin = htmlmin.minify(htmlcode, remove_empty_space = True)
		htmlcodemin = htmlcodemin.replace('<tr><th>', '<thead><tr><th>')
		htmlcodemin = htmlcodemin.replace('</th></tr>', '</th></tr></thead>')
		htmlcodemin = htmlcodemin.replace('<th>', '<th class="sort-header">')
		htmlcodemin = re.sub(r'\bNone\b', '0', htmlcodemin)
	except sqlite3.Error as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])
	return htmlcodemin
################################################################################
################################################################################
def plotKartHist(kartNumber = 1, trackConfig = None):
	if trackConfig is None:
		trackConfig = getTrackConfigModa()
	pyplot.gcf().clear()
	pyplot.margins(0,0)
	fig = pyplot.figure()
	fig.set_size_inches(3, 2, forward=True)
	bestLapList = getKartBestLaps(kartNumber,trackConfig)
	n, bins, patches = pyplot.hist(x=bestLapList, bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
	pyplot.grid(axis='y', alpha=0.75)
	fig.text(0.75, 0.85, kartNumber, fontsize=16, fontweight='bold', va='top')
	maxfreq = n.max()
	pyplot.ylim(top=numpy.ceil(maxfreq / 5) * 5 if maxfreq % 5 else maxfreq + 5)
	with BytesIO() as buffer:
		pyplot.tight_layout()
		pyplot.savefig(buffer, format='png')
		return base64.b64encode(buffer.getvalue()).decode()
################################################################################
################################################################################
def plotKartHistAll(trackConfig = None):
	if trackConfig is None:
		trackConfig = getTrackConfigModa()
	kartList = getKartList(trackConfig)
	numOfKarts = len(kartList)
	pyplot.gcf().clear()
	pyplot.margins(0,0)
	fig = pyplot.figure()
	fig.set_size_inches(10, 10, forward=True)
	cols = 5
	rows = int(numpy.ceil(numOfKarts/cols))
	for i, kartNumber in enumerate((kartList)):
		ax = fig.add_subplot(rows,cols,i+1)
		ax.text(0.75, 0.95, kartNumber, transform=ax.transAxes, fontsize=16, fontweight='bold', va='top')
		bestLapList = getKartBestLaps(kartNumber,trackConfig)
		ax.hist(x=bestLapList, bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
		ax.grid(axis='y', alpha=0.75)
	with BytesIO() as buffer:
		pyplot.tight_layout()
		pyplot.savefig(buffer, format='png')
		return base64.b64encode(buffer.getvalue()).decode()
################################################################################
################################################################################
def plotKartBoxplot(kartNumber = 1, trackConfig = None):
	if trackConfig is None:
		trackConfig = getTrackConfigModa()
	pyplot.gcf().clear()
	pyplot.margins(0,0)
	fig = pyplot.figure()
	fig.set_size_inches(3, 2, forward=True)
	bestLapList = getKartBestLaps(kartNumber,trackConfig)
	pyplot.boxplot(bestLapList, 0, 'gD', 1, 0.75)
	with BytesIO() as buffer:
		pyplot.tight_layout()
		pyplot.savefig(buffer, format='png')
		return base64.b64encode(buffer.getvalue()).decode()
################################################################################
################################################################################
def plotKartBoxplotAll(trackConfig = None):
	if trackConfig is None:
		trackConfig = getTrackConfigModa()
	kartList = getKartList(trackConfig)
	allLaps = getBestLaps(trackConfig)
	genMedian = median(allLaps)
	dictLaps = {}
	dictSort = {}
	for kartNumber in kartList:
		dictLaps[kartNumber] = getKartBestLaps(kartNumber,trackConfig)
		#dictSort[kartNumber] = median(dictLaps[kartNumber])
		#dictSort[kartNumber] = min(dictLaps[kartNumber])
		quartile_1, quartile_3 = numpy.percentile(dictLaps[kartNumber], [25, 75])
		iqr = quartile_3 - quartile_1
		lower_bound = quartile_1 - (iqr * 0.75)
		listLapF = [i for i in dictLaps[kartNumber] if i>= lower_bound]
		dictSort[kartNumber] = min(listLapF)
	xvalues = []
	bestLapList = []
	for kartNumber, theMedian in sorted(dictSort.items(), key=lambda x: x[1], reverse=True):
		xvalues.append(kartNumber)
		bestLapList.append(dictLaps[kartNumber])
	rcParams['ytick.direction'] = 'out'
	rcParams['xtick.direction'] = 'out'
	pyplot.gcf().clear()
	pyplot.margins(0,0)
	fig = pyplot.figure()
	fig.set_size_inches(5, 10, forward=True)
	ax = fig.add_subplot(111)
	ax.boxplot(bestLapList, 0, 'gD', 0, 0.75)
	ax.set_yticks(numpy.arange(len(xvalues))+1)
	ax.set_yticklabels(xvalues, rotation=0, ha='right')
	fig.subplots_adjust(bottom=0.3)
	minLap = int(numpy.floor(min(allLaps)))
	maxLap = int(numpy.ceil(max(allLaps)))
	xlabels = xticks = numpy.linspace(minLap, maxLap, 5)
	ax.set_xticks(xticks)
	ax.set_xticklabels(xlabels)
	ax.tick_params(axis='x', pad=10)
	ax.tick_params(axis='y', pad=10)
	ax.xaxis.set_major_formatter(FormatStrFormatter('%.0f'))
	ax.xaxis.grid(True, linestyle='-', which='major', color='lightgrey', alpha=0.5)
	ax.axvline(x=genMedian)
	with BytesIO() as buffer:
		pyplot.tight_layout()
		pyplot.savefig(buffer, format='png')
		return base64.b64encode(buffer.getvalue()).decode()
