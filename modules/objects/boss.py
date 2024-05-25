

class Boss:
    def __init__(self,name:str,kills:int):
        self.name:str = name
        self.kills:int = kills
        self.tracked_kills:int = 0
        self.kill_offset:int = 0

class LocalBoss:
    def __init__(self,name:str,api_name:str,level:int,location:str,image:str):
        self.name:str = name
        self.api_name:str = api_name
        self.level:int = level
        self.location:str = location
        self.image:str = image