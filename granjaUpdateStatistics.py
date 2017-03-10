#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import logging
import time
import sqlite3

from os.path import basename

################################################################################
# STATIC DEF
################################################################################
PATH_GRANJA_DB = './granjaResult.sqlite'

################################################################################
# GLOBAL DEF
################################################################################

################################################################################
################################################################################
def updateStatistics():
	func_name = sys._getframe().f_code.co_name
	logger = logging.getLogger(func_name)
	logger.debug(PATH_GRANJA_DB)

	dbConnection = sqlite3.connect(PATH_GRANJA_DB)
	dbCursor = dbConnection.cursor()

	####################
	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "KGV RACE TRACKS", "");''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "KGV RACE TRANCKS", "");''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "KVG RACE TRACKS", "");''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "KGV RACE TRANKS", "");''')

	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "CIRUITO", "");''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "CIRCUITO", "");''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "CRICUITO", "");''')

	dbCursor.execute('''UPDATE RACES SET trackConfig = replace(trackConfig, "-", "");''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = trim(trackConfig);''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = ltrim(trackConfig, '0');''')
	dbCursor.execute('''UPDATE RACES SET trackConfig = trim(trackConfig);''')

	dbConnection.commit()
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS LAST_RACES;''')
	dbCursor.execute('''CREATE TABLE LAST_RACES AS
		SELECT raceId,driverClass,trackConfig,COUNT(kartNumber) AS gridSize
		FROM races GROUP BY raceId ORDER BY raceId DESC LIMIT 50;''')

	dbCursor.execute('''DROP VIEW IF EXISTS VIEW_LAST_RACES;''')
	dbCursor.execute('''CREATE VIEW VIEW_LAST_RACES AS
		SELECT driverClass,COUNT(raceId) AS qtRaces,MAX(raceId) as lastRaceId
		FROM LAST_RACES GROUP BY driverClass;''')

	dbCursor.execute('''DROP VIEW IF EXISTS VIEW_LAST_RACES_PER_TRACK;''')
	dbCursor.execute('''CREATE VIEW VIEW_LAST_RACES_PER_TRACK AS
		SELECT driverClass,trackConfig,COUNT(raceId) AS qtRaces,MAX(raceId) as lastRaceId
		FROM LAST_RACES GROUP BY driverClass,trackConfig;''')
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS INDOOR_RANKING_LAPTIME_C_MODA;''')
	dbCursor.execute('''CREATE TABLE INDOOR_RANKING_LAPTIME_C_MODA AS
		SELECT kartNumber, driverName, MIN(bestLapTime) AS 'BEST_LAP', AVG(bestLapTime) AS 'AVG_LAP', COUNT(*) AS RACES
		FROM races
		WHERE driverClass = 'INDOOR'
			AND trackConfig IN (SELECT trackConfig FROM VIEW_LAST_RACES_PER_TRACK WHERE driverClass = 'INDOOR' ORDER BY qtRaces DESC LIMIT 1)
			AND raceId IN (SELECT raceId FROM LAST_RACES)
		GROUP BY kartNumber
		ORDER BY BEST_LAP;''')
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS PAROLIN_RANKING_LAPTIME_C_MODA;''')
	dbCursor.execute('''CREATE TABLE PAROLIN_RANKING_LAPTIME_C_MODA AS
		SELECT kartNumber, driverName, MIN(bestLapTime) AS 'BEST_LAP', AVG(bestLapTime) AS 'AVG_LAP', COUNT(*) AS RACES
		FROM races
		WHERE driverClass = 'PAROLIN'
			AND trackConfig IN (SELECT trackConfig FROM VIEW_LAST_RACES_PER_TRACK WHERE driverClass = 'PAROLIN' ORDER BY qtRaces DESC LIMIT 1)
			AND raceId IN (SELECT raceId FROM LAST_RACES)
		GROUP BY kartNumber
		ORDER BY BEST_LAP;''')
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS GERAL_RANKING_LAPTIME_C_MODA;''')
	dbCursor.execute('''CREATE TABLE GERAL_RANKING_LAPTIME_C_MODA AS
		SELECT driverClass, driverName, MIN(bestLapTime) AS 'BEST_LAP', COUNT(*) AS RACES
		FROM races
		WHERE
			trackConfig IN (SELECT trackConfig FROM (SELECT trackConfig,COUNT(*) AS qt FROM RACES ORDER BY qt DESC LIMIT 1))
			AND raceId IN (SELECT raceId FROM LAST_RACES)
		GROUP BY driverClass
		ORDER BY BEST_LAP;''')
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS GERAL_RANKING_LAPTIME;''')
	dbCursor.execute('''CREATE TABLE GERAL_RANKING_LAPTIME AS
		SELECT trackConfig, driverName, driverClass, MIN(bestLapTime) AS 'BEST_LAP', COUNT(*) AS RACES
		FROM races
		WHERE
			(driverClass='INDOOR' OR driverClass='PAROLIN')
			AND raceId IN (SELECT raceId FROM LAST_RACES)
		GROUP BY trackConfig;''')
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS ALLTIME_RANKING_LAPTIME;''')
	dbCursor.execute('''CREATE TABLE ALLTIME_RANKING_LAPTIME AS
		SELECT trackConfig, driverName, driverClass, MIN(bestLapTime) AS 'BEST_LAP', COUNT(*) AS RACES
		FROM races
		GROUP BY trackConfig;''')

	dbCursor.execute('''DROP TABLE IF EXISTS ALLTIME_RANKING_LAPTIME_INDOOR;''')
	dbCursor.execute('''CREATE TABLE ALLTIME_RANKING_LAPTIME_INDOOR AS
		SELECT trackConfig, driverName, MIN(bestLapTime) AS 'BEST_LAP', COUNT(*) AS RACES
		FROM races
		WHERE driverClass='INDOOR'
		GROUP BY trackConfig;''')

	dbCursor.execute('''DROP TABLE IF EXISTS ALLTIME_RANKING_LAPTIME_PAROLIN;''')
	dbCursor.execute('''CREATE TABLE ALLTIME_RANKING_LAPTIME_PAROLIN AS
		SELECT trackConfig, driverName, MIN(bestLapTime) AS 'BEST_LAP', COUNT(*) AS RACES
		FROM races
		WHERE driverClass='PAROLIN'
		GROUP BY trackConfig;''')

	dbConnection.commit()
	####################
	# CKC_BI_INDOOR
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS INDOOR_KART_POS_FINISH;''')
	dbCursor.execute('''CREATE TABLE INDOOR_KART_POS_FINISH AS
		SELECT kartNumber, racePosition, COUNT(*) AS posCount
		FROM races
		WHERE driverClass='INDOOR' AND raceId IN (SELECT raceId FROM LAST_RACES)
		GROUP BY kartNumber, racePosition;''')

	dbCursor.execute('''DROP TABLE IF EXISTS INDOOR_RANKING_PODIUM;''')
	dbCursor.execute('''CREATE TABLE INDOOR_RANKING_PODIUM AS
		SELECT
			*
			,(0.40*ifnull(qt1,0) + 0.25*ifnull(qt2,0) + 0.15*ifnull(qt3,0) + 0.10*ifnull(qt4,0) + 0.07*ifnull(qt5,0) + 0.03*ifnull(qt6,0)) / qtRaces AS PODIUM_RATE
			,ifnull(1.0*qt1,0) / qtRaces AS p1ratio
			,ifnull(1.0*qt2,0) / qtRaces AS p2ratio
			,ifnull(1.0*qt3,0) / qtRaces AS p3ratio
			,ifnull(1.0*qt4,0) / qtRaces AS p4ratio
			,ifnull(1.0*qt5,0) / qtRaces AS p5ratio
			,ifnull(1.0*qt6,0) / qtRaces AS p6ratio
		FROM (
			SELECT kartNumber,
				SUM(posCount) AS qtRaces
				,(SELECT i.posCount FROM INDOOR_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=1) AS qt1
				,(SELECT i.posCount FROM INDOOR_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=2) AS qt2
				,(SELECT i.posCount FROM INDOOR_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=3) AS qt3
				,(SELECT i.posCount FROM INDOOR_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=4) AS qt4
				,(SELECT i.posCount FROM INDOOR_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=5) AS qt5
				,(SELECT i.posCount FROM INDOOR_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=6) AS qt6
			FROM INDOOR_KART_POS_FINISH e
			GROUP BY kartNumber
		)
		WHERE qtRaces > 10
		ORDER BY PODIUM_RATE DESC;''')

	dbCursor.execute('''CREATE TEMPORARY TABLE IF NOT EXISTS TEMP_INDOOR_RANKING_PODIUM AS
		SELECT * FROM INDOOR_RANKING_PODIUM A ORDER BY A.PODIUM_RATE DESC;''')

	dbCursor.execute('''CREATE TEMPORARY TABLE IF NOT EXISTS TEMP_INDOOR_RANKING_LAPTIME_C_MODA AS
		SELECT * FROM INDOOR_RANKING_LAPTIME_C_MODA A ORDER BY A.BEST_LAP ASC;''')

	dbCursor.execute('''DROP TABLE IF EXISTS CKC_BI_INDOOR;''')
	dbCursor.execute('''CREATE TABLE CKC_BI_INDOOR AS
		SELECT P.kartNumber
			,P.qt1,P.qt2,P.qt3,P.qt4,P.qt5,P.qt6,P.qtRaces
			,P.PODIUM_RATE
			,P.rowid AS RANK_PODIUM
			,T.BEST_LAP
			,T.AVG_LAP
			,T.rowid AS RANK_LAPTIME
			,0.0125 * (P.rowid + T.rowid) AS SCORE
		FROM TEMP_INDOOR_RANKING_PODIUM P,TEMP_INDOOR_RANKING_LAPTIME_C_MODA T
		WHERE P.kartNumber=T.kartNumber
		GROUP BY P.kartNumber
		ORDER BY SCORE;''')
			#,0.0125 * (P.rowid + T.rowid) AS SCORE
			#,0.00625 * (P.rowid + 3 * T.rowid) AS SCORE
	# 1/(40+40) = .0125
	# 1/(40+3*40) = .00625

	dbConnection.commit()
	####################
	# CKC_BI_PAROLIN
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS PAROLIN_KART_POS_FINISH;''')
	dbCursor.execute('''CREATE TABLE PAROLIN_KART_POS_FINISH AS
		SELECT kartNumber, racePosition, COUNT(*) AS posCount
		FROM races
		WHERE driverClass='PAROLIN' AND raceId IN (SELECT raceId FROM LAST_RACES)
		GROUP BY kartNumber, racePosition;''')

	dbCursor.execute('''DROP TABLE IF EXISTS PAROLIN_RANKING_PODIUM;''')
	dbCursor.execute('''CREATE TABLE PAROLIN_RANKING_PODIUM AS
		SELECT *,(0.28*ifnull(qt1,0) + 0.20*ifnull(qt2,0) + 0.17*ifnull(qt3,0) + 0.14*ifnull(qt4,0) + 0.11*ifnull(qt5,0) + 0.09*ifnull(qt6,0)) / qtRaces AS PODIUM_RATE
		FROM (
			SELECT kartNumber,
				SUM(posCount) AS qtRaces
				,(SELECT i.posCount FROM PAROLIN_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=1) AS qt1
				,(SELECT i.posCount FROM PAROLIN_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=2) AS qt2
				,(SELECT i.posCount FROM PAROLIN_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=3) AS qt3
				,(SELECT i.posCount FROM PAROLIN_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=4) AS qt4
				,(SELECT i.posCount FROM PAROLIN_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=5) AS qt5
				,(SELECT i.posCount FROM PAROLIN_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=6) AS qt6
			FROM PAROLIN_KART_POS_FINISH e
			GROUP BY kartNumber
		)
		WHERE qtRaces > 30
		ORDER BY PODIUM_RATE DESC;''')

	dbCursor.execute('''CREATE TEMPORARY TABLE IF NOT EXISTS TEMP_PAROLIN_RANKING_PODIUM AS
		SELECT * FROM PAROLIN_RANKING_PODIUM A ORDER BY A.PODIUM_RATE DESC;''')

	dbCursor.execute('''CREATE TEMPORARY TABLE IF NOT EXISTS TEMP_PAROLIN_RANKING_LAPTIME_C_MODA AS
		SELECT * FROM PAROLIN_RANKING_LAPTIME_C_MODA A ORDER BY A.BEST_LAP ASC;''')

	dbCursor.execute('''DROP TABLE IF EXISTS CKC_BI_PAROLIN;''')
	dbCursor.execute('''CREATE TABLE CKC_BI_PAROLIN AS
		SELECT P.kartNumber
			,P.qt1,P.qt2,P.qt3,P.qt4,P.qt5,P.qt6,P.qtRaces
			,P.PODIUM_RATE
			,P.rowid AS RANK_PODIUM
			,T.BEST_LAP
			,T.AVG_LAP
			,T.rowid AS RANK_LAPTIME
			,0.00625 * (P.rowid + 3 * T.rowid) AS SCORE
		FROM TEMP_PAROLIN_RANKING_PODIUM P,TEMP_PAROLIN_RANKING_LAPTIME_C_MODA T
		WHERE P.kartNumber=T.kartNumber
		GROUP BY P.kartNumber
		ORDER BY SCORE;''')

	dbConnection.commit()
	####################
	####################
	dbConnection.execute('''VACUUM;''')
	dbConnection.commit()
	####################
	dbConnection.close()
	###
	logger.debug("DONE")

def persistLastRaceId():
	func_name = sys._getframe().f_code.co_name
	logger = logging.getLogger(func_name)

	con = sqlite3.connect(PATH_GRANJA_DB)
	con.row_factory = sqlite3.Row
	db_cur = con.cursor()
	db_cur.execute('SELECT MAX(raceID) as lastRaceId FROM races;')
	result = db_cur.fetchone()
	con.close()

	filename = './lastRaceId'
	with open(filename, 'wb') as file:
		file.write("%d\n" % result['lastRaceId'])

	logger.info("LAST RACE ID = %d" % result['lastRaceId'])
	
################################################################################
# MAIN
################################################################################
def main():
	appName = sys.argv[0]
	logging.basicConfig(
#		filename = './log/' + appName + '_' + time.strftime("%Y%m%d_%H%M%S") + '.log',
		datefmt = '%Y-%m%d %H:%M:%S',
		format = '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
		level = logging.INFO
	)
	func_name = sys._getframe().f_code.co_name
	logger = logging.getLogger(func_name)
	logger.info('Started')
	###
	updateStatistics()
	persistLastRaceId()
	###
	logger.info('Finished')

################################################################################
################################################################################
if __name__ == '__main__':
	main()
