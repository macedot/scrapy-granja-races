import scrapy
import re
import os
from scrapy.loader import ItemLoader
from granjaRaces.items import GranjaRacesItem

LOGIN_URL = 'http://www.kartodromogranjaviana.com.br/resultados/resultados_cad.php'

RESULT_URL = 'http://www.kartodromogranjaviana.com.br/resultados/resultados_folha.php'

RESULT_TYPE = 1 # race

# TRIVIA 1 2017-03-xx:
#	At Jan 2017, the asfalt of KGV race track was completly rebuild.
#	Thus all previous race and lap data is 'useless' for actual predictions.
#	The folloing ID refers to the first race at KGV after race track rebuild.
#		MIN_RACE_ID = 36612
# TRIVIA 2 2017-03-13:
#	Seems that Granja is running different track layouts/configuration
#	using the same 'CIRCUITO XX' identifier. Since the physical track layout 
#	have changed a lot, some new layout possibilities will be possible,
#	and 'CIRCUITO xx' definitions will be reset. We need to monitor their data
#	and estabilish this a new MIN_RACE_ID when this reset occurs.
MIN_RACE_ID = 36612

# Usable columns only
DICT_HEADER = {
	u'POS' : 'racePosition',
	u'NO.' : 'kartNumber',
	u'NOME' : 'driverName',
	u'CLASSE' : 'driverClass',
	u'VOLTAS' : 'numOfLaps',
	u'TOTAL TEMPO' : 'raceTime',
	u'MELHOR TEMPO' : 'bestLapTime'
}

class GranjaRaceSpider(scrapy.Spider):
	name = 'granjaRaces'
	start_urls = ['http://www.kartodromogranjaviana.com.br/resultados/resultados_cad.php']

	def start_requests(self):
		return [scrapy.FormRequest(
			LOGIN_URL,
			formdata = {
				'email': 'granja@macedo.me',
				'opt': 'L'
			},
			callback = self.after_login
		)]

	def after_login(self, response):
		# check login succeed before going on
		if 'Informe o e-mail cadastrado' in response.body:
			self.logger.error('Login failed')
			return

		# $> scrapy crawl granjaRaces -a begin=36620 -a end=36642
		firstRaceId = int(getattr(self, 'begin', MIN_RACE_ID))
		if firstRaceId < MIN_RACE_ID:
			firstRaceId = MIN_RACE_ID

		lastRaceId = int(getattr(self, 'end', -1))
		if lastRaceId < 0:
			raceIdList = response.css('a').re(r'resultados_folha\.php\?tipo=1\&amp;id=(\d+)')
			lastRaceId = int(max(raceIdList))
			self.logger.info('Using scarapped END RACE: %i', lastRaceId)

		if lastRaceId < firstRaceId:
			lastRaceId = firstRaceId

		self.logger.info('Scrapping races from %i to %i', firstRaceId, lastRaceId)

		# continue scraping with authenticated session...
		for raceId in range(firstRaceId, 1 + lastRaceId, 1):
			url = '%s?tipo=%i&id=%i' % (RESULT_URL, RESULT_TYPE, raceId)
			self.logger.debug('yielding a start url: %s' % url)
			yield scrapy.Request(url, callback=self.parse)

	def parse(self, response):
		# http://www.kartodromogranjaviana.com.br/resultados/resultados_folha.php?tipo=1&id=36612
		self.logger.debug('response.url = [' + response.url + ']')
		raceId = response.url.split('=')[-1]
		if not raceId:
			self.logger.error('Invalid URL: ' + response.url)
			return

		# filter body only with 'GRANJA VIANA'
		if 'GRANJA VIANA' not in response.body:
			self.logger.warning('Skipping RACE (Not GRANJA VIANA): ' + raceId)
			return

		# discart INTERLAGOS races (for now...)
		if 'INTERLAGOS' in response.body:
			self.logger.warning('Skipping RACE (INTERLAGOS): ' + raceId)
			return

		# filter body only with 'GRANJA VIANA'
		if 'INDOOR' not in response.body:
			self.logger.warning('Skipping RACE (Not INDOOR): ' + raceId)
			return
			
		self.logger.info('Scrapping RACE: %s' % raceId)
		self.persistToFile(raceId, response)

		# get track configuration
		# KARTODROMO INTERNACIONAL GRANJA VIANA KGV RACE TRACKS - CIRCUITO 01
		headerbig = response.css('div.headerbig::text').extract_first()
		if headerbig is None:
			self.logger.error('Missing headerbig (%s)' % raceId)
			return
		
		if '-' not in headerbig:
			self.logger.error('INVALID HEADER (Missing separator): %s' % headerbig)
			return

		self.logger.debug('headerbig = "%s"' % headerbig)

		trackConfig = headerbig.split('-')[1].strip()
		self.logger.debug('trackConfig = "%s"' % trackConfig)

		# get table header
		listHeader = [h.strip().upper() for h in response.css('th.column::text').extract()]
		if not listHeader:
			self.logger.error('No table header for RACE %s' % raceId)
			return

		# check header
		for h in DICT_HEADER.keys():
			if h not in listHeader:
				self.logger.error('MISSING HEADER COLUMN (%s): %s' % (raceId, h))
				return

		# get table data
		tableData = response.xpath('//table/tr')[1:]
		for line in tableData:
			raceEntryData = {}
			i = 1
			for h in listHeader:
				if h in DICT_HEADER.keys():
					key = DICT_HEADER[h]
					value = line.xpath('td[%i]/text()' % i).extract_first()
					raceEntryData[key] = value
				i += 1
		
			raceLoader = ItemLoader(item=GranjaRacesItem(), response=response)
			raceLoader.add_value('raceId', raceId)
			raceLoader.add_value('trackConfig', trackConfig)
			for col in raceEntryData.keys():
				raceLoader.add_value(col, raceEntryData[col])

			if not raceEntryData['racePosition'].isdigit():
				raceEntryData['racePosition'] = 99
			raceLoader.add_value('id', int(raceEntryData['racePosition']) + 100 * int(raceId))

			yield raceLoader.load_item()

	def persistToFile(self, raceId, response):
		filename = 'raceResults/%s.html' % raceId
		with open(filename, 'wb') as file:
			file.write(response.body)
		self.log('RACE %s saved file %s' % (raceId, filename))
