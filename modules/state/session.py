from modules.objects.boss import LocalBoss
from datetime import datetime

class Session:
    def __init__(self):
        self.session_name:str = ""
        self.tracking_active:bool = False
        self.voting_active:bool = False
        self.last_boss:LocalBoss = None
        self.current_boss:LocalBoss = None
        self.boss_pool:list[LocalBoss] = []
        self.start_time:datetime = None
        self.used_boss_list:list[LocalBoss] = []
