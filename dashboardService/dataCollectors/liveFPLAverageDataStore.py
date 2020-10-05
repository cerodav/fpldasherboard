from datetime import datetime
from liveFPLScrape.liveFPLScrape import LiveFPLScrape

class LiveFPLAverageDataStore:

    _liveFPLScraper = LiveFPLScrape()
    _lastScrapeTimestamp = None
    _liveAverages = None
    _refreshTime = 600

    def __init__(self):
        self._liveAverages = self._liveFPLScraper.getLiveAverages()
        self._lastScrapeTimestamp = datetime.now()

    def isRefreshRequired(self):
        if self._lastScrapeTimestamp is not None :
            return (datetime.now() - self._lastScrapeTimestamp).seconds > self._refreshTime
        else :
            return True

    def getAvgData(self):
        if self._liveAverages is None or self.isRefreshRequired():
            self._liveAverages = self._liveFPLScraper.getLiveAverages()
        return self._liveAverages





