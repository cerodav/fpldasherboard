import requests
import json
from logger import logger
from bs4 import BeautifulSoup

class LiveFPLScrape:

    _baseUrl = 'https://www.livefpl.net'

    def getHomepageData(self):
        r = requests.get(self._baseUrl)
        html = r.text
        parsedHtml = BeautifulSoup(html, features="html.parser")
        return parsedHtml

    def getLiveAverages(self):
        homepageData = self.getHomepageData()
        selectedData = homepageData.body.find('table', attrs={
            'class': 'table-custom table-custom-bordered table-team-statistic'}).text
        selectedGWData = homepageData.body.find('h5', attrs={
            'class': 'heading-component-title'}).text
        gwId = selectedGWData.split()[1]
        dataPoints = selectedData.split()

        top10KAvg = dataPoints[0]
        top10KHitsAvg = dataPoints[1]
        top10KHitsInclAvg = dataPoints[3]

        overallAvg = dataPoints[7]
        overallHitsAvg = dataPoints[8]
        overallHitsInclAvg = dataPoints[10]

        response = {}
        response['top10KAvg'] = top10KAvg
        response['top10KHitsAvg'] = top10KHitsAvg.replace('(','').replace(')','')
        response['top10KHitsInclAvg'] = top10KHitsInclAvg

        response['overallAvg'] = overallAvg
        response['overallHitsAvg'] = overallHitsAvg.replace('(','').replace(')','')
        response['overallHitsInclAvg'] = overallHitsInclAvg

        response['gameweekNumber'] = gwId

        return response

if __name__ == '__main__':
    l = LiveFPLScrape()
    l.getHomepageData()


