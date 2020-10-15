import requests
import json
from logger.logger import logger

class OfficialFPLApi:

    _baseUrl = 'https://fantasy.premierleague.com/api/'
    _staticFPLBootstrapData = None

    def getCompleteUrl(self, slug):
        return self._baseUrl + slug

    def getTeamDetails(self, teamId):
        logger.info('Collecting basic team info for {}'.format(teamId))

        slug = 'entry/{}/'
        formattedSlug = slug.format(teamId)
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for basic team info : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        logger.info('Collected response for classic league standings : {}'.format(responseData))
        return responseData

    def getLiveData(self, eventNumber):
        logger.info('Collecting live data info')

        slug = 'event/{}/live'
        formattedSlug = slug.format(eventNumber)
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for basic team info : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        logger.info('Collected response for live data : {}'.format(responseData))
        return responseData

    def getStaticPlayerData(self):
        staticPlayerData = {}
        for player in self.getStaticDataBootstrap()['elements']:
            staticPlayerData[player['id']] = player
        return staticPlayerData

    def getLatestEventData(self):
        latestEventData = {}
        selectedEvent = None
        interestedFields = ['name', 'average_entry_score', 'highest_score', 'most_selected', 'most_transferred_in', 'top_element', 'top_element_info',
                            'most_captained', 'most_vice_captained']
        renamedFields = ['name', 'avgScore', 'highestScore', 'mostSelectedId', 'mostTransferredInId', 'highestScoringPlayerId', 'highestScoringPlayerInfo',
                         'mostCaptainedId', 'mostViceCaptainedId']
        deltaAvgScore = 0
        deltaHighestScore = 0
        deltaHighestScoringPlayerScore = 0
        for event in self.getStaticDataBootstrap()['events']:
            if event['finished']:
                if selectedEvent is None:
                    selectedEvent = event
                else:
                    deltaAvgScore = event['average_entry_score'] - selectedEvent['average_entry_score']
                    deltaHighestScore = event['highest_score'] - selectedEvent['highest_score']
                    deltaHighestScoringPlayerScore = event['top_element_info']['points'] - selectedEvent['top_element_info']['points']
                    selectedEvent = event
                continue

            if not event['finished']:
                break

        for field, renamedField in zip(interestedFields, renamedFields):
            latestEventData[renamedField] = selectedEvent[field]

        latestEventData['deltaAvgScore'] = deltaAvgScore
        latestEventData['deltaHighestScore'] = deltaHighestScore
        latestEventData['deltaHighestScoringPlayerScore'] = deltaHighestScoringPlayerScore

        return latestEventData

    def getFixtures(self, gwNum):
        logger.info('Collecting fixture information')

        slug = 'fixtures/?event={}'
        formattedSlug = slug.format(gwNum)
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for event status : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        return responseData

    def getEventStatus(self):
        logger.info('Collecting event status')

        slug = 'event-status/'
        formattedSlug = slug
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for event status : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        return responseData


    def getStaticTeamData(self):
        staticTeamData = {}
        for team in self.getStaticDataBootstrap()['teams']:
            staticTeamData[team['code']] = team
        return staticTeamData

    def getStaticDataBootstrap(self):
        if self._staticFPLBootstrapData is not None:
            return self._staticFPLBootstrapData

        logger.info('Collecting bootstrap static data')

        slug = 'bootstrap-static/'
        formattedSlug = slug
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for bootstrap static data : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        # logger.info('Collected response for bootstrap static data : {}'.format(responseData))
        self._staticFPLBootstrapData = responseData
        return self._staticFPLBootstrapData

    def getPlayerData(self, playerId):
        logger.info('Collecting player data for {}'.format(playerId))

        slug = 'element-summary/{}/'
        formattedSlug = slug.format(playerId)
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for player info : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        logger.info('Collected response for player info : {}'.format(responseData))
        return responseData

    def getGWPlayerPick(self, teamId, gw=1):
        logger.info('Collecting player picks for {}, {}'.format(id, gw))

        slug = 'entry/{}/event/{}/picks/'
        formattedSlug = slug.format(teamId, gw)
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for player picks : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        # logger.info('Collected response for classic league standings : {}'.format(responseData))
        return responseData

    def getClassicLeagueStandings(self, leagueId):
        if leagueId is None or leagueId == '':
            return None

        logger.info('Collecting classic league standings for {}'.format(leagueId))

        slug = 'leagues-classic/{}/standings/'
        formattedSlug = slug.format(leagueId)
        completedUrl = self.getCompleteUrl(formattedSlug)
        logger.info('Request for classic league standings : {}'.format(completedUrl))

        r = requests.get(completedUrl)
        responseData = r.json()
        logger.info('Collected response for classic league standings : {}'.format(responseData))
        return responseData

if __name__ == '__main__':
    o = OfficialFPLApi()
    o.getClassicLeagueStandings(854530)
    o.getStaticDataBootstrap()


