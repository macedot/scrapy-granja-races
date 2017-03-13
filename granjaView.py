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

################################################################################
# STATIC DEF
################################################################################
PATH_GRANJA_DB = './granjaResult.sqlite'

################################################################################
# GLOBAL DEF
################################################################################


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
	except sqlite3.Error, e:
		if con:
			con.rollback()
		logging.error("Error %s:" % e.args[0])

	return htmlcodemin

################################################################################
################################################################################
class granjaView(object):
	@cherrypy.expose
	def index(self):
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
			<tr style="height:60%;">
				<td><iframe src="/LAST_RACES_RANKING_INDOOR" frameborder="0" style="overflow:hidden;overflow-x:hidden;overflow-y:hidden;"></iframe></td>
				<td><iframe src="/ALLTIME_RANKING_LAPTIME_INDOOR" frameborder="0"></iframe></td>
			</tr>
			<tr style="height:40%;">
				<td colSpan=2><iframe src="/CKC_BI_INDOOR" frameborder="0"></iframe></td>
			</tr>
		</table>
		</body></html>
		"""
		return htmlcode

	@cherrypy.expose
	def LAST_RACES_RANKING_INDOOR(self):
		return tableData2Html('LAST_RACES_RANKING_INDOOR')

	@cherrypy.expose
	def ALLTIME_RANKING_LAPTIME_INDOOR(self):
		return tableData2Html('ALLTIME_RANKING_LAPTIME_INDOOR')

	@cherrypy.expose
	def CKC_BI_INDOOR(self):
		return tableData2Html('CKC_BI_INDOOR')

################################################################################
################################################################################
if __name__ == '__main__':
	cherrypy.config.update({'server.socket_host': '0.0.0.0'})
	conf = {
		'/': {
			#'tools.sessions.on': True,
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

#TODO:
#/index/ -> iframe com rankings (SEM BI)
#/ckc/indoor/podium
#/ckc/indoor/laptime
#/ckc/indoor/bi
#/ckc/parolim/podium
#/ckc/parolim/laptime
#/ckc/parolim/bi
