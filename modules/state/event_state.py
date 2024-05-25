from datetime import datetime

class EventState:
    def __init__(self, vote_open:datetime, vote_close:datetime, tracking_start:datetime, tracking_stop:datetime):
        self.vote_open:datetime = vote_open
        self.vote_close:datetime = vote_close
        self.tracking_start:datetime = tracking_start
        self.tracking_stop:datetime = tracking_stop

        # generate additional fields for apscheduler cron jobs using the datetime objects
        self.vote_open_day:str = self.vote_open.strftime("%a").lower()
        self.vote_open_hour:int = self.vote_open.hour
        self.vote_open_minute:int = self.vote_open.minute

        self.vote_close_day:str = self.vote_close.strftime("%a").lower()
        self.vote_close_hour:int = self.vote_close.hour
        self.vote_close_minute:int = self.vote_close.minute

        self.tracking_start_day:str = self.tracking_start.strftime("%a").lower()
        self.tracking_start_hour:int = self.tracking_start.hour
        self.tracking_start_minute:int = self.tracking_start.minute

        self.tracking_stop_day:str = self.tracking_stop.strftime("%a").lower()
        self.tracking_stop_hour:int = self.tracking_stop.hour
        self.tracking_stop_minute:int = self.tracking_stop.minute
        