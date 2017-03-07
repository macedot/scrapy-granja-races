import scrapy
import re

LOGIN_URL = 'http://www.kartodromogranjaviana.com.br/resultados/resultados_cad.php'
RESULT_URL = 'http://www.kartodromogranjaviana.com.br/resultados/resultados_folha.php'
RESULT_TYPE = 1 # race
MIN_RACE_ID = 36612

class GranjaRaceSpider(scrapy.Spider):
	name = 'granjaRace'
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
		if "Informe o e-mail cadastrado" in response.body:
			self.logger.error("Login failed")
			return

		firstId = getattr(self, 'firstId', MIN_RACE_ID)
		if firstId < MIN_RACE_ID:
			firstId = MIN_RACE_ID
			
		qtFetch = getattr(self, 'qtFetch', 10)
		if qtFetch < 1:
			qtFetch = 1

		# continue scraping with authenticated session...
		for raceId in range(firstId, firstId + qtFetch, 1):
			url = '%s?tipo=%i&id=%i' % (RESULT_URL, RESULT_TYPE, raceId)
			print 'yielding a start url: %s' % url
			yield scrapy.Request(url, callback=self.parse)

	def parse(self, response):
		# http://www.kartodromogranjaviana.com.br/resultados/resultados_folha.php?tipo=1&id=36612
		print '========================================'
		print 'response.url = [' + response.url + ']'
		print '========================================'
		raceId = response.url.split('=')[-1]
		if not raceId:
			self.logger.error("Invalid URL: " + response.url)
			pass

		# TODO:
		# filter body only with 'GRANJA VIANA'
			
			
		filename = 'race-%s.html' % raceId
		with open(filename, 'wb') as f:
			f.write(response.body)
		self.log('Saved file %s' % filename)
