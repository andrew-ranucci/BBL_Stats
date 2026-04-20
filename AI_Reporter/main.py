from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import pandas as pd
from prompts import reporter_system_prompt, reporter_content_prompt, hot_take_content_prompt, hot_take_system_prompt, game_recap_content_prompt, game_recap_system_prompt,TAG_content_prompt,reporter_TAG_system_prompt,hot_take_TAG_system_prompt,game_recap_TAG_system_prompt
import argparse
import reporters

#Runs all the reporters and creates a dictionary of their scripts, might have them convert their own text to speech
#Fine for now just to see the output scripts
def create_scripts(game_logs,current_week):
    #regular_stats_reporter = reporters.regular_reporter(reporter_system_prompt,reporter_content_prompt,reporter_TAG_system_prompt,TAG_content_prompt)
    hot_take_reporter = reporters.hot_take_reporter(hot_take_system_prompt,hot_take_content_prompt,hot_take_TAG_system_prompt,TAG_content_prompt)
    #game_recap_reporter = reporters.game_recap_reporter(game_recap_system_prompt,game_recap_content_prompt,game_recap_TAG_system_prompt,TAG_content_prompt)

    #regular_stats_reporter.process_game_logs(game_logs,current_week)
    hot_take_reporter.process_game_logs(game_logs,current_week)
    #game_recap_reporter.process_game_logs(game_logs,current_week)

    #regular_stats_reporter.generate_report()
    hot_take_reporter.generate_report()
    #game_recap_reporter.generate_report()

    #regular_stats_reporter.add_audio_tags()
    hot_take_reporter.add_audio_tags()
    #game_recap_reporter.add_audio_tags()

    #regular_stats_reporter.convert_to_audio()
    hot_take_reporter.convert_to_audio()
    #game_recap_reporter.convert_to_audio()



    
    
    

#Need to either make this or give every reporter the ability to convert its text to speech??
#Need more research to figure this out
def convert_to_podcast():
    return None


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("current_week",type=int)
    args = parser.parse_args()

    game_logs = pd.read_excel("C:\\Users\\andre\\BBL_Stats_DATA\\BBL Season 2 Stats.xlsx",sheet_name="Game Logs")
    game_logs = game_logs.dropna()

    create_scripts(game_logs,args.current_week)



if __name__ == "__main__":
    main()
