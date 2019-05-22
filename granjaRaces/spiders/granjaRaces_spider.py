import scrapy
import re
import os
from scrapy.loader import ItemLoader
from granjaRaces.items import GranjaRacesItem

"""
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

Result list URL:
	http://www.kgv.net.br/resultados/Default.aspx

Example of url at resulting page:
	http://www.kgv.net.br/resultados/Results.aspx?UserId=&way=../Arquivos/KGV-G-20190117001238969-Rental-Resultado.html&year=2019&month=Janeiro&day=Todos

Example DIRECT ACCESS result page:
	http://www.kgv.net.br/Arquivos/KGV-G-20190117001238969-Rental-Resultado.html
	-> Granja viana + Standard rental kart
	
	http://www.kgv.net.br/Arquivos/KGV-G-20190116232555125-Interlagos-Resultado.html
	-> Interlagos + Standard rental kart

First Race in 2019
	http://www.kgv.net.br/Arquivos/KGV-G-20190103174040999-Rental-Resultado.html

	
- Some new Race Ids are bigger than 16 digits, which compromises comparison.
  Thus, some trim is needed BUT ONLY when comparing for filter purposes."""

# def trimId(i):
# 	return int('{}'.format(i)[:16])

def pair(a):
   # Or simply:
   # return zip(a[::2], a[1::2])
   for k, v in zip(a[::2], a[1::2]):
       yield k, v

# first race of 2019
#MIN_RACE_ID = trimId(20190103174040999)

# Usable columns only
DICT_HEADER = {
	u'POS' : 'racePosition',
	u'NO.' : 'kartNumber',
	u'NOME' : 'driverName',
	u'CLASSE' : 'driverClass',		# RENTAL (Granja) | INDOOR (Interlagos)
	u'VOLTAS' : 'numOfLaps',
	u'TOTAL TEMPO' : 'raceTime',
	u'MELHOR TEMPO' : 'bestLapTime'
}

class GranjaRaceSpider(scrapy.Spider):
	name = 'granjaRaces'

	def start_requests(self):
		#return [scrapy.Request('http://www.kgv.net.br/resultados/Default.aspx', callback = self.result_list)]
		return [scrapy.Request('http://kartodromogranjaviana.com.br/resultados/?flt_tipo=rental', callback = self.result_list)]

	def result_list(self, response):
		"""
		http://www.kgv.net.br/resultados/Results.aspx?UserId=&way=../Arquivos/KGV-G-20190117001238969-Rental-Resultado.html&year=2019&month=Janeiro&day=Todos

		http://www.kgv.net.br/resultados/Results.aspx
			?UserId=
			&way=../Arquivos/KGV-G-20190117001238969-Rental-Resultado.html
			&year=2019
			&month=Janeiro
			&day=Todos


		http://kartodromogranjaviana.com.br/resultados/folha/?uid=675aab086170c00367de344474dbb5ea&parte=prova			
		""" 

		# self.logger.debug(' RESPONSE: ' + response.body.decode("utf-8"))
		# return

		#list_raw = response.css('a').re(r'Results\.aspx\?.+\&amp;way=\.\.\/Arquivos\/KGV-G-(.+)-(.+)-Resultado\.html')
		list_raw = response.css('a').re(r'folha\/\?uid=(.+)\&amp;parte=prova')
		self.logger.debug('RAW raceIdList -> ' + ','.join(list_raw))

		# theList = list(pair(list_raw))
		# raceIdList_raw = []
		# raceTypeList_raw = []
		# for raceId, raceType in theList:
		# 	raceIdList_raw.append(raceId)
		# 	raceTypeList_raw.append(raceType)

		#self.logger.info('Number of RAW races at result page: %i', len(raceIdList_raw))
		self.logger.info('Number of RAW races at result page: %i', len(list_raw))
		
		# firstRaceId = int(getattr(self, 'begin', MIN_RACE_ID)) # us AS IS (dont trim here!)
		# self.logger.info('PARAM firstRaceId = {}'.format(firstRaceId))
		# if firstRaceId < MIN_RACE_ID:
		# 	firstRaceId = MIN_RACE_ID
		# self.logger.info('Scrapping races starting from %i', firstRaceId)
		# firstRaceId_t = trimId(firstRaceId)
		# self.logger.info('firstRaceId_t: %i', firstRaceId_t)

		# for raceIdKGV, raceType in theList:
		# 	if trimId(raceIdKGV) >= firstRaceId_t:
		# 		url = 'http://www.kgv.net.br/Arquivos/KGV-G-%d-%s-Resultado.html' % (int(raceIdKGV),raceType)
		# 		self.logger.debug('yielding a start url: %s' % url)
		# 		yield scrapy.Request(url, callback=self.parse)

		for raceIdKGV in list_raw:
			url = 'http://kartodromogranjaviana.com.br/resultados/folha/?uid=%s&parte=prova' % (raceIdKGV)
			self.logger.debug('yielding a start url: %s' % url)
			yield scrapy.Request(url, callback=self.parse)


	def parse(self, response):
		self.logger.debug('response.url = [' + response.url + ']')

		try:
			#raceIdKGV,raceType = re.search(r'Arquivos\/KGV-G-(.+)-(.+)-Resultado\.html', response.url).group(1, 2)
			raceIdKGV = re.search(r'uid=(.+)\&', response.url).group(1)
			raceType = 'RENTAL'
		except AttributeError:
			self.logger.error('Invalid URL: ' + response.url)
			return

		responseUpper = response.text.upper()
		self.logger.debug('response.text = [' + responseUpper + ']')

		# if 'INTERLAGOS' in raceType.upper():
		# 	# discart INTERLAGOS races (for now...)
		# 	if 'INTERLAGOS' not in responseUpper:
		# 		self.logger.warning('Skipping invalid RACE (INTERLAGOS): ' + raceIdKGV)
		# 		return
		# else:
		# filter body only with 'GRANJA VIANA'
		if 'GRANJA VIANA' not in responseUpper and 'GRANJAVIANA' not in responseUpper:
			self.logger.warning('Skipping RACE (' + responseUpper + '): ' + raceIdKGV)
			return
		# filter body only with 'GRANJA VIANA'
		if 'RENTAL' not in responseUpper:
			self.logger.warning('Skipping RACE (Not RENTAL): ' + raceIdKGV)
			return
			
		self.logger.info('Scrapping RACE: %s' % raceIdKGV)
		self.persistToFile(raceIdKGV, response)

		# get track configuration
		# KARTODROMO INTERNACIONAL GRANJA VIANA KGV RACE TRACKS - CIRCUITO 01
		#or
		# KGV ALPIE INTERLAGOS CIRCUITO 2
		headerbig = response.css('div.headerbig::text').extract_first()
		if headerbig is None:
			self.logger.error('Missing headerbig (%s)' % raceIdKGV)
			return
		
		headerUpper = headerbig.upper()
		# if 'INTERLAGOS' in raceType.upper():
		# 	# discart INTERLAGOS races (for now...)
		# 	if 'INTERLAGOS' not in headerUpper:
		# 		self.logger.error('INVALID INTERLAGOS HEADER: %s' % headerUpper)
		# 		return
		# 	trackConfig = headerUpper.split('INTERLAGOS')[1].strip()
		# else:
		# 	if '-' not in headerUpper:
		# 		self.logger.error('INVALID GRANJA HEADER: %s' % headerUpper)
		# 		return
		# 	trackConfig = headerUpper.split('-')[1].strip()
		if '-' not in headerUpper:
			self.logger.error('INVALID GRANJA HEADER: %s' % headerUpper)
			return
		trackConfig = headerUpper.split('-')[1].strip()

		self.logger.debug('trackConfig = "%s"' % trackConfig)

		# get table header
		listHeader = [h.strip().upper() for h in response.css('th.column::text').extract()]
		if not listHeader:
			self.logger.error('No table header for RACE %s' % raceIdKGV)
			return

		# check header
		for h in DICT_HEADER.keys():
			if h not in listHeader:
				self.logger.error('MISSING HEADER COLUMN (%s): %s' % (raceIdKGV, h))
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
			raceLoader.add_value('raceType', raceType.upper())
			#raceLoader.add_value('raceId', trimId(raceIdKGV))
			raceLoader.add_value('raceId', raceIdKGV)
			raceLoader.add_value('raceIdKGV', raceIdKGV)
			raceLoader.add_value('trackConfig', trackConfig)
			for col in raceEntryData.keys():
				raceLoader.add_value(col, raceEntryData[col])

			if not raceEntryData['racePosition'].isdigit():
				raceEntryData['racePosition'] = 99
			#raceLoader.add_value('id', int(raceEntryData['racePosition']) + 100 * int(raceIdKGV))
			raceLoader.add_value('id', '%02d_%s' % (int(raceEntryData['racePosition']), raceIdKGV))

			yield raceLoader.load_item()

	def persistToFile(self, raceIdKGV, response):
		filename = 'raceResults/%s.html' % raceIdKGV
		with open(filename, 'wb') as file:
			file.write(response.body)
		self.log('RACE %s saved file %s' % (raceIdKGV, filename))
