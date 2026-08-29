from .colors import *
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from textwrap import dedent
from pathlib import Path
from .steamInfo import SteamInfo
import requests
import json
import os
BASE_DIR = Path(__file__).resolve().parent

class Osint:
    def __init__(self):
        self._token = None
        self._accuracy = 0
        self._targetFriends = {}
        self._userDetail = {}
        self._path = BASE_DIR / "settings" / "steamKey.txt"
        self._steamKey = 'https://steamcommunity.com/dev/apikey'
        self._friendUrl = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
        self._profileURL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key="
        self._profileDetail = "https://api.steampowered.com/ISteamUser/ResolveVanityURL/v0001/?key="
        self.getToken()
        self.steamInfo = SteamInfo()
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
    def scanProfile(self, steamID):
        user = self.verifySteamID(steamID)
        self.crawlingProfile(user)
        hasFriend = self.get_friends(user)
        if hasFriend:
            self.addTargetFriends(hasFriend)
            self.run_threads(self._targetFriends.items(), self.friendsOfFriend)
            print(f"\n{CN}[*] Starting friend enumeration...")
            self.creatingAccuracy()
            self.addingDetailToMutual()
            self.addingDetailToCurrentUser()
            return
        print(f"\n   {BR}[{RD}x{RS}]{RD}{RD} A friends list needs to be public.{RS}")
    def verifySteamID (self, user):
        if "7656119" == user[0:7]:
            return user
        request =  requests.get(f"{self._profileDetail}{self._token}&vanityurl={user}")
        userData = json.loads(request.content)
        if userData:
            return userData.get("response").get("steamid")
    def addTargetFriends(self, friends):
       self._targetFriends = {
        user["steamid"]: {
        "friend_since": user["friend_since"]
    }
    for user in friends
}
    def get_friends(self, steamID):
        try:
            scanProfile = f'{self._friendUrl}{self._token}&steamid={steamID}'
            request = requests.get(scanProfile)
            friends = request.json()
            if friends:
                return friends["friendslist"]["friends"]
        except:
            print("o erro está aqui fi")
            return []
    def friendsOfFriend(self, steamid, friend):
        since = friend["friend_since"]
        mutualList = []
        try:
            friends = self.get_friends(steamid)
            if friends:
                for friendOFfriend in friends:
                    if friendOFfriend["steamid"] in self._targetFriends:
                        mutualList.append(friendOFfriend["steamid"])
            self._targetFriends[steamid] = {
                "accuracy":0, 
                "since": self.formatDate(since),
                "mutual": mutualList
                }
        except Exception as e:
            print(f"{type(e).__name__}: {e}")
            print(f"\n   {BR}[{RD}x{RS}]{RD} An error occurred while retrieving the friends list..{RS}")
    def showFriends(self):
        HAS = f"{BR}[{GR}+{BR}]{RS}"
        for steam in self._targetFriends.values():
            mutualList = steam.get("mutual")
            self.setAcurracy(steam.get("accuracy"))
            mutualNames = self.getMutualNames(mutualList)
            print(dedent(f'''
            {HAS}{GR} Friend found{RS}
                {self.line(steam,"name")}{YL} Nick        :{BR} {self.formatUser(steam,"name")}
                {self.line(steam,"realname")}{YL} Name        :{BR} {self.formatUser(steam,"realname")}
                {self.line(steam,"country")}{YL} Country     :{BR} {self.formatUser(steam,"country")}
                {HAS}{YL} Friend since:{BR} {steam["since"]} MM/DD/YYYY
                {HAS}{YL} Accuracy    :{BR} {self.percentage(steam)}%
                {self.line(steam,"mutual")}{YL} Mutual      :{BR} [ {mutualNames} ]
                {HAS}{YL} Steam       :{BL} {steam["url"]}'''))
    def creatingAccuracy(self):
        for steamIDFriend in self._targetFriends:
            counting = 0
            for mutual in self._targetFriends:
                if steamIDFriend in self._targetFriends.get(mutual).get("mutual"):
                    counting +=1
            self._targetFriends[steamIDFriend]["accuracy"] = counting
        self._targetFriends = dict(sorted(self._targetFriends.items(),key=lambda item: item[1].get("accuracy", 0),reverse=True)[:10])
    def detailFromUser(self, steamid):
        try:
            detail = requests.get(f"{self._profileURL}{self._token}&steamids={steamid}")
            detailContent = detail.json()
            players = detailContent.get("response", {}).get("players", [])
            data = players[0]
            info = {
                "steamid":data.get("steamid"),
                "name": data.get("personaname"),
                "realname":data.get("realname"),
                "url":data.get("profileurl"),
                "country":data.get("loccountrycode")

                }
            return info
        except:
            print(f"\n   {BR}[{RD}x{RS}]{RD} failure to seek details about mutual friends.{RS}")
    def run_threads(self, friend_list, func):
        with ThreadPoolExecutor(max_workers=20) as executor:
            for friend in friend_list:
                if isinstance(friend, tuple):
                    executor.submit(func, *friend)
                else:
                    executor.submit(func, friend)
    def getTotalPerc(self, friendList):
        for mutualFriend in friendList:
            if mutualFriend["accuracy"] > self._total:
                self._total =  mutualFriend["accuracy"]
    def percentage(self, value):
        return round((value.get("accuracy") / self._accuracy) * 100)
    def getMutualNames(self, mutualList):
        if mutualList:
            nameList = list(map(lambda user: user.get("name"), mutualList.values()))
            return f"{BL} | {RS}".join(nameList)
        return f"{RD}Private friends list.{RS}"
    def setAcurracy(self, value):
        if value > self._accuracy:
            self._accuracy = value
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

    def addingDetailToMutual(self):
        for userID, user in self._targetFriends.items():
            mutual = user.get("mutual")
            detailList = {}
            for steamid in mutual:
                if steamid in self._userDetail and steamid in self._targetFriends:
                    detailList[steamid] = self._userDetail[steamid]
                elif steamid in self._targetFriends:
                    detail = self.detailFromUser(steamid)
                    detailList[steamid] = detail
                    self._userDetail[steamid] = detail
            self._targetFriends[userID]["mutual"] = detailList
    def addingDetailToCurrentUser(self):
        for steamid, details in self._targetFriends.items():
            if steamid in self._userDetail:
                self._targetFriends[steamid] = {**self._userDetail[steamid], **details}
            else:
                info = self.detailFromUser(steamid)
                self._targetFriends[steamid] = {**info, **details}
    def clearList(self):
        self._accuracy = 0
        self._targetFriends = {}
    def crawlingProfile(self, steamId):
        try:
            data = self.steamInfo.run(steamId)
            if data.get("name"):
                HAS = f"{BR}[{GR}+{BR}]{RS}"
                print(f"\n{HAS}{GR} Target Persona Name History{RS} MM/DD/YYYY")
                for name in data.get("name"):
                    print(f"  * {YL}{name.get('Name')}  {BR}{self.formatDate(name.get('Timestamp'))}")
                print(f"\n{HAS}{GR} Target Real Name History{RS} MM/DD/YYYY")
                for name in data.get("realName"):
                    print(f"  * {YL}{name.get('Name')} : {BR}{self.formatDate(name.get('Timestamp'))}")
                print(f"\n{HAS}{GR} Target Url History{RS} MM/DD/YYYY")
                for url in data.get("url"):
                    print(f"  * {BL}{url.get('URL')} : {BR}{self.formatDate(name.get('Timestamp'))}")
            else:
                 print(f"\n   {BR}[{RD}x{RS}]{RD} This user is not indexed, so we can't retrieve their history.{RS}")
        except:
                print(f"\n   {BR}[{RD}x{RS}]{RD} Error while trying to retrieve the history. It may be temporarily unavailable due to maintenance.{RS}")