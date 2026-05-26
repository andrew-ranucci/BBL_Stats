from dotenv import load_dotenv
import os
from google import genai
from google.genai import types
import pandas as pd
from prompts import debate_system_prompt, debate_content_prompt
import wave
from google import genai
from google.genai import types


load_dotenv()

def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm)

def debate_show(names_dict,game_logs,player_name,current_week):
    if(player_name not in names_dict):
        print("Invalid Player Name")
        return None
    
    player_name = names_dict[player_name]
    
    strings_dict = process_games(game_logs,current_week,player_name)
    
    fill_debate_content_prompt = debate_content_prompt.format(
        league_avg_string = strings_dict['league_avg_string'],
        current_string = strings_dict['current_string'],
        averages_string = strings_dict['averages_string']
    )
    

    
    client = genai.Client()

    try:
        reporter_response = client.models.generate_content(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(system_instruction=debate_system_prompt),contents=fill_debate_content_prompt
            )
        text = reporter_response.text
        print("Generating Script.......Success!")
        
    except Exception as e:
        print("Gemini failed script creation failed")
        print(e)
        return None
    
    
    #Audio Conversion 
    
    print("Attempting to convert to audio")
    

    try:
        client = genai.Client()

        response = client.models.generate_content(
        model="gemini-3.1-flash-tts-preview",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker='Randy',
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Puck',
                            )
                        )
                    ),
                    types.SpeakerVoiceConfig(
                        speaker='Joe',
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name='Algenib',
                            )
                        )
                    ),
                    ]
                )
            )
        )
        )

    except Exception as e:
        print("Audio conversion failed")
        print(e)
        return None

    

    data = response.candidates[0].content.parts[0].inline_data.data

    print("Audio generated successfully")

    wave_file(f"debate_{player_name}_week{current_week}.wav", data)
    return None
    



def clean_num(x):
    if pd.isna(x):
        return "0"
    x = float(x)
    if x.is_integer():
        return str(int(x))
    return f"{x:.1f}"

def process_games(game_logs,current_week,player_name):
    weeks = pd.to_numeric(game_logs["Week"])
    past_game_logs = game_logs[weeks < current_week].copy()
    current_week_log = game_logs[weeks == current_week].copy()
    
    game_logs['FG_P'] = ((game_logs['FGM'] / game_logs['FGA']) * 100).round(2)

    game_logs['3P_P'] = ((game_logs['3PM'] / game_logs['3PA']) * 100).round(2)
    
    league_fg_pct = (game_logs['FGM'].sum() / game_logs['FGA'].sum()) * 100
    league_3p_pct = (game_logs['3PM'].sum() / game_logs['3PA'].sum()) * 100

    league_avg_string = f"""The following stats are the league averages: 
    {game_logs['PTS'].mean():.1f} points per game, 
    {game_logs['FGM'].mean():.1f} field goals made per game, 
    {game_logs['FGA'].mean():.1f} field goals attempted per game, 
    {league_fg_pct:.1f}% field goal shooting, 
    {game_logs['3PM'].mean():.1f} three-pointers made per game, 
    {game_logs['3PA'].mean():.1f} three-pointers attempted per game, 
    {league_3p_pct:.1f}% three-point shooting, 
    {game_logs['REB'].mean():.1f} rebounds per game, 
    {game_logs['AST'].mean():.1f} assists per game, 
    {game_logs['STL'].mean():.1f} steals per game, 
    and {game_logs['BLK'].mean():.1f} blocks per game."""
    print(league_avg_string)
    #Add shooting percentages
    
    current_week_log['FG_P'] = ((current_week_log['FGM'] / current_week_log['FGA']) * 100).round(2)

    current_week_log['3P_P'] = ((current_week_log['3PM'] / current_week_log['3PA']) * 100).round(2)

    past_game_logs['FG_P'] = ((past_game_logs['FGM'] / past_game_logs['FGA']) * 100).round(2)

    past_game_logs['3P_P'] = ((past_game_logs['3PM'] / past_game_logs['3PA']) * 100).round(2)

    week_logs = {
            'current_week_log':current_week_log,
            'past_game_logs':past_game_logs
    }

    print("Processing Game Logs......Success!")
    
    
    current_week_log = week_logs['current_week_log']
    past_game_logs = week_logs['past_game_logs']


        #Compute player season averages
        
    player_averages = past_game_logs.groupby("Name",sort=False)[["PTS", "FGA", "FGM", "3PA", "3PM", "REB", "AST", "STL", "BLK","GP"]].mean().reset_index()

    player_averages['GP'] = player_averages['GP'] * (current_week - 1)

    player_averages['FG_P'] = ((player_averages['FGM'] / player_averages['FGA']) * 100).round(2)

    player_averages['3P_P'] = ((player_averages['3PM'] / player_averages['3PA']) * 100).round(2)


        #Create averages string
    player_average_match = player_averages[player_averages["Name"] == player_name]

    if player_average_match.empty:
        averages_string = f"{player_name} has no prior averages."
    else:
        row = player_average_match.iloc[0]
        averages_string = f"{row['Name']} averages {clean_num(row['PTS'])} points, {clean_num(row['FG_P'])}% field goal percentage, {clean_num(row['3P_P'])}% three point percentage, {clean_num(row['REB'])} rebounds, {clean_num(row['AST'])} assists, {clean_num(row['STL'])} steals, {clean_num(row['BLK'])} blocks, and has played in {clean_num(row['GP'])} games."


        #Creat current week string
    current_week_match = current_week_log[current_week_log["Name"] == player_name]

    if current_week_match.empty:
        current_string = f"{player_name} did not play in Week {current_week}."
    else:
        row = current_week_match.iloc[0]
        current_string = f"{row['Name']} had {clean_num(row['PTS'])} points, shot {clean_num(row['FG_P'])}% from the field, shot {clean_num(row['3P_P'])}% on three pointers, and had {clean_num(row['REB'])} rebounds, {clean_num(row['AST'])} assists, {clean_num(row['STL'])} steals, and {clean_num(row['BLK'])} blocks this week"

    print("Data injected into prompt......success!")

    strings_dict = {
        'current_string':current_string,
        'averages_string':averages_string,
        'league_avg_string':league_avg_string
    }

    return strings_dict
