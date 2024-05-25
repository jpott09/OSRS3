

class DiscordState:
    def __init__(self):
        self.voting_channel_id:int = -1
        self.leaderboard_channel_id:int = -1
        self.set_name_channel_id:int = -1
        self.console_channel_id:int = -1
        self.bot_token:str = ""
        self.discord_admin_list:list[str] = []