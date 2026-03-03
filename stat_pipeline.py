import pandas as pd
import openpyxl
import os
import json
from datetime import datetime

def main():
    path = r"C:\\Users\\andre\\OneDrive\\Desktop\\BBL_SEASON_2\\BBL Season 2 Stats.xlsx" 
    df_players = pd.read_excel(path, sheet_name="Season Stats")
    df_teams = pd.read_excel(path, sheet_name="Team Stats")

    os.makedirs("data", exist_ok=True)

    df_players.to_json("data/season_stats.json", orient="records", indent=4)
    df_teams.to_json("data/team_stats.json", orient="records", indent=4)

    
    
    with open("data/last_updated.json", "w") as f:
        json.dump({"last_updated": datetime.now().strftime("%Y-%m-%d")}, f, indent=4)

if __name__ == "__main__":
    main()