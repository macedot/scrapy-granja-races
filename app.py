from flask import Flask, send_from_directory

import os, logging

from funcAux import *

################################################################################
# APP
################################################################################
app = Flask(__name__)

################################################################################
################################################################################
@app.route('/VIEW_LAST_RACES_PER_TRACK')
def VIEW_LAST_RACES_PER_TRACK():
	return tableData2Html('VIEW_LAST_RACES_PER_TRACK')

@app.route('/LAST_RACES_RANKING_RENTAL')
def LAST_RACES_RANKING_RENTAL():
	return tableData2Html('LAST_RACES_RANKING_RENTAL')

@app.route('/ALLTIME_RANKING_LAPTIME_RENTAL')
def ALLTIME_RANKING_LAPTIME_RENTAL():
	return tableData2Html('ALLTIME_RANKING_LAPTIME_RENTAL')

@app.route('/CKC_BI_RENTAL')
def CKC_BI_RENTAL():
	return tableData2Html('CKC_BI_RENTAL')

@app.route('/KARTHIST')
def KARTHIST(kartNumber = None, trackConfig = None):
	if trackConfig is None:
		trackConfig = getTrackConfigModa()
	if kartNumber is None:
		# return f'<img src="data:image/png;base64,{image_base64(kartNumber,trackConfig)}" width="320" height="240" border="0" />'
		return f'<img src="data:image/png;base64,{plotKartHistAll(trackConfig)}" border="0" />'
	return f'<img src="data:image/png;base64,{plotKartHist(kartNumber,trackConfig)}" border="0" />'

@app.route('/KARTBOXPLOT')
def KARTBOXPLOT(kartNumber = None, trackConfig = None):
	if trackConfig is None:
		trackConfig = getTrackConfigModa()
	if kartNumber is None:
		return f'<img src="data:image/png;base64,{plotKartBoxplotAll(trackConfig)}" border="0" />'
	return f'<img src="data:image/png;base64,{plotKartBoxplot(kartNumber,trackConfig)}" border="0" />'

@app.route('/')
def index():
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

# @app.route('/static/<filename>')
# def send_static(filename):
# 	app.logger.info('Info=' + filename)
# 	return send_from_directory('public', filename)

################################################################################
################################################################################
if __name__ == '__main__':
	app.run()
