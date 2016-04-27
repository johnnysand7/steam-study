import pandas as pd


class CleanData(object):
    """
    Class to clean up a data frame directly
    from json or MongoDB
    """

    def __init__(self, df):
        self.df = df[(df.friends != "private") & (df.game_info != "empty")]\
                    .reset_index()
        del self.df["_id"]
        del self.df["index"]

    def _remove_columns(self):
        """
        Remove unused columns
        """
        del_columns = set(["gameextrainfo", "gameid", "gameserverip",
                           "gameserversteamid", "lobbysteamid", "loccityid",
                           "ban_status", "user_info"])
        for col in del_columns:
            try:
                del self.df[col]
            except KeyError:
                continue

    def ban_status_df(self):
        """
        Convert a df with a column of single dictionaries and
        a steamid
        Returns a df with the unpacked dictionaries
        """
        new_df = pd.DataFrame()
        for i in xrange(self.df.steamid.count()):
            self.df.ban_status[i]["steamid"] = self.df.steamid[i]
            user_df = pd.DataFrame(self.df.ban_status[i], index=[0])
            new_df = new_df.append(user_df)
        return new_df

    def user_info_df(self):
        """
        Convert a df with a column of single dictionaries and
        a steamid
        Returns a df with the unpacked dictionaries
        """
        new_df = pd.DataFrame()
        for i in xrange(self.df.steamid.count()):
            self.df.user_info[i]["steamid"] = self.df.steamid[i]
            user_df = pd.DataFrame(self.df.user_info[i], index=[0])
            new_df = new_df.append(user_df)
        return new_df

    def profile_summary_df(self):
        """
        Convert a df with a column of single dictionaries and
        a steamid
        Returns a df with the unpacked dictionaries
        """
        new_df = pd.DataFrame()
        for i in xrange(self.df.steamid.count()):
            if type(self.df.profile_summary[i]) == dict:
                profile_dict = self.df.profile_summary[i]
                profile_dict["steamid"] = int(self.df.steamid[i])
                user_df = pd.DataFrame(profile_dict, index=[0])
                new_df = new_df.append(user_df)
            else:
                self.df.profile_summary[i] = {"steamid" : self.df.steamid[i]}
                user_df = pd.DataFrame(self.df.profile_summary[i], index=[0])
                new_df = new_df.append(user_df)
        return new_df

    def merge_dfs(self, new_df):
        """
        Merge dataframes on the "steamid" column
        """
        self.df = pd.merge(self.df, new_df,
                           on='steamid')

    def build_df(self):
        """
        Call the above functions to build one dataframe
        """
        ban_status = self.ban_status_df()
        self.merge_dfs(ban_status)
        del ban_status
        user_info = self.user_info_df()
        self.merge_dfs(user_info)
        del user_info
        self._remove_columns()
        self.df.drop_duplicates("steamid", keep="first")
