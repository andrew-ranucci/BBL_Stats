from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import pandas as pd
from prompts import reporter_system_prompt, reporter_content_prompt, hot_take_content_prompt, hot_take_week_one_system_prompt, hot_take_system_prompt, game_recap_content_prompt, game_recap_system_prompt,TAG_content_prompt,reporter_TAG_system_prompt,hot_take_TAG_system_prompt,game_recap_TAG_system_prompt
import argparse
import reporters
from pathlib import Path
import wave
from show_scripts import intro
from pydub import AudioSegment
import time
from debate_show import debate_show

#Remove this later and leave in reporters.py
def write_report_to_file(report, filename):
        with open(filename, "w", encoding="utf-8") as file:
            file.write(report)
            
def read_report_from_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return file.read()
    
def write_game_recaps_to_file(reports):
    for i, report in enumerate(reports, start=1):
        write_report_to_file(report, f"game_recap_{i}.txt")
        
def build_results_from_files():
    reports_done = (
        Path("regular_report.txt").is_file()
        and Path("hot_take_report.txt").is_file()
        and Path("game_recap_1.txt").is_file()
        and Path("game_recap_2.txt").is_file()
    )

    tags_done = (
        Path("regular_report_tagged.txt").is_file()
        and Path("hot_take_report_tagged.txt").is_file()
        and Path("game_recap_1_tagged.txt").is_file()
        and Path("game_recap_2_tagged.txt").is_file()
    )

    audio_done = (
        Path("regular_reporter.wav").is_file()
        and Path("hot_take_reporter.wav").is_file()
        and Path("game_recap_1.wav").is_file()
        and Path("game_recap_2.wav").is_file()
    )

    return {
        "process": False,
        "reports": reports_done,
        "tags": tags_done,
        "audio": audio_done,
        "regular_stats_reporter": None,
        "hot_take_reporter": None,
        "game_recap_reporter": None
    }

def read_game_recaps_from_file():
    reports = []
    count = 1

    while Path(f"game_recap_{count}.txt").is_file():
        reports.append(read_report_from_file(f"game_recap_{count}.txt"))
        count += 1

    return reports

def write_game_recaps_to_file_tagged(reports):
    for i, report in enumerate(reports, start=1):
        write_report_to_file(report, f"game_recap_{i}_tagged.txt")

def read_game_recaps_from_file_tagged():
    reports = []
    count = 1

    while Path(f"game_recap_{count}_tagged.txt").is_file():
        reports.append(read_report_from_file(f"game_recap_{count}_tagged.txt"))
        count += 1

    return reports

#Runs all the reporters and creates a dictionary of their scripts, might have them convert their own text to speech
#Fine for now just to see the output scripts
def create_scripts(game_logs,current_week,results_dict,requests):
    regular_stats_reporter = reporters.regular_reporter(reporter_system_prompt,reporter_content_prompt,reporter_TAG_system_prompt,TAG_content_prompt)
    if(current_week == 1):
        hot_take_reporter = reporters.hot_take_reporter(hot_take_week_one_system_prompt,hot_take_content_prompt,hot_take_TAG_system_prompt,TAG_content_prompt)
    else:
        hot_take_reporter = reporters.hot_take_reporter(hot_take_system_prompt,hot_take_content_prompt,hot_take_TAG_system_prompt,TAG_content_prompt)
    
    game_recap_reporter = reporters.game_recap_reporter(game_recap_system_prompt,game_recap_content_prompt,game_recap_TAG_system_prompt,TAG_content_prompt)

    if results_dict["tags"]:
        print("Tagged script files found. Loading tagged scripts.")

        regular_stats_reporter.generated_report = read_report_from_file(
            "regular_report_tagged.txt"
        )

        hot_take_reporter.generated_report = read_report_from_file(
            "hot_take_report_tagged.txt"
        )

        game_recap_reporter.generated_report = read_game_recaps_from_file_tagged()

    elif results_dict["reports"]:
        print("Report files found. Loading untagged scripts.")

        regular_stats_reporter.generated_report = read_report_from_file(
            "regular_report.txt"
        )

        hot_take_reporter.generated_report = read_report_from_file(
            "hot_take_report.txt"
        )

        game_recap_reporter.generated_report = read_game_recaps_from_file()

    #Replace all of this with one function to run each reporter cuz main is getting cluttered

    if(not results_dict['process']):
        regular_stats_reporter.process_game_logs(game_logs,current_week)
        hot_take_reporter.process_game_logs(game_logs,current_week)
        game_recap_reporter.process_game_logs(game_logs,current_week)
        results_dict['process'] = True
        results_dict['regular_stats_reporter'] = regular_stats_reporter
        results_dict['hot_take_reporter'] = hot_take_reporter
        results_dict['game_recap_reporter'] = game_recap_reporter

    if(not results_dict['reports']):
        
        reg = regular_stats_reporter.generate_report()
        if(reg is None):
            results_dict['reports'] = False
            print("regular reporter failed")
            return results_dict
        hot = hot_take_reporter.generate_report()
        if(hot is None):
            results_dict['reports'] = False
            print("hot take reporter failed")
            return results_dict
        #Need a way to check this
        game_recap_reporter.generate_report()
        
        regular_stats_reporter.add_transition()
        hot_take_reporter.add_transition()
        game_recap_reporter.add_transition()

        write_report_to_file(
            regular_stats_reporter.generated_report,
            filename="regular_report.txt"
        )

        write_report_to_file(
            hot_take_reporter.generated_report,
            filename="hot_take_report.txt"
        )

        write_game_recaps_to_file(game_recap_reporter.generated_report)
        
        
        results_dict['reports'] = True
        results_dict['regular_stats_reporter'] = regular_stats_reporter
        results_dict['hot_take_reporter'] = hot_take_reporter
        results_dict['game_recap_reporter'] = game_recap_reporter
        
    print("Waiting one minutw")
    time.sleep(65)

    if(not results_dict['tags']):
        reg = regular_stats_reporter.add_audio_tags()
        if(reg is None):
            results_dict['tags'] = False
            print("regular reporter tags failed")
            return results_dict
        hot = hot_take_reporter.add_audio_tags()
        if(hot is None):
            results_dict['tags'] = False
            print("hot take reporter tags failed")
            return results_dict
        #Need a way to test this
        game_recap_reporter.add_audio_tags()
        
        write_report_to_file(
        regular_stats_reporter.generated_report,
        filename="regular_report_tagged.txt"
        )

        write_report_to_file(
            hot_take_reporter.generated_report,
            filename="hot_take_report_tagged.txt"
        )

        write_game_recaps_to_file_tagged(game_recap_reporter.generated_report)
        
        results_dict['tags'] = True
        results_dict['regular_stats_reporter'] = regular_stats_reporter
        results_dict['hot_take_reporter'] = hot_take_reporter
        results_dict['game_recap_reporter'] = game_recap_reporter


    if(not results_dict['audio']):
        regular_stats_reporter.convert_to_audio()
        hot_take_reporter.convert_to_audio()
        game_recap_reporter.convert_to_audio()

        results_dict["audio"] = (
            Path("regular_reporter.wav").is_file()
            and Path("hot_take_reporter.wav").is_file()
            and Path("game_recap_1.wav").is_file()
            and Path("game_recap_2.wav").is_file()
        )

        if not results_dict["audio"]:
            print("Audio conversion failed or incomplete.")
            return results_dict
    
    return results_dict



    
    
    

#Need to either make this or give every reporter the ability to convert its text to speech??
#Need more research to figure this out
def convert_to_podcast(week_num):
    load_dotenv()
    p = Path("conclusion.wav")
    if p.is_file():
        print("Conclusion found")
    else:
        print("Conclusion does not exist")
        return None
    
    def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm)
      
    back = None       
    if(week_num == 1):
        back = 'back'
    script = intro.format(week_num = week_num,back=back)
    
    print("Attempting to write intro")
    client = genai.Client()


#Could hard code the intro instead if hitting gemini token limit too frequently
    response = client.models.generate_content(
    model="gemini-2.5-flash-preview-tts",
    contents=script,
        config=types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name='Schedar',
                    )
                )
                ),
            )
            )

    data = response.candidates[0].content.parts[0].inline_data.data

    wave_file('intro.wav', data)
    
    print("Intro created successfully")
    
    intro_wav = AudioSegment.from_wav("intro.wav")
    #Hardcoded and needs to be generalized for other league applications
    game_recap1_wav = AudioSegment.from_wav("game_recap_1.wav")
    game_recap2_wav = AudioSegment.from_wav("game_recap_2.wav")
    regular__wav = AudioSegment.from_wav("regular_reporter.wav")
    hot_take_wav = AudioSegment.from_wav("hot_take_reporter.wav")
    conclusion_wav = AudioSegment.from_wav("conclusion.wav")
    
    combined = intro_wav + game_recap1_wav + game_recap2_wav + regular__wav + hot_take_wav + conclusion_wav
    
    podcast_name = f"week{week_num}_podcast.wav"
    combined.export(podcast_name,format="wav")


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("current_week",type=int)
    parser.add_argument("player",type=str)
    args = parser.parse_args()

    game_logs = pd.read_excel("C:\\Users\\andre\\BBL_Stats_DATA\\BBL Season 2 Stats.xlsx",sheet_name="Game Logs")
    game_logs = game_logs.dropna()
    
    names_dict = {
        "SamO":"Sam Olivastro",
        "Andrew":"Andrew Ranucci",
        "SamL":"Sam Lamar",
        "Ryan":"Ryan Corvo",
        "Alex":"Alex Corvo",
        "Matthew":"Matt Berube",
        "Jojo":"Jojo Chapman",
        "Gavin":"Gavin Damboise",
        "Reydro":"Reydro Phillipe",
        "Aaron":"Aaron Burke",
        "Jonny":"Jonny Cassarola"
        
    }
    
    game_logs["Name"] = game_logs["Name"].replace(names_dict)
    
    if(args.player != "None"):
        debate_show(names_dict,game_logs,args.player,args.current_week)
        
    else:
        results = build_results_from_files()
        
        '''
        results = {
            'process':False,
            'reports':False,
            'tags':False,
            'audio':False,
            'regular_stats_reporter':None,
            'hot_take_reporter':None,
            'game_recap_reporter':None
        }
        '''
        
        count = 0
        requests = 0
        while((count != 5) 
            or (not results['process']) 
            or (not results['reports'])
            or (not results['tags']) 
            or (not results['audio'])):
            count += 1
            print(f"Iteration number {count}")
            results = create_scripts(game_logs,args.current_week,results,requests)
            
            #Need to do this better, if program runs perfectly it will still wait 60s unecessarily
            print(f"Waiting 60s")
            time.sleep(60)
        
        convert_to_podcast(args.current_week)


if __name__ == "__main__":
    main()
