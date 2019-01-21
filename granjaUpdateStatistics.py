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

	dbCursor.execute('''UPDATE races SET trackConfig = replace(trackConfig, "CIRUITO", "");''')
	dbCursor.execute('''UPDATE races SET trackConfig = replace(trackConfig, "CIRCUITO", "");''')
	dbCursor.execute('''UPDATE races SET trackConfig = replace(trackConfig, "CRICUITO", "");''')

	dbCursor.execute('''UPDATE races SET trackConfig = replace(trackConfig, "-", "");''')
	dbCursor.execute('''UPDATE races SET trackConfig = "0" || trim(trackConfig);''')

	dbCursor.execute('''UPDATE races SET trackConfig = replace(trackConfig, "00", "0");''')
	dbCursor.execute('''UPDATE races SET trackConfig = trim(trackConfig);''')

	dbConnection.commit()
	
	####################

	dbCursor.execute('''DROP TABLE IF EXISTS LAST_RACES;''')
	dbCursor.execute('''CREATE TABLE LAST_RACES AS
		SELECT raceId,driverClass,trackConfig,COUNT(kartNumber) AS gridSize
		FROM races
		WHERE 
			driverClass = 'RENTAL'
			AND bestLapTime IS NOT NULL
			AND trackConfig IS NOT NULL
			AND trackConfig != ''
		GROUP BY raceId 
		ORDER BY raceId DESC
		LIMIT 50;''')

	dbCursor.execute('''DROP VIEW IF EXISTS VIEW_LAST_RACES;''')
	dbCursor.execute('''CREATE VIEW VIEW_LAST_RACES AS 
		SELECT driverClass,COUNT(raceId) AS QT_RACES,MAX(raceId) as lastRaceId
		FROM LAST_RACES
		GROUP BY driverClass;''')

	dbCursor.execute('''DROP VIEW IF EXISTS VIEW_LAST_RACES_PER_TRACK;''')
	dbCursor.execute('''CREATE VIEW VIEW_LAST_RACES_PER_TRACK AS 
		SELECT trackConfig, COUNT(raceId) AS QT_RACES, MAX(raceId) as lastRaceId
		FROM LAST_RACES
		WHERE driverClass = 'RENTAL'
		GROUP BY trackConfig;''')

	####################

	dbCursor.execute('''DROP TABLE IF EXISTS LAST_RACES_RANKING_RENTAL;''')
	dbCursor.execute('''CREATE TABLE LAST_RACES_RANKING_RENTAL AS
		SELECT trackConfig, driverName, raceId, MIN(bestLapTime) AS 'BEST_LAP', SUM(numOfLaps) AS QT_LAPS
		FROM races
		WHERE
			raceId IN (SELECT raceId FROM LAST_RACES)
			and driverClass = 'RENTAL'
		GROUP BY trackConfig;''')

	####################

	dbCursor.execute('''DROP TABLE IF EXISTS RENTAL_RANKING_LAPTIME_C_MODA;''')
	dbCursor.execute('''CREATE TABLE RENTAL_RANKING_LAPTIME_C_MODA AS
		SELECT kartNumber, driverName, MIN(bestLapTime) AS 'BEST_LAP', AVG(bestLapTime) AS 'AVG_BEST_LAP'
		FROM races
		WHERE 
			raceId IN (SELECT raceId FROM LAST_RACES)
			AND trackConfig IN (
				SELECT trackConfig 
				FROM VIEW_LAST_RACES_PER_TRACK
				WHERE driverClass = 'RENTAL' 
				GROUP BY trackConfig 
				ORDER BY QT_RACES DESC 
				LIMIT 1
			)
		GROUP BY kartNumber
		ORDER BY BEST_LAP;''')

	####################

	dbCursor.execute('''DROP TABLE IF EXISTS ALLTIME_RANKING_LAPTIME;''')
	dbCursor.execute('''CREATE TABLE ALLTIME_RANKING_LAPTIME AS
		SELECT driverClass, trackConfig, driverName, raceId, MIN(bestLapTime) AS 'BEST_LAP', SUM(numOfLaps) AS QT_LAPS
		FROM races
		GROUP BY driverClass,trackConfig;''')

	dbCursor.execute('''DROP TABLE IF EXISTS ALLTIME_RANKING_LAPTIME_RENTAL;''')
	dbCursor.execute('''CREATE TABLE ALLTIME_RANKING_LAPTIME_RENTAL AS
		SELECT trackConfig, driverName, raceId, MIN(bestLapTime) AS 'BEST_LAP', SUM(numOfLaps) AS QT_LAPS
		FROM races
		WHERE driverClass = 'RENTAL'
		GROUP BY trackConfig;''')

	dbConnection.commit()
	####################
	# CKC_BI_RENTAL
	####################
	dbCursor.execute('''DROP TABLE IF EXISTS RENTAL_KART_POS_FINISH;''')
	dbCursor.execute('''CREATE TABLE RENTAL_KART_POS_FINISH AS
		SELECT kartNumber, racePosition, COUNT(*) AS posCount, SUM(numOfLaps) AS numOfLaps
		FROM races
		WHERE raceId IN (SELECT raceId FROM LAST_RACES)
			AND driverClass='RENTAL' 
		GROUP BY kartNumber, racePosition;''')

	dbCursor.execute('''DROP TABLE IF EXISTS RENTAL_RANKING_PODIUM;''')
	dbCursor.execute('''CREATE TABLE RENTAL_RANKING_PODIUM AS
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
				,SUM(numOfLaps) AS qtLaps
				,(SELECT i.posCount FROM RENTAL_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=1) AS qt1
				,(SELECT i.posCount FROM RENTAL_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=2) AS qt2
				,(SELECT i.posCount FROM RENTAL_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=3) AS qt3
				,(SELECT i.posCount FROM RENTAL_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=4) AS qt4
				,(SELECT i.posCount FROM RENTAL_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=5) AS qt5
				,(SELECT i.posCount FROM RENTAL_KART_POS_FINISH i WHERE e.kartNumber=i.kartNumber AND i.racePosition=6) AS qt6
			FROM RENTAL_KART_POS_FINISH e
			GROUP BY kartNumber
		)
		WHERE qtRaces > 10
		ORDER BY PODIUM_RATE DESC;''')

	dbCursor.execute('''CREATE TEMPORARY TABLE IF NOT EXISTS TEMP_RENTAL_RANKING_PODIUM AS
		SELECT * FROM RENTAL_RANKING_PODIUM A ORDER BY A.PODIUM_RATE DESC;''')

	dbCursor.execute('''CREATE TEMPORARY TABLE IF NOT EXISTS TEMP_RENTAL_RANKING_LAPTIME_C_MODA AS
		SELECT * FROM RENTAL_RANKING_LAPTIME_C_MODA A ORDER BY A.BEST_LAP ASC;''')

	dbCursor.execute('''DROP TABLE IF EXISTS CKC_BI_RENTAL;''')
	dbCursor.execute('''CREATE TABLE CKC_BI_RENTAL AS
		SELECT P.kartNumber
			,P.qt1,P.qt2,P.qt3,P.qt4,P.qt5,P.qt6,P.qtRaces,P.qtLaps
			,P.PODIUM_RATE
			,P.rowid AS RANK_PODIUM
			,T.BEST_LAP
			,T.AVG_BEST_LAP
			,T.rowid AS RANK_LAPTIME
			,0.0125 * (P.rowid + T.rowid) AS SCORE
		FROM TEMP_RENTAL_RANKING_PODIUM P,TEMP_RENTAL_RANKING_LAPTIME_C_MODA T
		WHERE P.kartNumber=T.kartNumber
		GROUP BY P.kartNumber
		ORDER BY SCORE;''')
			#,0.0125 * (P.rowid + T.rowid) AS SCORE
			#,0.00625 * (P.rowid + 3 * T.rowid) AS SCORE
	# 1/(40+40) = .0125
	# 1/(40+3*40) = .00625

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
	#db_cur.execute('SELECT MAX(raceID) as lastRaceId FROM races;')
	db_cur.execute('SELECT raceID,substr(raceID,1,16) as T FROM races ORDER BY T DESC LIMIT 1;')
	result = db_cur.fetchone()
	con.close()

	filename = './lastRaceId'
	with open(filename, 'wb') as file:
		file.write(str.encode("{}\n".format(result['raceID'])))

	logger.info("LAST RACE ID = %d" % result['raceID'])
	
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
