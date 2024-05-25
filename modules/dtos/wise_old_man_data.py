from datetime import datetime
import math

class WiseOldManBossData:
    def __init__(self,name:str,kills:int,rank:int,ehb:int):
        self.name:str = name
        self.kills:int = kills
        self.rank:int = rank
        self.ehb:int = ehb

class WiseOldManPlayerData:
    def __init__(self,username:str, displayName:str,snapshot_creation:datetime,boss_data:list[WiseOldManBossData]) -> None:
        self.username:str = username
        self.displayName:str = displayName
        self.snapshot_creation:datetime = snapshot_creation
        self.boss_data:list[WiseOldManBossData] = boss_data
