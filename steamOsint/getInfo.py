import requests
from bs4 import BeautifulSoup
import demjson3
class GetInfo:
    def __init__(self):
        self.url = "https://steamhistory.net/history/"
        self.steamID = ""
    def fetchInfo(self, typeOption):
        options = {"0":"0/","1":"1/","2":"2/"}
        response = requests.get(self.url + options[typeOption] + str(self.steamID))
        soup = BeautifulSoup(response.content, "html.parser")
        for script in soup.find_all("script"):
            if script.string and 'data:' in script.string:
                js = script.string
                break
        start = js.find('data:')
        start = js.find('[', start)
        count = 0
        end = start
        for i in range(start, len(js)):
            if js[i] == '[':
                count += 1
            elif js[i] == ']':
                count -= 1
            if count == 0:
                end = i + 1
                break
        raw_data = js[start:end]
        data = demjson3.decode(raw_data)
        return data[1]["data"]["entries"]
    
    def personaNameHistory(self, steamId):
        self.steamID = steamId
        return self.fetchInfo("0")
    def realNameHistory(self, steamId):
        self.steamID = steamId
        return self.fetchInfo("1")
    def UrlHistory(self, steamId):
        self.steamID = steamId
        return self.fetchInfo("2")
