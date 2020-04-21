import scrapy
import re
import os
import datetime
from scrapy.loader import ItemLoader
from granjaRaces.items import GranjaRacesItem

now = datetime.datetime.now()

def pair(a):
   # Or simply:
   # return zip(a[::2], a[1::2])
   for k, v in zip(a[::2], a[1::2]):
       yield k, v

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
		urls = [
			'http://kartodromogranjaviana.com.br/resultados/?flt_ano=%d&flt_mes=%d&flt_dia=%d&flt_tipo=rental' % (now.year, now.month, now.day),
			#'http://kartodromogranjaviana.com.br/resultados/?flt_ano=%d&flt_mes=%d&flt_dia=%d&flt_tipo=rental' % (2020, 3, 21),
			#'http://kartodromogranjaviana.com.br/resultados/?flt_ano=%d&flt_mes=%d&flt_tipo=rental' % (now.year, now.month),
			#'http://kartodromogranjaviana.com.br/resultados/?flt_ano=%d&flt_mes=%d&flt_tipo=rental' % (now.year, now.month-1),
			#'http://kartodromogranjaviana.com.br/resultados/?flt_ano=%d&flt_mes=%d&flt_tipo=rental' % (now.year, now.month-2),
			#'http://kartodromogranjaviana.com.br/resultados/?flt_ano=%d&flt_mes=%d&flt_tipo=rental' % (now.year, now.month-3),
		]
		for url in urls:
			self.logger.info('urlResults -> ' + url)
			yield scrapy.Request(url=url, callback=self.result_list)

	def result_list(self, response):
		list_raw = response.css('a').re(r'folha\/\?uid=(.+)\&amp;parte=prova')
		self.logger.debug('RAW raceIdList -> ' + ','.join(list_raw))
		self.logger.info('Number of RAW races at result page: %i', len(list_raw))

		for row in response.xpath('//*[@class="tb-results"]//tr')[1:]:
			day,month = row.xpath('td[1]//text()').extract_first().split('/', 1)
			hour,minute = row.xpath('td[2]//text()').extract_first().split(':', 1)
			raceDate = now.year * 10000 + int(month) * 100 + int(day)
			raceTime = int(hour) * 100 + int(minute)
			raceDateTime = "{:08d}_{:04d}".format(raceDate, raceTime)
			raceIdKGV = row.css('a').re(r'folha\/\?uid=(.+)\&amp;parte=prova')[0]
			url = 'http://kartodromogranjaviana.com.br/resultados/folha/?uid=%s&parte=prova' % (raceIdKGV)
			self.logger.info('yielding "%s - %s" with a start url: %s' % (raceDateTime, raceIdKGV, url))
			yield scrapy.Request(url, callback=self.parse, cb_kwargs={'raceDateTime': raceDateTime})

	def parse(self, response, raceDateTime):
		self.logger.debug('response.url = [' + response.url + ']')
		try:
			raceIdKGV = re.search(r'uid=(.+)\&', response.url).group(1)
			raceType = 'RENTAL'
		except AttributeError:
			self.logger.error('Invalid URL: ' + response.url)
			return

		self.logger.info('Scrapping RACE: %s' % raceIdKGV)
		self.persistToFile(raceIdKGV, response)

		responseUpper = response.text.upper()
		if 'GRANJA VIANA' not in responseUpper and 'GRANJAVIANA' not in responseUpper:
			self.logger.warning('Skipping RACE (' + responseUpper + '): ' + raceIdKGV)
			return
		if 'RENTAL' not in responseUpper:
			self.logger.warning('Skipping RACE (Not RENTAL): ' + raceIdKGV)
			return

		headerbig = response.css('div.headerbig::text').extract_first()
		if headerbig is None:
			self.logger.error('Missing headerbig (%s)' % raceIdKGV)
			return

		headerUpper = headerbig.upper()
		if '-' not in headerUpper:
			if 'CIRCUITO' not in headerUpper:
				self.logger.error('INVALID GRANJA HEADER: %s' % headerUpper)
				return
			trackConfig = 'CIRCUITO ' + headerUpper.split('CIRCUITO')[1].strip()
		else:
			trackConfig = headerUpper.split('-')[1].strip()

		self.logger.debug('trackConfig = "%s"' % trackConfig)

		listHeader = [h.strip().upper() for h in response.css('th.column::text').extract()]
		if not listHeader:
			self.logger.error('No table header for RACE %s' % raceIdKGV)
			return

		for h in DICT_HEADER.keys():
			if h not in listHeader:
				self.logger.error('MISSING HEADER COLUMN (%s): %s' % (raceIdKGV, h))
				return

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
			raceLoader.add_value('raceDateTime', raceDateTime)
			raceLoader.add_value('raceType', raceType.upper())
			raceLoader.add_value('raceId', raceIdKGV)
			raceLoader.add_value('raceIdKGV', raceIdKGV)
			raceLoader.add_value('trackConfig', trackConfig)
			for col in raceEntryData.keys():
				raceLoader.add_value(col, raceEntryData[col])

			if not raceEntryData['racePosition'].isdigit():
				raceEntryData['racePosition'] = 99
			raceLoader.add_value('id', '%02d_%s' % (int(raceEntryData['racePosition']), raceIdKGV))

			yield raceLoader.load_item()

	def persistToFile(self, raceIdKGV, response):
		filename = 'raceResults/%s.html' % raceIdKGV
		with open(filename, 'wb') as file:
			file.write(response.body)
		self.log('RACE %s saved file %s' % (raceIdKGV, filename))
