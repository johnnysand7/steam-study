import os
import re
import json
import requests
import time
from bs4 import BeautifulSoup
from pymongo import MongoClient


class SteamScraper(object):
    """
    Class to keep track of Steam APIs.
    Ideally will return usful info.
    Pass in the Steam API key to get going!
    """
    def __init__(self):
        """
        Initialize with the Steam API key and Game ID (if needed)
        """
        self.key = os.environ["ACCESS_STEAM"]
        self.uid = None
        self.player_dict = {}
        self.db = None
        self.s_code = None
        self.friend_response = None

    def user_id(self, uid):
        """
        Resets self.uid to a new 17-digit user ID
        Also checks the GetFriendList API for status code 200 (public user)
        or 401 (private user)
        """
        self.uid = uid
        url = "http://api.steampowered.com/ISteamUser/GetFriendList\
               /v0001/?key=" + self.key + "&steamid=" + self.uid +\
              "&relationship=all"
        try:
            response = requests.get(url)
        except requests.ConnectionError:
            time.sleep(10)
            response = requests.get(url)
        self.s_code = str(response.status_code).startswith("2")
        self.friend_response = response

    def mongodb_connection(self):
        """
        Connect to MongoDB 'steam'
        """
        client = MongoClient()
        self.db = client.steam

    def insert_document(self):
        """
        Insert a player dictionary document in db_name of MongoDB
        """
        self.db.test.insert_one(self.player_dict)

    def get_bans(self):
        """
        Access a user's ban status with Steams API
        """
        url = "http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key=" +\
              self.key + "&steamids=" + self.uid
        try:
            response = requests.get(url)
        except requests.ConnectionError:
            time.sleep(10)
            response = requests.get(url)
        self.s_code = str(response.status_code).startswith("2")
        ban = response.json()["players"][0]
        desired_keys = set(ban.keys()) - set(["SteamId"])
        return {k: ban[k] for k in desired_keys}

    def get_user_info(self):
        """
        Get user information with Steam's API
        """
        url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries\
               /v0002/?key=" + self.key + "&steamids=" + self.uid
        try:
            user = requests.get(url).json()["response"]["players"][0]
        except requests.ConnectionError:
            time.sleep(10)
            user = requests.get(url).json()["response"]["players"][0]
        desired_keys = set(user.keys()) - set(["steamid", "profileurl",
                                               "personastateflags", "avatar",
                                               "avatarmedium", "steamid"])
        return {k: user[k] for k in desired_keys}

    def get_friends(self):
        """
        Get the friends list of users
        """
        friends = self.friend_response.json()["friendslist"]["friends"]
        excluding = set(["relationship"])
        return [{k: friend[k] for k in (set(friend.keys()) - excluding)}
                for friend in friends]

    def get_game_info(self):
        """
        Get the game information for a user with the Steam API
        """
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames\
              /v0001/?key=" + self.key + "&steamid=" + self.uid +\
              "&include_appinfo=1&include_played_free_games=1&format=json"
        try:
            games = requests.get(url).json()["response"]
        except requests.ConnectionError:
            time.sleep(10)
            games = requests.get(url).json()["response"]
        if "games" in games.keys():
            games = games["games"]
            for i, game in enumerate(games):
                desired_keys = set(game.keys()) -\
                                   set(["has_community_visible_stats",
                                        "img_icon_url", "img_logo_url"])
                game = {k: game[k] for k in desired_keys}
                games[i] = game
            return games
        else:
            return None

    def get_player_achievments(self, appid):
        """
        Given a player ID and appid, return a list of achievments
        """
        url = "http://api.steampowered.com/ISteamUserStats/\
              GetPlayerAchievements/v0001/?appid=" + appid + "&key=" +\
              self.key + "&steamid=" + self.uid
        playerstats = json.loads(urllib2.urlopen(url).read())["playerstats"]
        return {k: playerstats[k] for k in ("achievements", "gameName")}

    def scrape_profile(self):
        """
        Look at a user's community profile
        Maybe include '?xml=1' at the end of the url?
        """
        url = "http://steamcommunity.com/profiles/"+self.uid
        try:
            text = requests.get(url).text
        except requests.ConnectionError:
            time.sleep(10)
            text = requests.get(url).text
        rm_delims = re.sub(r"[\t\r\n]+", r" ", text)
        rm_breaks = re.sub(r"\<br\>+", r" ", rm_delims).strip()
        soup = BeautifulSoup(text, "lxml")
        try:
            summary = " ".join(re.findall(r"[0-9a-zA-Z\.\,\!\?\'\"\$]+",
                                          " ".join([list(link.stripped_strings)
                                                    for link in
                                                    soup.find_all("div",
                                                    "profile_header_summary")]
                                                   [0][:-2])))
            level = soup.select("span.friendPlayerLevelNum")[0].text
            profile_links = soup.find_all("div", "profile_count_link")
            profile_dict = [{list(link.stripped_strings)
                            [0]:list(link.stripped_strings)
                            [-1]} for link in profile_links]
            profile_dict = dict(i.items()[0] for i in profile_dict)
            profile_dict["level"] = level
            profile_dict["summary"] = summary

            return profile_dict
        except IndexError:
            return None

    def build_dict(self):
        """
        Reference above functions to build a player info dictionary
        Eventually do a self.id kinda thang, naw mean?
        """
        self.player_dict = None
        self.player_dict = {}

        if self.s_code:
            self.player_dict["ban_status"] = self.get_bans()
            self.player_dict["friends"] = self.get_friends()
            self.player_dict["game_info"] = self.get_game_info()
            self.player_dict["user_info"] = self.get_user_info()
            self.player_dict["profile_summary"] = self.scrape_profile()
            self.player_dict["steamid"] = self.uid
        else:
            self.player_dict["ban_status"] = self.get_bans()
            self.player_dict["friends"] = "private"
            self.player_dict["game_info"] = "private"
            self.player_dict["user_info"] = self.get_user_info()
            self.player_dict["profile_summary"] = "private"
            self.player_dict["steamid"] = self.uid
