#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import sqlite3
import cherrypy
import logging
import htmlmin

from prettytable import from_db_cursor

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot
import numpy
from io import BytesIO
import base64
import math

################################################################################
# STATIC DEF
################################################################################
PATH_GRANJA_DB = './granjaResult.sqlite'

################################################################################
# GLOBAL DEF
################################################################################


################################################################################
################################################################################
def getKartBestLaps(kartNumber,trackConfig):
	resultList = []

	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute(f'''
			SELECT bestLapTime
			FROM races
			WHERE raceId in (SELECT raceId FROM LAST_RACES)
				AND kartNumber = '{kartNumber}'
				AND trackConfig = '{trackConfig}'
				AND bestLapTime is not null
		;''')
		
		for row in db_cur:
			resultList.append(row['bestLapTime'])
		con.close()
		resultList.sort()

	except (sqlite3.Error, x) as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])

	return resultList

################################################################################
################################################################################

def getKartList(trackConfig):
	resultList = []

	try:
		con = sqlite3.connect(PATH_GRANJA_DB)
		con.row_factory = sqlite3.Row
		db_cur = con.cursor()
		db_cur.execute(f'''
		SELECT * FROM (
			SELECT kartNumber,COUNT(raceId) AS QT
			FROM races
			WHERE raceId in (SELECT raceId FROM LAST_RACES)
			AND trackConfig = '{trackConfig}'
			AND bestLapTime is not null
			GROUP BY kartNumber
			ORDER BY kartNumber
		)
		WHERE QT > 10
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
	except (sqlite3.Error, x) as e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])

	return htmlcodemin

################################################################################
################################################################################
class granjaView(object):
	@cherrypy.expose
	def index(self):
		# <td style="width:400px"><iframe src="/VIEW_LAST_RACES_PER_TRACK" frameborder="0" style="overflow:hidden;overflow-x:hidden;overflow-y:hidden;"></iframe></td>
		# <td><iframe src="/LAST_RACES_RANKING_RENTAL" frameborder="0" style="overflow:hidden;overflow-x:hidden;overflow-y:hidden;"></iframe></td>
		htmlcode = """
		<html><head><title>CKC_BI</title>
		<!-- link href="/static/style.css" rel="stylesheet" -->
		<style rel="stylesheet">
		body, html { height: 100%; }
		body { margin: 0px; padding: 0px; overflow: hidden; overflow-x: hidden; overflow-y: hidden; }
		table { width: 100%; height: 100%; padding: 0px; border: 0px; }
		iframe { height: 100%; width: 100%; top: 0px; left: 0px; right: 0px; bottom: 0px }
		</style>
		</head><body>
		<table style="position: absolute; top: 0; bottom: 0; left: 0; right: 0;">
			<tr style="height:35%;">
				<td style="width:50%"><iframe src="/LAST_RACES_RANKING_RENTAL" frameborder="0" style="overflow:hidden;overflow-x:hidden;overflow-y:hidden;"></iframe></td>
				<td><iframe src="/ALLTIME_RANKING_LAPTIME_RENTAL" frameborder="0"></iframe></td>
			</tr>
			<tr style="height:65%;">
				<td colSpan=2><iframe src="/CKC_BI_RENTAL" frameborder="0"></iframe></td>
			</tr>
		</table>
		</body></html>
		"""
		return htmlcode

	@cherrypy.expose
	def VIEW_LAST_RACES_PER_TRACK(self):
		return tableData2Html('VIEW_LAST_RACES_PER_TRACK')

	@cherrypy.expose
	def LAST_RACES_RANKING_RENTAL(self):
		return tableData2Html('LAST_RACES_RANKING_RENTAL')

	@cherrypy.expose
	def ALLTIME_RANKING_LAPTIME_RENTAL(self):
		return tableData2Html('ALLTIME_RANKING_LAPTIME_RENTAL')

	@cherrypy.expose
	def CKC_BI_RENTAL(self):
		return tableData2Html('CKC_BI_RENTAL')

	@cherrypy.expose
	def KARTHIST(self, kartNumber = 1, trackConfig = '0101'):
		# return f'<img src="data:image/png;base64,{self.image_base64(kartNumber,trackConfig)}" width="320" height="240" border="0" />'
		return f'<img src="data:image/png;base64,{self.image_base64(kartNumber,trackConfig)}" border="0" />'

	def image_base64(self, kartNumber = 1, trackConfig = '0101'):
		kartList = getKartList(trackConfig)
		numOfKarts = len(kartList)
		pyplot.gcf().clear()

		# bestLapList = getKartBestLaps(kartNumber,trackConfig)
		# totalRaces = len(bestLapList)
		# n, bins, patches = pyplot.hist(x=bestLapList, bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
		# pyplot.grid(axis='y', alpha=0.75)
		# pyplot.xlabel('Best Laptime')
		# pyplot.ylabel('Frequency')
		# pyplot.title(f'{kartNumber} @ {trackConfig}')
		# pyplot.text(0.5, 0.5, f'N = {totalRaces}', fontsize=12)
		# maxfreq = n.max()
		# pyplot.ylim(ymax=numpy.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

		pyplot.margins(0,0)
		fig = pyplot.figure()
		fig.set_size_inches(10, 10, forward=True)
		cols = 5
		rows = int(math.ceil(numOfKarts/cols))
		for i, kartNumber in enumerate((kartList)):
			ax = fig.add_subplot(rows,cols,i+1)
			ax.text(0.75, 0.95, kartNumber, transform=ax.transAxes, fontsize=16, fontweight='bold', va='top')
			bestLapList = getKartBestLaps(kartNumber,trackConfig)
			totalRaces = len(bestLapList)
			n, bins, patches = ax.hist(x=bestLapList, bins='auto', color='#0504aa', alpha=0.7, rwidth=0.85)
			ax.grid(axis='y', alpha=0.75)
			# ax.xlabel('Best Laptime')
			# ax.ylabel('Frequency')
			# ax.title(f'{kartNumber} @ {trackConfig}')
			# ax.text(0.5, 0.5, f'N = {totalRaces}', fontsize=12)
			# maxfreq = n.max()
			# ax.ylim(ymax=numpy.ceil(maxfreq / 10) * 10 if maxfreq % 10 else maxfreq + 10)

		with BytesIO() as buffer:
			pyplot.tight_layout()
			pyplot.savefig(buffer, format='png')
			return base64.b64encode(buffer.getvalue()).decode()

################################################################################
################################################################################
if __name__ == '__main__':
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	cherrypy.config.update({'server.socket_port': 8080})
	conf = {
		'/': {
			# # 'tools.sessions.on': True,
			'tools.staticdir.root': os.path.abspath(os.getcwd()),
			'tools.caching.on' : True,
			'tools.caching.delay' : 3600,
		},
		'/static': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': './public',
			'tools.caching.on' : True,
			'tools.caching.delay' : 3600,
		}
	}
	cherrypy.quickstart(granjaView(), '/', conf)

