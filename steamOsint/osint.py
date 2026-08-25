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
        self._targetFriends = []
        self._targetFriendsComplete = []
        self._detail = []
        self._usersFounds = []
        self._history = {"Name", "realName", "url"}
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
            self._targetFriends = hasFriend
            self.run_threads(self._targetFriends, self.friendsOfFriend)
            print(f"\n{CN}[*] Starting friend enumeration...")
            mutualFriends = self.creatingAccuracy()
            self.run_threads(mutualFriends, self.addingDetail)
            self._usersFounds = sorted(self._usersFounds,key=lambda friend: next(iter(friend.values()))["accuracy"],reverse=True)
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
        print(f"\n   {BR}[{RD}x{RS}]{RD}{RD} A friends list needs to be public.{RS}")
    def friendsOfFriend(self, user):
        mutualList = []
        try:
            requestThreads = requests.get(f"{self._friendUrl}{self._token}&steamid={user['steamid']}")
            friends = json.loads(requestThreads.content)
            if friends:
                for friendOFfriend in friends["friendslist"]["friends"]:
                    for targetFriend in self._targetFriends:
                        if friendOFfriend["steamid"] == targetFriend["steamid"]:
                            mutualList.append(targetFriend["steamid"])
            detail = self.detailFromUser(user['steamid'])
            self._targetFriendsComplete.append({
                 user['steamid']: 
                    {
                    **detail,
                    "accuracy":0, 
                    "since": self.formatDate(user.get("friend_since")),
                    "mutual": mutualList
                    }
            })
        except:
            print(f"{BR}[{RD}x{BR}]{RS}{RD} An error occurred while retrieving the friends list..{RS}")
    def showFriends(self):
        HAS = f"{BR}[{GR}+{BR}]{RS}"
        for steam in self._usersFounds:
            key = next(iter(steam))
            user = steam.get(key)
            mutualList = user.get("mutual")
            self.setAcurracy(user.get("accuracy"))
            mutualNames = self.getMutualNames(mutualList)
            print(dedent(f'''
            {HAS}{GR} Friend found{RS}
                {self.line(user,"name")}{YL} Nick        :{BR} {self.formatUser(user,"name")}
                {self.line(user,"realname")}{YL} Name        :{BR} {self.formatUser(user,"realname")}
                {self.line(user,"country")}{YL} Country     :{BR} {self.formatUser(user,"country")}
                {HAS}{YL} Friend since:{BR} {user.get("since")} MM/DD/YYYY
                {HAS}{YL} Accuracy    :{BR} {self.percentage(user)}%
                {self.line(user,"mutual")}{YL} Mutual      :{BR} [ {mutualNames} ]
                {HAS}{YL} Steam       :{BL} https://steamcommunity.com/profiles/{user["steamid"]}'''))
    def creatingAccuracy(self):
        accuracyList = []
        for cFriend in self._targetFriendsComplete:
            counting = 0
            for mutualFriend in self._targetFriendsComplete:
                steamID = next(iter(cFriend))
                key = next(iter(mutualFriend))
                if steamID in mutualFriend.get(key).get("mutual"):
                    counting +=1
                    cFriend[steamID]["accuracy"] = counting
            accuracyList.append(cFriend)
        return sorted(accuracyList,key=lambda friend: next(iter(friend.values()))["accuracy"],reverse=True)[:15]
    def detailFromUser(self, steamid):
        user =  self.checkDetail(steamid)
        try:
            if not user:
                detail = requests.get(f"{self._profileURL}{self._token}&steamids={steamid}")
                detailContent = json.loads(detail.content)
                data = detailContent["response"]["players"][0]
                info = {
                    "steamid":data.get("steamid"),
                    "name": data.get("personaname"),
                    "realname":data.get("realname"),
                    "url":data.get("url"),
                    "country":data.get("loccountrycode")

                }
                self._detail.append(info)
                return info
            return user
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
        return round((value.get("accuracy") / self._accuracy) * 100)
    def getMutualNames(self, mutualList):
        if mutualList:
            getNameFromMutualList = list(map(lambda steamUser: steamUser.get("name"), mutualList))
            return f"{BL} | {RS}".join(getNameFromMutualList)
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

    def addingDetail(self, user):
        key = next(iter(user))
        user = user.get(key)
        mutual = user.get("mutual")
        mutualDetail = []
        if mutual:
            mutualDetail = list(map(lambda user: self.detailFromUser(user), mutual))

        self._usersFounds.append({ key: {**user, "mutual": mutualDetail }})
    def checkDetail(self, steamid):
        for user in self._detail:
            if user.get("steamid") == steamid:
                return user
            return None
    def clearList(self):
        self._accuracy = 0
        self._targetFriends = []
        self._targetFriendsComplete = []
        self._detail = []
        self._usersFounds = []
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
                 print(f"\n   {BR}[{RD}x{RS}]{RD} {RD}This user is not indexed, so we can't retrieve their history.{RS}")
        except:
                print(f"\n   {BR}[{RD}x{RS}]{RD} {RD}Error while trying to retrieve the history. It may be temporarily unavailable due to maintenance.{RS}")