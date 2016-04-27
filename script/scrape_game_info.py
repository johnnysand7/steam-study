import requests
import re
import time
from bs4 import BeautifulSoup
import pymongo
import pandas as pd


class ScrapeGameInfo(object):

    def __init__(self, appids):
        """
        Takes container of appids used in the Steam store
        """
        self.appids = appids
        self.db = None
        self.app = None

    def mongodb_connection(self):
        """
        Connect to Mongo Database 'steam'
        """
        client = pymongo.MongoClient()
        self.db = client.steam

    def insert_document(self, dct):
        """
        Insert a player dictionary document in db_name of MongoDB
        """
        self.db.games2.insert_one(dct)

    def scrape_store(self):
        """
        Look up a game's store page, collect information, and save to
        MongoDB
        """

        # Gets around age restrictions
        cookies = {"birthtime": "226815406"}

        # Used with all ~8,000 games and the top 526
        for app in self.appids:
            game_info_dict = {}
            self.app = app
            url = "https://store.steampowered.com/app/" + str(app)
            try:
                response = requests.get(url, cookies=cookies)
                soup = BeautifulSoup(response.text, "html.parser")
                # Release Date in the form MMM DD, YYYY
                try:
                    release_date = re.findall(r": ([a-zA-Z0-9, ]+)\n",
                                              soup.findAll("div",
                                                           "release_date")
                                              [0].text)[0]
                except IndexError:
                    release_date = re.findall(r": ([a-zA-Z0-9, ]+)\n",
                                              soup.findAll("div",
                                                           "release_date")
                                              [0].text)
                # Community review of game
                reviews = soup.find_all("div",
                                        "block responsive_apppage_reviewblock")
                try:
                    review_num = re.findall(r"([0-9]+)\/", reviews[0].text)[0]
                except IndexError:
                    reviews = ''.join(list(
                                      soup.find_all("div",
                                                    "user_reviews_summary_row")
                                      [0].stripped_strings))
                    review_num = re.findall(r"([0-9]+)%",
                                            reviews)[0]

                # Overwhelmingly Negative to Overwhelmingly Positive
                review_status = soup.find_all("span",
                                              "game_review_summary")[0].text
                # Community Genre Tags
                genre = list(soup.find_all("div", "glance_tags popular_tags")
                             [0].stripped_strings)[:-1]
                # Current price of the game
                try:
                    price = re.findall(r"[0-9\.]+",
                                       soup.find_all("div", "game_purchase_price\
                                                     price")[0].text)[-1]
                except IndexError:
                    price = "0"
                game_info_dict["appid"] = app
                game_info_dict["genres"] = genre
                game_info_dict["release_year"] = release_date
                game_info_dict["reviews"] = review_status
                game_info_dict["price"] = price
                self.insert_document(game_info_dict)

            except requests.ConnectionError:
                time.sleep(10)
                response = requests.get(url, cookies=cookies)
                soup = BeautifulSoup(response.text, "html.parser")
                # Release Date in the form MMM DD, YYYY
                try:
                    release_date = re.findall(r": ([a-zA-Z0-9, ]+)\n",
                                              soup.findAll("div",
                                                           "release_date")
                                              [0].text)[0]
                except IndexError:
                    release_date = re.findall(r": ([a-zA-Z0-9, ]+)\n",
                                              soup.findAll("div",
                                                           "release_date")
                                              [0].text)
                # Community review of game
                reviews = soup.find_all("div",
                                        "block responsive_apppage_reviewblock")
                try:
                    review_num = re.findall(r"([0-9]+)\/", reviews[0].text)[0]
                except IndexError:
                    reviews = ''.join(list(
                                      soup.find_all("div",
                                                    "user_reviews_summary_row")
                                      [0].stripped_strings))
                    review_num = re.findall(r"([0-9]+)%",
                                            reviews)[0]

                # Overwhelmingly Negative to Overwhelmingly Positive
                review_status = soup.find_all("span",
                                              "game_review_summary")[0].text
                # Community Genre Tags
                genre = list(soup.find_all("div", "glance_tags popular_tags")
                             [0].stripped_strings)[:-1]
                # Current price of the game
                try:
                    price = re.findall(r"[0-9\.]+",
                                       soup.find_all("div", "game_purchase_price\
                                                     price")[0].text)[-1]
                except IndexError:
                    price = "0"
                game_info_dict["appid"] = app
                game_info_dict["genres"] = genre
                game_info_dict["release_year"] = release_date
                game_info_dict["reviews"] = review_status
                game_info_dict["price"] = price
                self.insert_document(game_info_dict)

            except (ValueError, IndexError):
                continue


if __name__ == "__main__":
    with open("../data/top_appids.csv", "rb") as f:
        game_ids = f.read()
    game_ids = game_ids.replace("\n", "").split(",")[2:]

    collect_games = ScrapeGameInfo(game_ids)
    collect_games.mongodb_connection()
    collect_games.scrape_store()
