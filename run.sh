#!/bin/bash
BEGIN_RACE=$(cat ./lastRaceId)
scrapy crawl granjaRaces -a begin=$BEGIN_RACE
python ./granjaUpdateStatistics.py
exit 0
