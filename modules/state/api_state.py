class ApiState:
    def __init__(self,
                url:str,
                discord_contact_name:str,
                bulk_update_frequency_minutes:int,
                update_ratelimit_seconds:int):
        self.url:str = url
        self.discord_contact_name:str = discord_contact_name
        self.bulk_update_frequency_minutes:int = bulk_update_frequency_minutes
        self.update_ratelimit_seconds:int = update_ratelimit_seconds