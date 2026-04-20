from google import genai
from google.genai import types
import wave

class reporter:
    def __init__(self,system_prompt,content_prompt,TAG_system_prompt,TAG_content_prompt):
        self.system_prompt = system_prompt
        self.content_prompt = content_prompt
        self.TAG_system_prompt = TAG_system_prompt
        self.TAG_content_prompt = TAG_content_prompt
        self.strings = None
        self.generated_report = None

    def generate_report(self):
        client = genai.Client()
        reporter_response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            config=types.GenerateContentConfig(system_instruction=self.system_prompt),contents=self.content_prompt
        )
        self.generated_report = reporter_response.text

    def add_audio_tags(self):

        if(self.generated_report == None):
            print("No prompt generated")
            return None

        self.TAG_content_prompt = self.TAG_content_prompt.format(
            TAG_script = self.generated_report
        )

        client = genai.Client()
        reporter_response = client.models.generate_content(
            model="gemini-2.5-flash-lite",
            config=types.GenerateContentConfig(system_instruction=self.TAG_system_prompt),contents=self.TAG_content_prompt
        )
        print(reporter_response.text)
        self.generated_report = reporter_response.text
        
    
    def process_game_logs(self,game_logs,current_week):
        
        #Split into current weeks and past weeks
        past_game_logs = game_logs[game_logs["Week"] < current_week ]
        current_week_log = game_logs[game_logs["Week"] == current_week]

        #Add shooting percentages
        current_week_log['FG_P'] = ((current_week_log['FGM'] / current_week_log['FGA']) * 100).round(2)

        current_week_log['3P_P'] = ((current_week_log['3PM'] / current_week_log['3PA']) * 100).round(2)

        past_game_logs['FG_P'] = ((past_game_logs['FGM'] / past_game_logs['FGA']) * 100).round(2)

        past_game_logs['3P_P'] = ((past_game_logs['3PM'] / past_game_logs['3PA']) * 100).round(2)

        week_logs = {

            'current_week_log':current_week_log,
            'past_game_logs':past_game_logs
        }

        return week_logs
    
    def convert_to_audio(self,voice,file_name):

        # Set up the wave file to save the output:
        def wave_file(filename, pcm, channels=1, rate=24000, sample_width=2):
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(sample_width)
                wf.setframerate(rate)
                wf.writeframes(pcm)

        if(self.generated_report == None):
            print("No report generated, Audio failed")
            return None

        client = genai.Client()

        response = client.models.generate_content(
        model="gemini-3.1-flash-tts-preview",
        contents=self.generated_report,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice,
                    )
                )
            ),
        )
        )

        print("Audio generated successfully")

        data = response.candidates[0].content.parts[0].inline_data.data

        wave_file(file_name, data)
        return None




class hot_take_reporter(reporter):

    def process_game_logs(self,game_logs,current_week):
        week_logs = super().process_game_logs(game_logs,current_week)
        current_week_log = week_logs['current_week_log']
        past_game_logs = week_logs['past_game_logs']


        #Compute player season averages
        player_averages = past_game_logs.groupby("Name",sort=False)[["PTS", "FGA", "FGM", "3PA", "3PM", "REB", "AST", "STL", "BLK"]].mean().reset_index()

        player_averages['FG_P'] = ((player_averages['FGM'] / player_averages['FGA']) * 100).round(2)

        player_averages['3P_P'] = ((player_averages['3PM'] / player_averages['3PA']) * 100).round(2)


        #Create averages string
        lines = []

        for _, row in player_averages.iterrows():
            line = f"{row['Name']} averages {row['PTS']:.1f} points, {row['FG_P']:.1f}% field goal percentage, {row['3P_P']:.1f}% three point percentage, {row['REB']:.1f} rebounds, {row['AST']:.1f} assists, {row['STL']:.1f} steals, and {row['BLK']:.1f} blocks"
            lines.append(line)

        averages_string = "\n".join(lines) 


        #Creat current week string
        lines = []

        for _, row in current_week_log.iterrows():
            line = f"{row['Name']} had {row['PTS']:.1f} points, shot {row['FG_P']:.1f}% from the field, shot {row['3P_P']:.1f}% on three pointers, and had {row['REB']:.1f} rebounds, {row['AST']:.1f} assists, {row['STL']:.1f} steals, and {row['BLK']:.1f} blocks this week"
            lines.append(line)

        current_string = "\n".join(lines)

        self.content_prompt = self.content_prompt.format(
            current_string = current_string,
            averages_string=averages_string
        )

        print("Data injected into prompt......success!")

    def convert_to_audio(self):
        super().convert_to_audio('Iapetus', 'hot_take_reporter.wav')

class regular_reporter(reporter):


    #This is super hard coded probably want to make better
    def process_game_logs(self, game_logs,current_week):
        week_logs = super().process_game_logs(game_logs,current_week)
        current_week_log = week_logs['current_week_log']

        pt_leader = current_week_log.sort_values(by=('PTS'),ascending=False).head(1)[['Name','PTS']]
        pt_leader_string = f"The leader in points scored was {pt_leader['Name'].iloc[0]} with {pt_leader['PTS'].iloc[0]} points\n"

        threepm_leader = current_week_log.sort_values(by=('3PM'),ascending=False).head(1)[['Name','3PM']]
        threepm_leader_string = f"The leader in 3 pointers made was {threepm_leader['Name'].iloc[0]} with {threepm_leader['3PM'].iloc[0]} three pointers made\n"

        fgp_leader = current_week_log.sort_values(by=('FG_P'),ascending=False).head(1)[['Name','FG_P']]
        fgp_leader_string = f"The leader in field goal percent was {fgp_leader['Name'].iloc[0]} shooting {fgp_leader['FG_P'].iloc[0]}%\n"

        threepp_leader = current_week_log.sort_values(by=('3P_P'),ascending=False).head(1)[['Name','3P_P']]
        threepp_leader_string = f"The leader in three point percent was {threepp_leader['Name'].iloc[0]} shooting {threepp_leader['3P_P'].iloc[0]}%\n"

        reb_leader = current_week_log.sort_values(by=('REB'),ascending=False).head(1)[['Name','REB']]
        reb_leader_string = f"The leader in rebounds was {reb_leader['Name'].iloc[0]} with {reb_leader['REB'].iloc[0]} rebounds\n"

        ast_leader = current_week_log.sort_values(by=('AST'),ascending=False).head(1)[['Name','AST']]
        ast_leader_string = f"The leader in assists was {ast_leader['Name'].iloc[0]} with {ast_leader['AST'].iloc[0]} assists\n"

        stl_leader = current_week_log.sort_values(by=('STL'),ascending=False).head(1)[['Name','STL']]
        stl_leader_string = f"The leader in steals was {stl_leader['Name'].iloc[0]} with {stl_leader['STL'].iloc[0]} steals\n"

        blk_leader = current_week_log.sort_values(by=('BLK'),ascending=False).head(1)[['Name','BLK']]
        blk_leader_string = f"The leader in blocks was {blk_leader['Name'].iloc[0]} with {blk_leader['BLK'].iloc[0]} blocks\n"

        total_string = f"{pt_leader_string}{fgp_leader_string}{threepp_leader_string}{threepm_leader_string}{reb_leader_string}{ast_leader_string}{stl_leader_string}{blk_leader_string}"

        self.content_prompt = self.content_prompt.format(
            total_string = total_string
        )

        print("Data injected into prompt......success!")


    def convert_to_audio(self):
        super().convert_to_audio('Gacrux', 'regular_reporter.wav')


def process_game(game_team_groups,team_names):
        winner = game_team_groups.iloc[game_team_groups['PTS'].idxmax()]
        loser = game_team_groups.iloc[game_team_groups['PTS'].idxmin()]
        return f"{team_names[winner["Team"]]} beat {team_names[loser["Team"]]} {winner["PTS"]} to {loser["PTS"]}. {team_names[winner["Team"]]} had {winner['REB']} rebounds, {winner['AST']} assists, {winner['STL']} steals, {winner['BLK']} blocks and shot {winner['FG_P']} percent from the field and shot {winner['3P_P']} percent from three. {team_names[loser["Team"]]} had {loser['REB']} rebounds, {loser['AST']} assists, {loser['STL']} steals, {loser['BLK']} blocks and shot {loser['FG_P']} percent from the field and shot {loser['3P_P']} percent from three." 

class game_recap_reporter(reporter):

    #Helper function for process game logs
    
    #Super hardcoded, definitely want to add some loops in here for cleaner code
    def process_game_logs(self,game_logs,current_week):
        week_logs = super().process_game_logs(game_logs,current_week)
        current_week_log = week_logs['current_week_log']

        #Split into games
        game1_id = current_week_log.at[17,'Game_ID']

        game1 = current_week_log[current_week_log['Game_ID'] == game1_id]
        game2 = current_week_log[current_week_log['Game_ID'] != game1_id]
        
        game1_team_groups = game1.groupby("Team",sort=False)[["PTS","FGA", "FGM", "3PA", "3PM","REB", "AST", "STL", "BLK"]].sum().reset_index()
        game2_team_groups = game2.groupby("Team",sort=False)[["PTS","FGA", "FGM", "3PA", "3PM","REB", "AST", "STL", "BLK"]].sum().reset_index()

        game1_team_groups['FG_P'] = ((game1_team_groups['FGM'] / game1_team_groups['FGA']) * 100).round(2)

        game1_team_groups['3P_P'] = ((game1_team_groups['3PM'] / game1_team_groups['3PA']) * 100).round(2)

        game2_team_groups['FG_P'] = ((game2_team_groups['FGM'] / game2_team_groups['FGA']) * 100).round(2)

        game2_team_groups['3P_P'] = ((game2_team_groups['3PM'] / game2_team_groups['3PA']) * 100).round(2)

        team_names =  {
            'WESTDIST' : 'West District Tigers',
            'DAB' : 'Dab Dynasty',
            'THREES' : 'Drilled Threes Burrito',
            'ECTA' : 'Emerald City Throat Artist'
        }

        game1_string = process_game(game1_team_groups,team_names)
        game2_string = process_game(game2_team_groups,team_names)

        game_strings = [game1_string,game2_string]

        prompts = []
        for game_string in game_strings:
            prompts.append(self.content_prompt.format(
            game_string = game_string
        ))
        self.content_prompt = prompts

        print("Data injected into prompt......success!")


        

    def generate_report(self,n_games):
        reports = []

        for prompt in self.content_prompt:
            self.content_prompt = prompt
            reports.append(super().generate_report())

        self.generated_report = reports
    
    def convert_to_audio(self):
        #List of generated reports
        all_gen_reports = self.generated_report
        count = 1
        for generated_report in all_gen_reports:
            self.generated_report = generated_report
            filename = 'game_recap_' + count + '.wav'
            count += 1
            super().convert_to_audio('Algieba', filename)


