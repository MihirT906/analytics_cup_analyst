import pandas as pd
from kloppy import skillcorner
import requests
import json
import numpy as np

class DataLoader:
    def __init__(self):
        pass

    def _time_to_seconds(self, time_str) -> int:
        if time_str is None:
            return 90 * 60  # 120 minutes = 7200 seconds
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s

    def load_tracking_data(self, match_id) -> pd.DataFrame:
        '''
            Load tracking data for a specific match.
        '''
        
        # Ingest tracking data from Github
        tracking_data_github_url = f'https://media.githubusercontent.com/media/SkillCorner/opendata/741bdb798b0c1835057e3fa77244c1571a00e4aa/data/matches/{match_id}/{match_id}_tracking_extrapolated.jsonl'
        raw_data=pd.read_json(tracking_data_github_url,lines=True)
        raw_df = pd.json_normalize(
            raw_data.to_dict("records"),
            "player_data",
            ["frame", "timestamp", "period", "possession", "ball_data"],
        )
        
        # Extract 'player_id' and 'group from the 'possession' dictionary
        raw_df["possession_player_id"] = raw_df["possession"].apply(
            lambda x: x.get("player_id")
        )
        raw_df["possession_group"] = raw_df["possession"].apply(lambda x: x.get("group"))
        
        # (Optional) Expand the ball_data with json_normalize
        raw_df[["ball_x", "ball_y", "ball_z", "is_detected_ball"]] = pd.json_normalize(
            raw_df.ball_data
        )
        
        # (Optional) Drop the original 'possession' column if you no longer need it
        raw_df = raw_df.drop(columns=["possession", "ball_data"])

        # Add the match_id identifier to your dataframe
        raw_df["match_id"] = match_id
        tracking_df = raw_df.copy()

        return tracking_df

    def load_meta_data(self, match_id) -> pd.DataFrame:
        '''
            Load metadata for a specific match.
        '''
        
        # Ingest metadata from Github
        meta_data_github_url=f'https://raw.githubusercontent.com/SkillCorner/opendata/741bdb798b0c1835057e3fa77244c1571a00e4aa/data/matches/{match_id}/{match_id}_match.json'
        response = requests.get(meta_data_github_url)
        raw_match_data = response.json()
        
        # The output has nested json elements. We process them
        raw_match_df = pd.json_normalize(raw_match_data, max_level=2)
        raw_match_df["home_team_side"] = raw_match_df["home_team_side"].astype(str)

        players_df = pd.json_normalize(
            raw_match_df.to_dict("records"),
            record_path="players",
            meta=[
                "home_team_score",
                "away_team_score",
                "date_time",
                "home_team_side",
                "home_team.name",
                "home_team.id",
                "away_team.name",
                "away_team.id",
            ],  # data we keep
        )
                
        # Take only players who played and create their total time
        players_df = players_df[
            ~((players_df.start_time.isna()) & (players_df.end_time.isna()))
        ]
        players_df["total_time"] = players_df["end_time"].apply(self._time_to_seconds) - players_df[
            "start_time"
        ].apply(self._time_to_seconds)

        # Create a flag for GK
        players_df["is_gk"] = players_df["player_role.acronym"] == "GK"

        # Add a flag if the given player is home or away
        players_df["match_name"] = (
            players_df["home_team.name"] + " vs " + players_df["away_team.name"]
        )


        # Add a flag if the given player is home or away
        players_df["home_away_player"] = np.where(
            players_df.team_id == players_df["home_team.id"], "Home", "Away"
        )

        # Create flag from player
        players_df["team_name"] = np.where(
            players_df.team_id == players_df["home_team.id"],
            players_df["home_team.name"],
            players_df["away_team.name"],
        )

        # Figure out sides
        players_df[["home_team_side_1st_half", "home_team_side_2nd_half"]] = (
            players_df["home_team_side"]
            .astype(str)
            .str.strip("[]")
            .str.replace("'", "")
            .str.split(", ", expand=True)
        )
        # Clean up sides
        players_df["direction_player_1st_half"] = np.where(
            players_df.home_away_player == "Home",
            players_df.home_team_side_1st_half,
            players_df.home_team_side_2nd_half,
        )
        players_df["direction_player_2nd_half"] = np.where(
            players_df.home_away_player == "Home",
            players_df.home_team_side_2nd_half,
            players_df.home_team_side_1st_half,
        )


        # Clean up and keep the columns that we want to keep about

        columns_to_keep = [
            "start_time",
            "end_time",
            "match_name",
            "date_time",
            "home_team.name",
            "away_team.name",
            "id",
            "short_name",
            "number",
            "team_id",
            "team_name",
            "player_role.position_group",
            "total_time",
            "player_role.name",
            "player_role.acronym",
            "is_gk",
            "direction_player_1st_half",
            "direction_player_2nd_half",
        ]
        players_df = players_df[columns_to_keep]
        return players_df
    
    def load_event_data(self, match_id) -> pd.DataFrame:
        '''
            Load event data for a specific match.
        '''

        event_data_github_url = f'https://raw.githubusercontent.com/SkillCorner/opendata/refs/heads/master/data/matches/{match_id}/{match_id}_dynamic_events.csv'
        raw_data=pd.read_csv(event_data_github_url)
        #raw_data = pd.read_csv('../../sandbox/sample_data/1886347_dynamic_events.csv')
        return raw_data
        
        

    def create_enriched_tracking_data(self, match_id) -> pd.DataFrame:
        '''
            Merge tracking data with metadata to create enriched tracking data.
        '''
        tracking_df = self.load_tracking_data(match_id)
        meta_df = self.load_meta_data(match_id)
        enriched_tracking_data = tracking_df.merge(
            meta_df, left_on=["player_id"], right_on=["id"]
        )
        return enriched_tracking_data
