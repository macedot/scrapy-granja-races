# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst

def intCheckDQ(str):
  try:
    return int(str)
  except:
    return 99

def strRaceType(str):
	if 'INTERLAGOS' in str:
		return 'INTERLAGOS'
	return 'GRANJA'

def strTimeToFloat(str):
	str = str.replace(',', '.') # pt_BR time format
	if '.' not in str:
		return 999999
	if ':' in str:
		# 18:21.801
		retValue = 0
		valTime = str.split(':')
		size = len(valTime)
		for i in range(0, size):
			retValue = retValue + pow(60, i) * float(valTime[size - i - 1])
	else:
		retValue = float(str)
	return float("{0:.3f}".format(retValue))

class GranjaRacesItem(scrapy.Item):
	# define the fields for your item here like:
	# name = scrapy.Field()
	# pass
	# class RaceEntry(scrapy.Item):
	# [u'POS', u'NO.', u'NOME', u'CLASSE', u'COMENT\xc1RIOS', u'PONTOS', u'VOLTAS', u'TOTAL TEMPO', u'MELHOR TEMPO', u'DIFF', u'ESPA\xc7O']
	id = scrapy.Field(
        input_processor=MapCompose(str),
        output_processor=TakeFirst(),
    )
	raceDateTime = scrapy.Field(
        input_processor=MapCompose(str),
        output_processor=TakeFirst(),
    )
	raceId = scrapy.Field(
        input_processor=MapCompose(str),
        output_processor=TakeFirst(),
    )
	raceIdKGV = scrapy.Field(
        input_processor=MapCompose(str),
        output_processor=TakeFirst(),
    )
	trackConfig = scrapy.Field(
        input_processor=MapCompose(str),
        output_processor=TakeFirst(),
    )
	racePosition = scrapy.Field(
        input_processor=MapCompose(intCheckDQ),
        output_processor=TakeFirst(),
    )
	kartNumber = scrapy.Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst(),
    )
	driverName = scrapy.Field(
        input_processor=MapCompose(str.strip),
        output_processor=TakeFirst(),
    )
	driverClass = scrapy.Field(
        input_processor=MapCompose(str),
        output_processor=TakeFirst(),
    )
	# comments = scrapy.Field()
	# points = scrapy.Field()
	numOfLaps = scrapy.Field(
        input_processor=MapCompose(int),
        output_processor=TakeFirst(),
    )
	raceTime = scrapy.Field(
        input_processor=MapCompose(strTimeToFloat),
        output_processor=TakeFirst(),
    )
	bestLapTime = scrapy.Field(
        input_processor=MapCompose(strTimeToFloat),
        output_processor=TakeFirst(),
    )
	raceType = scrapy.Field(
        input_processor=MapCompose(strRaceType),
        output_processor=TakeFirst(),
    )
	# diffToLeader = scrapy.Field()
	# diffToPrevious = scrapy.Field()
