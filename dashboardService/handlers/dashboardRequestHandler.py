from logger import logger
from datetime import datetime
from dashboardService.handlers.baseHandler import BaseHandler
from api.officialFPL.officialFPLApi import OfficialFPLApi
import pandas as pd
from collections import defaultdict
from dashboardService.dataCollectors.liveFPLAverageDataStore import LiveFPLAverageDataStore

class DashboardRequestHandler(BaseHandler):

    _liveFPLAverageDataStore = LiveFPLAverageDataStore()

    async def get(self):
        logger.info('[INCOMING] Request at {}'.format(self.request.path))
        parentPath = self.pathInfo[0].upper()

        if parentPath == 'CLASSICLEAGUE':
            response = self.calculateLiveStandingsForLeague()
        elif parentPath == 'LATESTSTATISTICS':
            response = self.getLatestEventData()

        self.send_response(response)

    def getPlayerInfo(self, playerId):
        playerMetadata = self.staticPlayerData[playerId]
        returnObj =  {
            'id': playerId,
            'name' : playerMetadata['second_name'],
            'firstName': playerMetadata['first_name'],
            'teamCode' : playerMetadata['team_code'],
            'teamName' : self.staticTeamData[playerMetadata['team_code']]['name'],
        }
        return returnObj

    def getLatestEventData(self):
        rawData = self.fplApi.getLatestEventData()
        response = {}
        for key in rawData:
            if key.endswith('Id'):
                reformattedKey = key.replace('Id', '')
                playerDetail = self.getPlayerInfo(rawData[key])
                response[reformattedKey] = {}
                response[reformattedKey]['upper'] = playerDetail['firstName']
                response[reformattedKey]['lower'] = playerDetail['name']
                continue
            if key == 'avgScore':
                response['avgScore'] = {}
                response['avgScore']['upper'] = str(rawData['deltaAvgScore'])
                response['avgScore']['lower'] = str(rawData['avgScore'])
                continue
            if key == 'highestScore':
                response['highestScore'] = {}
                response['highestScore']['upper'] = str(rawData['deltaHighestScore'])
                response['highestScore']['lower'] = str(rawData['highestScore'])
                continue
            if key == 'highestScoringPlayerInfo':
                response['highestScoringPlayerScore'] = {}
                response['highestScoringPlayerScore']['upper'] = str(rawData['deltaHighestScoringPlayerScore'])
                response['highestScoringPlayerScore']['lower'] = str(rawData['highestScoringPlayerInfo']['points'])
                continue
            if key in ['deltaAvgScore', 'deltaHighestScore', 'deltaHighestScoringPlayerScore']:
                continue
            response[key] = {}
            response[key]['upper'] = None
            response[key]['lower'] = rawData[key]

        avgData = self._liveFPLAverageDataStore.getAvgData()

        response['top10KAvg'] = avgData['top10KAvg']
        response['top10KHitsAvg'] = avgData['top10KHitsAvg']
        response['top10KHitsInclAvg'] = avgData['top10KHitsInclAvg']

        response['overallAvg'] = avgData['overallAvg']
        response['overallHitsAvg'] = avgData['overallHitsAvg']
        response['overallHitsInclAvg'] = avgData['overallHitsInclAvg']

        response['gameweekNumber'] = avgData['gameweekNumber']

        # logger.info('# Response - ', response)
        return response

    def getCodeForChipUser(self, chipName):
        chipMap = {
            'WILDCARD':'WC',
            'TRIPLECAPTAIN':'TC',
            'BBOOST':'BB',
            'FREEHIT':'FH'
        }
        if chipName is not None:
            if chipName.upper() in chipMap:
                return chipMap[chipName.upper()]
            else:
                return None
        else:
            return '-'

    def getGWTeamInfo(self, teamId, gwId):
        data = {}
        playing = []
        bench = []
        captain = []
        captainName = None
        vicecaptainName = None

        teamRawData = self.fplApi.getGWPlayerPick(teamId, gwId)

        for player in teamRawData['picks']:
            processedPlayer = self.getPlayerInfo(player['element'])
            processedPlayer['multiplier'] = player['multiplier']
            if player['is_vice_captain'] or player['multiplier'] == 2:
                if player['is_vice_captain']:
                    vicecaptainName = processedPlayer['name']
                if player['multiplier'] == 2:
                    captainName = processedPlayer['name']
                captain.append(processedPlayer)
                if player['multiplier'] != 0:
                    playing.append(processedPlayer)
                continue
            if player['multiplier'] == 0:
                bench.append(processedPlayer)
                continue
            playing.append(processedPlayer)

        data['squad'] = {'playing' : playing, 'bench' : bench, 'captain' : captain}

        interestedEventFields = ['points', 'total_points', 'event_transfers', 'event_transfers_cost', 'points_on_bench']
        renamedEventFields = ['points', 'totalPoints', 'eventTransfers', 'eventTransfersCost',
                              'pointsOnBench']
        data['eventData'] = {}
        for field, renamedField in zip(interestedEventFields, renamedEventFields):
            data['eventData'][renamedField] = teamRawData['entry_history'][field]
        data['eventData']['activeChip'] = teamRawData['active_chip']
        data['eventData']['automaticSubs'] = teamRawData['automatic_subs']

        return data

    def getDashboardDisplayTableFields(self, item):
        # Formatted for dashboard
        for entry in item['squad']['captain']:
            if entry['multiplier'] == 2:
                captainName = entry['name']
            else:
                vicecaptainName = entry['name']

        item['captaincy'] = {}
        item['captaincy']['upper'] = ''
        item['captaincy']['lower'] = captainName

        item['vicecaptaincy'] = {}
        item['vicecaptaincy']['upper'] = ''
        item['vicecaptaincy']['lower'] = vicecaptainName

        item['ranking'] = {}
        item['ranking']['upper'] = item['lastRank'] - item['liveRank']
        item['ranking']['lower'] = item['liveRank']

        item['hits'] = {}
        item['hits']['upper'] = ''
        item['hits']['lower'] = item['eventData']['eventTransfersCost'] * (-1)

        item['chip'] = {}
        item['chip']['upper'] = ''
        item['chip']['lower'] = self.getCodeForChipUser(item['eventData']['activeChip'])

        playedCount = 0
        for player in item['squad']['playing']:
            if 'minsPlayed' in player:
                playedCount += 1
        item['playersPlayed'] = {}
        item['playersPlayed']['upper'] = ''
        item['playersPlayed']['lower'] = str(playedCount) + '/11'

        item['gwPoints'] = {}
        item['gwPoints']['upper'] = ''
        # item['gwPoints']['lower'] = item['eventData']['points']
        item['gwPoints']['lower'] = item['livePlayingTeamScore']

        # team['livePlayingTeamScore'] = playingTeamLiveScore
        # team['liveTotalTeamScore'] = team['total'] - team['eventTotal'] + playingTeamLiveScore

        item['totalPoints'] = {}
        item['totalPoints']['upper'] = ''
        # item['totalPoints']['lower'] = item['eventData']['totalPoints']
        item['totalPoints']['lower'] = item['liveTotalTeamScore']

        pName = item['playerName'].split()
        item['manager'] = {}
        item['manager']['upper'] = ' '.join(pName[1:])
        item['manager']['lower'] = pName[0]

    def getClassicLeagueStandings(self):
        if 1 not in self.pathInfo:
            return None

        leagueId = self.pathInfo[1]
        basicInfo = self.fplApi.getClassicLeagueStandings(leagueId=leagueId)

        standings = []
        currentGW = None
        interestedFields = ['event_total', 'player_name', 'rank', 'last_rank', 'rank_sort', 'total', 'entry', 'entry_name']
        renamedFields = ['eventTotal', 'playerName', 'rank', 'lastRank', 'rankSort', 'total', 'id',
                            'teamName']
        for entry in basicInfo['standings']['results']:
            item = {}
            for field, renamedField in zip(interestedFields, renamedFields):
                item[renamedField] = entry[field]
            if currentGW is None:
                teamEntryData = self.fplApi.getTeamDetails(item['id'])
                currentGW = teamEntryData['current_event']

            # Collecting the latest team composition
            item.update(self.getGWTeamInfo(item['id'], currentGW))
            # Adding adequate fields that are values for columns in dashboard
            # self.getDashboardDisplayTableFields(item)
            standings.append(item)

        # Finally adding some league level metadata
        leagueInfo = {}
        leagueInfo['leagueName'] = basicInfo['league']['name']
        leagueInfo['leagueId'] = leagueId
        leagueInfo['updateTime'] = datetime.now().strftime("%d %b, %H:%M %p %Z")
        leagueInfo['gameweekLabel'] = 'Gameweek ' + str(currentGW)
        leagueInfo['gameweekNumber'] = currentGW
        leagueInfo['numOfTeams'] = len(standings)

        response = {'standings' : standings}
        response.update(leagueInfo)
        return response

    def getLastBonusPointUpdateDate(self, eventStatus):
        bonusDate = datetime(2020,1,1)
        for item in eventStatus['status']:
            if item['bonus_added']:
                bonusDate = max(bonusDate, pd.to_datetime(item['date']))
        return bonusDate

    def updateDifferentialsData(self, data):

        playerMap = defaultdict(lambda : 0)
        teamCount = 0
        for team in data['standings']:
            teamCount += 1
            playingSquad = team['squad']['playing']
            for player in playingSquad:
                playerMap[player['id']] += 1

        for team in data['standings']:
            playingSquad = team['squad']['playing']
            team['squad']['differential'] = []
            for player in playingSquad:
                if (playerMap[player['id']]/teamCount)*100 < 20:
                    team['squad']['differential'].append(player)

        return data

    def calculateLiveStandingsForLeague(self):

        if 1 not in self.pathInfo:
            return None

        eventStatus = self.fplApi.getEventStatus()
        currentStandings = self.getClassicLeagueStandings()
        currentGW = currentStandings['gameweekNumber']
        # response = currentStandings
        # if eventStatus['leagues'].upper() != 'UPDATED':
        bonusDate = self.getLastBonusPointUpdateDate(eventStatus)
        liveActionPlayerData = self.generateInformationFromLiveData(currentGW)
        response = self.getUpdatedLeagueStandings(currentStandings, liveActionPlayerData, bonusDate)
        response = self.updateDifferentialsData(response)
        for item in response['standings']:
            self.getDashboardDisplayTableFields(item)
        # else:
        #     for idx, team in enumerate(response['standings']):
        #         team['liveRank'] = idx
        logger.info(' * Finished serving request for dashboard live league')
        return response

    def filterOutUnplayedPlayers(self, liveDataMap):

        playedElements = {}
        for idx, element in enumerate(liveDataMap):
            elementId = element['id']
            if element['stats']['minutes'] == 0:
                continue

            elementInfo = {}
            elementInfo['id'] = elementId
            elementInfo['points'] = element['stats']['total_points']
            elementInfo['bonusPoints'] = element['stats']['bps']
            elementInfo['fixtures'] = []
            elementInfo['minsPlayed'] = element['stats']['minutes']
            for event in element['explain']:
                elementInfo['fixtures'].append(event['fixture'])
            playedElements[elementId] = elementInfo

        return playedElements

    def generateInformationFromLiveData(self, currentGW):

        liveData = self.fplApi.getLiveData(currentGW)
        if 'elements' in liveData:
            liveData = liveData['elements']
        else:
            liveData = None
        liveData = self.filterOutUnplayedPlayers(liveData)
        liveData = self.accountForBonusPoints(liveData)
        return liveData

    def isBonusIncludedInTotal(self, fixtureId, fixtures, bonusDate):
        for fixture in fixtures:
            if fixture['id'] == fixtureId:
                if pd.to_datetime(fixture['kickoff_time']).date() <= bonusDate.date():
                    return True
        return False

    def updatePointBasedOnLiveScores(self, team, liveActionData, bonusDate, gwNum, fixtures, addBonus):
        teamPicks = team['squad']
        playingTeamLiveScore = 0
        benchTeamLiveScore = 0
        for mode in teamPicks:
            for player in teamPicks[mode]:
                multiplier = player['multiplier'] if mode != 'bench' else 1
                player['liveScore'] = 0
                if player['id'] in liveActionData:
                    player['minsPlayed'] = liveActionData[player['id']]['minsPlayed']
                    bonusIncludedInTotal = self.isBonusIncludedInTotal(liveActionData[player['id']]['fixtures'][0],
                                                                       fixtures, bonusDate)
                    player['liveScore'] += multiplier * liveActionData[player['id']]['points']
                    if addBonus and not bonusIncludedInTotal:
                        player['liveScore'] += multiplier * liveActionData[player['id']]['bonus']
                if mode.upper() == 'PLAYING':
                    playingTeamLiveScore += player['liveScore']
                if mode.upper() == 'BENCH':
                    benchTeamLiveScore += player['liveScore']

        team['livePlayingTeamScore'] = playingTeamLiveScore
        team['liveTotalTeamScore'] = team['total'] - team['eventTotal'] + playingTeamLiveScore
        team['liveBenchTeamScore'] = benchTeamLiveScore
        return team

    def basedOnLivePlayingTeamScore(self, elem):
        return elem['liveTotalTeamScore']

    def getUpdatedLeagueStandings(self, currentStandings, liveActionMap, bonusDate, addBonus=True):
        fixtures = self.fplApi.getFixtures(currentStandings['gameweekNumber'])
        for team in currentStandings['standings']:
            team = self.updatePointBasedOnLiveScores(team, liveActionMap, bonusDate, currentStandings['gameweekNumber'], fixtures, addBonus)
        currentStandings['standings'] = sorted(currentStandings['standings'], key=self.basedOnLivePlayingTeamScore,
                                               reverse=True)
        for idx, team in enumerate(currentStandings['standings']):
            team['liveRank'] = idx + 1
        return currentStandings

    def accountForBonusPoints(self, liveData):

        innerDefaultDict = defaultdict(lambda : [])
        # bpsMapPerFixture = defaultdict(lambda : innerDefaultDict)
        bpsMapPerFixture = {}

        for elementId in liveData:
            element = liveData[elementId]
            element['bonus'] = 0
            for f in element['fixtures']:
                if f in bpsMapPerFixture:
                    if element['bonusPoints'] in bpsMapPerFixture[f]:
                        bpsMapPerFixture[f][element['bonusPoints']].append(element)
                    else:
                        bpsMapPerFixture[f][element['bonusPoints']] = []
                        bpsMapPerFixture[f][element['bonusPoints']].append(element)
                else:
                    bpsMapPerFixture[f] = {}
                    bpsMapPerFixture[f][element['bonusPoints']] = []
                    bpsMapPerFixture[f][element['bonusPoints']].append(element)
                # bpsMapPerFixture[f][element['bonusPoints']].append(element)

        for fixtureId in bpsMapPerFixture:
            maxBps = max(bpsMapPerFixture[fixtureId].keys())
            if len(bpsMapPerFixture[fixtureId][maxBps]) == 2:
                for element in bpsMapPerFixture[fixtureId][maxBps]:
                    liveData[element['id']]['bonus'] += 3
                nextMaxBps = max([x for x in bpsMapPerFixture[fixtureId].keys() if x not in [maxBps]])
                for element in bpsMapPerFixture[fixtureId][nextMaxBps]:
                    liveData[element['id']]['bonus'] += 1
            else:
                liveData[bpsMapPerFixture[fixtureId][maxBps][0]['id']]['bonus'] += 3
                nextMaxBps = max([x for x in bpsMapPerFixture[fixtureId].keys() if x not in [maxBps]])
                if len(bpsMapPerFixture[fixtureId][nextMaxBps]) == 2:
                    for element in bpsMapPerFixture[fixtureId][nextMaxBps]:
                        liveData[element['id']]['bonus'] += 2
                else:
                    liveData[bpsMapPerFixture[fixtureId][nextMaxBps][0]['id']]['bonus'] += 2
                    nextNextMaxBps = max([x for x in bpsMapPerFixture[fixtureId].keys() if x not in [maxBps, nextMaxBps]])
                    if len(bpsMapPerFixture[fixtureId][nextNextMaxBps]) == 2:
                        for element in bpsMapPerFixture[fixtureId][nextNextMaxBps]:
                            liveData[element['id']]['bonus'] += 1
                    else:
                        liveData[bpsMapPerFixture[fixtureId][nextNextMaxBps][0]['id']]['bonus'] += 1

        return liveData




