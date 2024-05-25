from modules.objects.boss import LocalBoss
class VoteData:
    def __init__(self,
                discord_name:str,
                boss:LocalBoss,
                emoji:str):
        self.discord_name:str = discord_name
        self.boss:LocalBoss = boss
        self.emoji:str = emoji