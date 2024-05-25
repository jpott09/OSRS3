class ApiState:
    def __init__(self,url:str,discord_contact_name:str, update_frequency:int):
        self.url = url
        self.discord_contact_name = discord_contact_name
        self.update_frequency = update_frequency