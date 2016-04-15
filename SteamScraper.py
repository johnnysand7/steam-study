import os, re, json, requests, time
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
        Also checks the GetFriendList API for a status code of 200 (public user)
        or 401 (private user)
        """
        self.uid = uid
        url = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='\
               +self.key+'&steamid='+self.uid+'&relationship=all'
        #friends = json.loads(urllib2.urlopen(url).read())['friendslist']['friends']
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


    def insert_document(self, collection_name="users"):
        """
        Insert a player dictionary document in db_name of MongoDB
        """
        #name = collection_name
        self.db.test.insert_one(self.player_dict)


    def get_bans(self):
        """
        INPUTS:
          self - .key: API key
                 .uid: 17-digit Steam ID string, up to 100 comma-delimited
        OUTPUTS:
          Dictionary:
            {u'CommunityBanned': False,
             u'DaysSinceLastBan': 0,
             u'EconomyBan': u'none',
             u'NumberOfGameBans': 0,
             u'NumberOfVACBans': 0,
             u'SteamId': u'76561197967398882', UPDATE - removed
             u'VACBanned': False} VAC is for online gaming

        Looks at the 17-digit ID's ban history (up to 100 comma-delimited IDs)
        """
        url = "http://api.steampowered.com/ISteamUser/GetPlayerBans/v1/?key="+self.key+"&steamids="+self.uid
        #ban = json.loads(urllib2.urlopen(url).read())['players'][0]
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
        INPUTS:
          self - .key: API key
                 .uid: 17-digit Steam ID string, up to 100 comma-delimited
        OUTPUTS:
          Dictionary:
          {u'avatar': u'https://steamcdn-a.akamaihd.net/.../jpg', # REMOVED
           u'avatarfull': u'https://steamcdn-a.akamaihd.net/.../full.jpg',
           u'avatarmedium': u'https://steamcdn-a.akamaihd.net/.../medium.jpg', # REMOVED
           u'communityvisibilitystate': 3,   # 1 - private profile, 3 - public profile
           u'lastlogoff': 1460189153,  # epoch time
           u'loccountrycode': u'VA',    # May need to look into how to pull that out. Some also have "locstatecode"
           u'personaname': u'Deck Gumby',
           u'personastate': 0,      # 0 - Offline, 1 - Online, 2 - Busy, 3 - Away, 4 - Snooze, 5 - looking to trade, 6 - looking to play.
           u'personastateflags': 0, #
           u'primaryclanid': u'103582791432291036',
           u'profilestate': 1,      # If set, indicates the user has a community profile configured (will be set to '1')
           u'profileurl': u'http://steamcommunity.com/id/deckgumby/',
           u'realname': u'Ken Tucky',
           u'steamid': u'76561197967398882',
           u'timecreated': 1089486992}    # epoch time
        For a user or users (up to 100 comma-delimited),
        return some basic user information
        """
        url = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='\
               +self.key+'&steamids='+self.uid
        #user = json.loads(urllib2.urlopen(url).read())['response']['players'][0]
        try:
            user = requests.get(url).json()["response"]["players"][0]
        except requests.ConnectionError:
            time.sleep(10)
            user = requests.get(url).json()["response"]["players"][0]
        desired_keys = set(user.keys()) - set(["steamid", "profileurl", "personastateflags", "avatar", "avatarmedium", "steamid"])
        return {k: user[k] for k in desired_keys}


    def get_friends(self):
        """
        INPUTS:
          self - .key: API key
                 .uid: 17-digit Steam ID
        OUTPUT:
          List of dictionaries, e.g.,
            {u'friend_since': 0,
             u'relationship': u'friend', UPDATE - now removes this field
             u'steamid': u'76561197960559382'}
        Starting with a single user ID, return their friends
        If public, only return users who have public profiles
        """
        #url = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='\
        #       +self.key+'&steamid='+self.uid+'&relationship=all'
        #friends = json.loads(urllib2.urlopen(url).read())['friendslist']['friends']
        #response = requests.get(url)
        #self.s_code = str(response.status_code).startswith("2")
        friends = self.friend_response.json()["friendslist"]["friends"]
        excluding = set(["relationship"])
        return [{k: friend[k] for k in (set(friend.keys()) - excluding)} for friend in friends]


    def get_game_info(self):
        """
        INPUTS:
          self - .key: API key
                 .uid: 17-digit Steam ID
        OUTPUT:
          List of dictionaries, e.g.,
            {u'appid': 10,
             u'has_community_visible_stats': True,
             u'img_icon_url': u'6b0312cda02f5f777efa2f3318c307ff9acafbb5', UPDATE - removed
             u'img_logo_url': u'af890f848dd606ac2fd4415de3c3f5e7a66fcb9f', UPDATE - removed
             u'name': u'Counter-Strike',
             u'playtime_forever': 0, in minutes
             u'playtime_2weeks': 0} in minutes UPDATE - added whether played in two weeks or not

        Get owned game information for a give user
        Returns a list of dictionaries
        """
        url =  "http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key="\
                +self.key+"&steamid="+self.uid+"&include_appinfo=1\
                &include_played_free_games=1&format=json"
        #games = json.loads(urllib2.urlopen(url).read())["response"]["games"]
        try:
            games = requests.get(url).json()["response"]
        except requests.ConnectionError:
            time.sleep(10)
            games = requests.get(url).json()["response"]
        if "games" in games.keys():
            games = games["games"]
            for i, game in enumerate(games):
                desired_keys = set(game.keys()) - set(["has_community_visible_stats", "img_icon_url", "img_logo_url"])
                #if "playtime_2weeks" in desired_keys:
                game = {k: game[k] for k in desired_keys}
                games[i] = game
                #else:
                    #game = {k: game[k] for k in desired_keys}
                    #game[u"playtime_2weeks"] = 0
                    #games[i] = game
            return games
        else:
            return "empty"


    def get_player_achievments(self, appid):
        """
        Given a player ID and appid, return a list of achievments
        """
        url = "http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid="+appid+"&key="+self.key+"&steamid="+self.uid
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
        ### profile summary statement
        try:
            summary = " ".join(re.findall(r"[0-9a-zA-Z\.\,\!\?\'\"\$]+", " ".join(\
                                                  [list(link.stripped_strings) for link in soup.find_all(\
                                                  "div", "profile_header_summary")][0][:-2])))
            #summary = " ".join(re.findall(r"[0-9a-zA-Z\.\,\!\?\'\"\$]+", " ".join(\
            #          list(soup.select("div.profile_summary")[0].stripped_strings))))
            level = soup.select("span.friendPlayerLevelNum")[0].text

            #profile_items = soup.find_all("div", "profile_count_link")
            #profile_items = [{list(link.stripped_strings)[0]:list(link.stripped_strings)[-1]} for link in profile_items]
            #profile_items = dict(i.items()[0] for i in profile_dict)
            profile_links = soup.find_all("div", "profile_count_link")
            profile_dict = [{list(link.stripped_strings)[0]:list(\
                           link.stripped_strings)[-1]} for link in profile_links]
            profile_dict = dict(i.items()[0] for i in profile_dict)
            profile_dict["level"] = level
            profile_dict["summary"] = summary


            return profile_dict#, profile_items
        except IndexError:
            return "empty"



        #pass


    def game_info(self, appid):
        """
        Get the information for a given game / appid
        """
        url = ""
        pass


    def get_global_achievements(self, appid):
        """
        Get the global achievement stats, kinda intersting
        Currently returns a LIST of achievement name / global completion percentages; maybe average one number?
        """
        url = "http://api.steampowered.com/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/?gameid="+appid+"&format=json"
        return json.loads(urllib2.urlopen(url).read())["achievementpercentages"]["achievements"]


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


        #self.player_dict["achievments"] = self.get_player_achievments() needs a specific game


    def check_out(self):
        """
        Returns a built-up dictionary
        """
        return self.player_dict
