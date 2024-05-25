from modules.objects.boss import LocalBoss

class BossEmoji:
    def __init__(self,boss:LocalBoss,emoji:str):
        self.boss:LocalBoss = boss
        self.emoji:str = emoji