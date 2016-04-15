from pymongo import MongoClient
import cPickle
from SteamScraper import SteamScraper
import time

def run_and_insert(uids):
    """
    Run the SteamScraper and insert into the
    MongoDB database
    """

    scraping = SteamScraper()
    scraping.mongodb_connection()

    i = 0
    t0 = time.time()

    for uid in uids:
        scraping.user_id(uid)
        scraping.build_dict()
        scraping.insert_document()

        i += 1
        if i == 100 or i == 1000 or i == 1000:
            print "{0} documents inserted in {1} minutes"\
                  .format(i, (time.time() - t0)/60)

if __name__ == "__main__":
    with open("my_project/data/public_uids.p", "rb") as uids:
        public_uids = cPickle.load(uids)

    run_and_insert(public_uids)
