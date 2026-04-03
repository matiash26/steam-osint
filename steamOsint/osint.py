from .colors import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from textwrap import dedent
from pathlib import Path
from .getInfo import GetInfo
import requests
import json
import os
BASE_DIR = Path(__file__).resolve().parent

class Osint:
    def __init__(self):
        self._total = 0
        self._token = None
        self._targetFriends = []
        self._mutualFriend = []
        self._mutualDetails = []
        self._path = BASE_DIR / "settings" / "steamKey.txt"
        self._steamKey = 'https://steamcommunity.com/dev/apikey'
        self._friendUrl = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
        self._profileURL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="
        self._profileDetail = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key="
        self.getToken()
        self.profileCrawling = GetInfo()
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
    def scanProfile(self, steamID):
        user = self.verifySteamID(steamID)
        hasFriend = self.get_friends(user)
        self.crawlingProfile(user)
        if hasFriend:
            self._targetFriends = hasFriend
            self.run_threads(self._targetFriends,self.friendsOfFriend)
            print(f"\n{CN}[*] Starting friend enumeration...")
            mutualFriends = self.creatingAccuracy()
            self.run_threads(mutualFriends,self.detailFromUser)
            self._mutualDetails = sorted(self._mutualDetails, key=lambda friend: friend["accuracy"], reverse=True)
    def verifySteamID (self, user):
        if "7656119" == user[0:7]:
            return user
        request =  requests.get(f"{self._profileDetail}{self._token}&vanityurl={user}")
        userData = json.loads(request.content)
        if userData:
            return userData.get("response").get("steamid")
    def get_friends(self, steamID):
        scanProfile = f'{self._friendUrl}{self._token}&steamid={steamID}'
        request = requests.get(scanProfile)
        friends = json.loads(request.content)
        if friends:
            return friends["friendslist"]["friends"]
        print(f"    {BR}[{RD}!{RS}]{RD} {RD}A friends list needs to be public.{RS}")
    def friendsOfFriend(self, steamURL):
        try:
            requestThreads = requests.get(f"{self._friendUrl}{self._token}&steamid={steamURL['steamid']}")
            friends = json.loads(requestThreads.content)
            if friends:
                for friendOFfriend in friends["friendslist"]["friends"]:
                    for targetFriend in self._targetFriends:
                        if(friendOFfriend["steamid"] == targetFriend["steamid"]):
                            self._mutualFriend.append(targetFriend["steamid"])
        except:
            print(f"{BR}[{RD}x{BR}]{RS}{RD} An error occurred while retrieving the friends list..{RS}")
    def showFriends(self):
        HAS = f"{BR}[{GR}+{BR}]{RS}"
        for mutual in self._mutualDetails:
            print(dedent(f'''
            {HAS}{GR} Friend found{RS}
                {self.line(mutual,"personaname")}{YL} Nick        :{BR} {self.formatUser(mutual,"personaname")}
                {self.line(mutual,"realname")}{YL} Name        :{BR} {self.formatUser(mutual,"realname")}
                {self.line(mutual,"loccountrycode")}{YL} Country     :{BR} {self.formatUser(mutual,"loccountrycode")}
                {HAS}{YL} Friend since:{BR} {mutual.get("since")} MM/DD/YYYY
                {HAS}{YL} Accuracy    :{BR} {self.percentage(mutual)}%
                {HAS}{YL} Steam       :{BL} https://steamcommunity.com/profiles/{mutual["steamid"]}'''))
    def creatingAccuracy(self):
        mutual = []
        for Tfriend in self._targetFriends:
            if(Tfriend["steamid"] in self._mutualFriend):
                accuracy = self._mutualFriend.count(Tfriend.get("steamid"))
                since = self.formatDate(Tfriend.get("friend_since"))
                mutual.append({
                "steamid":f"{Tfriend.get('steamid')}", "accuracy": accuracy, "since": since})
                if(accuracy > self._total):
                    self._total = accuracy
        sortedFriend = sorted(mutual, key=lambda friend: friend["accuracy"], reverse=True)[:15]
        return sortedFriend
    def detailFromUser(self, user):
        try:
            detail = requests.get(f"{self._profileURL}{self._token}&steamids={user['steamid']}")
            detailContent = json.loads(detail.content)
            self._mutualDetails.append({**user,**detailContent["response"]["players"][0]})
        except:
            print(F"{BR}[{RD}!{RS}]{RD} failure to seek details about mutual friends {RS}")
    def run_threads(self, friend_list, func):
        with ThreadPoolExecutor(max_workers=10) as executor:
            for friend in friend_list:
                executor.submit(func,friend)
    def getTotalPerc(self, friendList):
        for mutualFriend in friendList:
            if mutualFriend["accuracy"] > self._total:
                self._total =  mutualFriend["accuracy"]
    def percentage(self, value):
        return round((value.get("accuracy") / self._total) * 100)
    def formatDate(self,timestamp):
        if timestamp:
            since = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            return since.strftime("%m/%d/%Y %H:%M:%S")
    def formatUser(self, user, key):
        return user.get(key) if user.get(key) else f'{RD}x{RS}'
    def line(self, user,key):
        return f"{BR}[{GR}+{BR}]{RS}" if user.get(key) else f"{BR}[{RD}-{BR}]{RS}"
    def setToken(self, token):
        with open(self._path,"w") as tokenFile:
            tokenFile.write(token)
            self._token = token
    def getToken(self):
        if(os.path.isfile(self._path)):
            with open(self._path,"r") as token:
                content = token.read()
                self._token = content
    def clearList(self):
        self._targetFriends = []
        self._mutualFriend = []
        self._mutualDetails = []
        return
    def crawlingProfile(self, steamId):
        personaNames = self.profileCrawling.personaNameHistory(steamId)
        HAS = f"{BR}[{GR}+{BR}]{RS}"
        print(f"\n{HAS}{GR} Target Persona Name History{RS} MM/DD/YYYY")
        for name in personaNames:
            print(f"  * {YL}{name['Name']}  {BR}{self.formatDate(name['Timestamp'])}")
        realName = self.profileCrawling.realNameHistory(steamId)
        print(f"\n{HAS}{GR} Target Real Name History{RS} MM/DD/YYYY")
        for name in realName:
            print(f"  * {YL}{name['Name']} : {BR}{self.formatDate(name['Timestamp'])}")

        print(f"\n{HAS}{GR} Target Url History{RS} MM/DD/YYYY")
        urls = self.profileCrawling.UrlHistory(steamId)
        for url in urls:
            print(f"  * {BL}{url['URL']} : {BR}{self.formatDate(name['Timestamp'])}")