import cPickle
import operator
import os
import re
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup


class CollectNewUser():

    def __init__(self, popular_games):
        self.popular_games = popular_games
        self.uid = self.determine_user_input()
        self.key = os.environ["ACCESS_STEAM"]
        self.bans = None
        self.user = None
        self.friends = None

    def determine_user_input(self):
        user_input = raw_input("Paste your Steam community profile url here: ")
        if len(user_input) == 17:
            if user_input.isdigit():
                return user_input
            else:
                return "Maybe you tried your 17-digt Steam ID,\
                        which was not recognized"

        elif "steamcommunity.com" not in user_input:
            return "Must be a Steam Community URL!"

        else:
            try:
                response = requests.get(user_input)
                uid = re.findall(r"[0-9]{17}", response.text)[0]
                if len(uid) != 17:
                    return "Url did not work"
                return uid

            except IndexError:
                return "Could not find your profile."

            except requests.ConnectionError:
                return "Could not find your profile."

    def get_user_info(self):
        """
        For my model, I need the new user's:
          personastate
          location (eventually)
          profile avatar url (eventually)
          other things?
        """
        url = "http://api.steampowered.com/ISteamUser/GetPlayerSummaries"\
              + "/v0002/?key=" + self.key + "&steamids=" + self.uid
        user = requests.get(url).json()["response"]["players"][0]
        if user["communityvisibilitystate"] == 1:
            return None
        self.user = {k: user[k] for k in ("personastate", "timecreated",
                                          "steamid")}

    def get_bans(self):
        url = "http://api.steampowered.com/ISteamUser/GetPlayerBans"\
              + "/v1/?key=" + self.key + "&steamids=" + self.uid
        response = requests.get(url)
        self.s_code = str(response.status_code).startswith("2")
        ban = response.json()["players"][0]
        desired_keys = set(ban.keys()) - set(["SteamId", "DaysSinceLastBan",
                                              "EconomyBan", "NumberOfGameBans",
                                              "NumberOfVACBans"])
        self.bans = {k: ban[k] for k in desired_keys}

    def get_friends(self):
        url = "http://api.steampowered.com/ISteamUser/GetFriendList/v0001\
              /?key=" + self.key + "&steamid=" + self.uid + "&relationship=all"
        response = requests.get(url)
        if str(response.status_code).startswith("2"):
            friends = response.json()["friendslist"]["friends"]
            excluding = set(["relationship"])
            self.friends = len(friends)
        else:
            return None

    def get_game_info(self):
        url = "http://api.steampowered.com/IPlayerService/GetOwnedGames"\
              + "/v0001/?key=" + self.key + "&steamid=" + self.uid + \
              "&include_appinfo=1&include_played_free_games=1&format=json"
        response = requests.get(url)
        if str(response.status_code).startswith("2"):
            try:
                games = response.json()["response"]["games"]
                for i, game in enumerate(games):
                    desired_keys = set(game.keys()) -\
                                   set(["has_community_visible_stats",
                                        "img_icon_url", "img_logo_url"])
                    if "playtime_2weeks" in desired_keys:
                        game = {k: game[k] for k in desired_keys}
                        games[i] = game
                    else:
                        game = {k: game[k] for k in desired_keys}
                        game[u"playtime_2weeks"] = 0
                        games[i] = game
                return games
            except KeyError:
                return None
        else:
            return None

    def game_user_frames(self):
        game_df = pd.DataFrame(self.get_game_info())
        owned, played = len(game_df), len(game_df[game_df["playtime_forever"
                                                          ] != 0])
        game_df = game_df[game_df["appid"].isin(self.popular_games)]
        game_df["rating"] = pd.cut(game_df["playtime_forever"],
                                   bins=[-1, 60, 120, 180, 240, 300,
                                         10e10],
                                   labels=[0, 1, 2, 3, 4, 5]).astype(int)
        game_df["user_id"] = ((self.uid+" ") * len(game_df)).split()
        game_df["item_id"] = game_df["appid"].astype(int)
        game_df = game_df[["item_id", "rating", "user_id"]]
        game_df = graphlab.SFrame(game_df)
        user_dict = dict(self.bans.items() + self.user.items() +
                         [("num_friends", self.friends),
                         ("num_played", played),
                         ("num_games", owned)])
        user_df = pd.DataFrame([user_dict])
        user_df["timecreated"] = int(round((time.time() -
                                     user_df["timecreated"]) /
                                     (3600 * 24 * 365), 2))
        user_df.rename(columns={"steamid": "user_id"}, inplace=True)
        user_df = graphlab.SFrame(user_df)
        return user_df, game_df


if __name__ == "__main__":
    with open("../data/top_appids.csv", "rb") as f:
        game_ids = f.read()
    game_ids = game_ids.replace("\n", "").split(",")[2:]
