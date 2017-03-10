# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import MapCompose, TakeFirst

def intCheckDQ(str):
	if 'DQ' in str:
		return 99
	return int(str)

def strTimeToFloat(str):
	retValue = 0
	str = str.replace(',', '.') # pt_BR time format
	if '.' not in str:
		return 999999
	if ':' in str:
		# 18:21.801
		valTime = str.split(':')
		sizeTime = len(valTime)
		for i in range(0, sizeTime - 1):
			retValue = retValue + pow(60, i) * float(valTime[i])
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
        input_processor=MapCompose(int),
        output_processor=TakeFirst(),
    )
	raceId = scrapy.Field(
        input_processor=MapCompose(int),
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
        input_processor=MapCompose(unicode.strip),
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
	# diffToLeader = scrapy.Field()
	# diffToPrevious = scrapy.Field()
