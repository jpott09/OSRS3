from modules.objects.boss import Boss

class Player:
    def __init__(self,discord_name:str,osrs_name:str,boss_list:list[Boss]):
        self.discord_name:str = discord_name
        self.osrs_name:str = osrs_name
        self.boss_list:list[Boss] = boss_list