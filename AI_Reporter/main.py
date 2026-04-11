from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import pandas as pd
from prompts import reporter_system_prompt, reporter_content_prompt, hot_take_content_prompt, hot_take_system_prompt
import argparse

def process_data(current_week):
    game_logs = pd.read_excel("C:\\Users\\andre\\BBL_Stats_DATA\\BBL Season 2 Stats.xlsx",sheet_name="Game Logs")
    game_logs = game_logs.dropna()

    #Makes dataframe of only stats from past weeks
    past_game_logs = game_logs[game_logs["Week"] < current_week ]
    current_week_log = game_logs[game_logs["Week"] == current_week]
    player_averages = past_game_logs.groupby("Name",sort=False)[["PTS", "FGA", "FGM", "3PA", "3PM", "REB", "AST", "STL", "BLK"]].mean().reset_index()

    #Makes string out of player averages

    lines = []
    for _, row in player_averages.iterrows():
        line = f"{row['Name']} averages {row['PTS']:.1f} points, {row['REB']:.1f} rebounds, {row['AST']:.1f} assists, {row['STL']:.1f} steals, and {row['BLK']:.1f} blocks"
        lines.append(line)
    averages_string = "\n".join(lines) 

    #Makes string out of player stats for the current week
    lines = []
    for _, row in current_week_log.iterrows():
        line = f"{row['Name']} had {row['PTS']:.1f} points, {row['REB']:.1f} rebounds, {row['AST']:.1f} assists, {row['STL']:.1f} steals, and {row['BLK']:.1f} blocks this week"
        lines.append(line)
    current_string = "\n".join(lines) 


    #Gets statistical leaders in each category for the week and combines into one string
    pt_leader = current_week_log.sort_values(by=('PTS'),ascending=False).head(1)[['Name','PTS']]
    pt_leader_string = f"The leader in points scored was {pt_leader['Name'].iloc[0]} with {pt_leader['PTS'].iloc[0]} points\n"

    threepm_leader = current_week_log.sort_values(by=('3PM'),ascending=False).head(1)[['Name','3PM']]
    threepm_leader_string = f"The leader in 3 pointers made was {threepm_leader['Name'].iloc[0]} with {threepm_leader['3PM'].iloc[0]} three pointers made\n"

    reb_leader = current_week_log.sort_values(by=('REB'),ascending=False).head(1)[['Name','REB']]
    reb_leader_string = f"The leader in rebounds was {reb_leader['Name'].iloc[0]} with {reb_leader['REB'].iloc[0]} rebounds\n"

    ast_leader = current_week_log.sort_values(by=('AST'),ascending=False).head(1)[['Name','AST']]
    ast_leader_string = f"The leader in assists was {ast_leader['Name'].iloc[0]} with {ast_leader['AST'].iloc[0]} assists\n"

    stl_leader = current_week_log.sort_values(by=('STL'),ascending=False).head(1)[['Name','STL']]
    stl_leader_string = f"The leader in steals was {stl_leader['Name'].iloc[0]} with {stl_leader['STL'].iloc[0]} steals\n"

    blk_leader = current_week_log.sort_values(by=('BLK'),ascending=False).head(1)[['Name','BLK']]
    blk_leader_string = f"The leader in blocks was {blk_leader['Name'].iloc[0]} with {blk_leader['BLK'].iloc[0]} blocks\n"

    total_leaders_string = f"{pt_leader_string}{threepm_leader_string}{reb_leader_string}{ast_leader_string}{stl_leader_string}{blk_leader_string}"

    stat_strings = {
        "averages": averages_string,
        "current": current_string,
        "total_leaders": total_leaders_string
    }

    return stat_strings


#Left off here

def report(report_type,stats):
    if(report_type == "r"):
        
        system_prompt = reporter_system_prompt
        content_prompt = reporter_content_prompt.format(total_string=stats["total"])

    elif(report_type == "h"):
        system_prompt = hot_take_system_prompt
        content_prompt = hot_take_content_prompt.format(current_string=stats["current"],averages_string=stats["averages"])
         
    client = genai.Client()

    reporter_response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(system_instruction=system_prompt),contents=content_prompt
    )

    print(reporter_response.text)
    return reporter_response



def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("current_week",type=int)
    parser.add_argument("report_type",choices=["r","h"])
    args = parser.parse_args()



    stats = process_data(current_week = args.current_week)

    report_result = report(args.report_type,stats)


if __name__ == "__main__":
    main()
