# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


import logging

from scrapy import signals

from sqlalchemy import Column, Integer, String, DateTime, Float, PrimaryKeyConstraint
from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)

DeclarativeBase = declarative_base()

# dbCursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS racePosition_index ON races (raceId, racePosition);')
# dbCursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS race_kart_index ON races (raceId, kartNumber);')
# dbCursor.execute('CREATE INDEX IF NOT EXISTS driverClass_index ON races (driverClass);')

class GranjaRaces(DeclarativeBase):
	__tablename__ = "races"

	id = Column('id', Integer, primary_key=True)
	raceId = Column('raceId', Integer)
	raceIdKGV = Column('raceIdKGV', Integer)
	trackConfig = Column('trackConfig', String)
	racePosition = Column('racePosition', Integer)
	kartNumber = Column('kartNumber', Integer)
	driverName = Column('driverName', String)
	driverClass = Column('driverClass', String)
	# comments = Column('comments', String)
	# points = Column('points', Integer)
	numOfLaps = Column('numOfLaps', Integer)
	raceTime = Column('raceTime', Float)
	bestLapTime = Column('bestLapTime', Float)
	# diffToLeader = Column('diffToLeader', Float)
	# diffToPrevious = Column('diffToPrevious', Float)
	
	def __repr__(self):
		return "<GranjaRaces({}_{})>".format(self.raceId, self.racePosition)

class GranjaRacesPipeline(object):
	def __init__(self, settings):
		self.database = settings.get('DATABASE')
		self.sessions = {}

	@classmethod
	def from_crawler(cls, crawler):
		pipeline = cls(crawler.settings)
		crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
		crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
		return pipeline

	def create_engine(self):
		engine = create_engine(URL(**self.database), poolclass=NullPool)
		return engine

	def create_tables(self, engine):
		DeclarativeBase.metadata.create_all(engine, checkfirst=True)

	def create_session(self, engine):
		session = sessionmaker(bind=engine)()
		return session

	def spider_opened(self, spider):
		engine = self.create_engine()
		self.create_tables(engine)
		session = self.create_session(engine)
		self.sessions[spider] = session

	def spider_closed(self, spider):
		session = self.sessions.pop(spider)
		session.close()

	def process_item(self, item, spider):
		session = self.sessions[spider]
		raceEntry = GranjaRaces(**item)
		try:
			# session.add(raceEntry)
			session.merge(raceEntry) # inser or update if exists
			session.commit()
			logger.info('Item {} stored in db'.format(raceEntry))
		except:
			logger.info('Failed to add {} to db'.format(raceEntry))
			session.rollback()
			raise

		return item

# class GranjaRacesPipeline(object):
	# def process_item(self, item, spider):
		# return item

