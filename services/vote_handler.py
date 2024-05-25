from base.logging import Logger
from modules.dtos.vote_data import VoteData
from modules.objects.boss import LocalBoss
from modules.dtos.boss_emoji_data import BossEmoji
class VoteHandler:
    def __init__(self,boss_emojis:list[BossEmoji]):
        super().__init__()
        self.boss_emojis:list[BossEmoji] = boss_emojis
        self.votes:list[VoteData] = []
        self.selected_boss:LocalBoss = None

    def __voted(self,discord_name:str) -> VoteData:
        """Check if a discord user already has a vote logged.  Returns the VoteData if found, else None"""
        for vote in self.votes:
            if vote.discord_name == discord_name:
                return vote
        return None

    def get_previous_reaction(self,discord_name:str) -> str:
        """Get the reaction the user previously used to vote.  Returns None if the user has not voted."""
        vote = self.__voted(discord_name)
        if vote is None:
            return None
        return vote.emoji
    
    def add_vote(self,discord_name:str,emoji:str,overwrite_previous:bool = True) -> bool:
        """Add a user vote.  Unless overwrite_previous is specifically flagged as False, it will overwrite previous votes if they exist.
        returns True, unless a previous vote exists and overwrite_previous is False"""
        boss:LocalBoss = None
        for boss_emoji in self.boss_emojis:
            if boss_emoji.emoji == emoji:
                boss = boss_emoji.boss
                break
        if boss is None:
            Logger.error(f"Could not find boss for emoji {emoji}")
            return False
        if self.__voted(discord_name):
            if not overwrite_previous:
                    return False
            else:
                self.votes.remove(self.__voted(discord_name))
        self.votes.append(VoteData(discord_name,boss,emoji))
        return True
    
    def remove_vote(self,discord_name:str,emoji:str) -> bool:
        """Remove a user vote if it exists. Returns True if the vote was removed, False if it did not exist."""
        for vote in self.votes:
            if vote.discord_name == discord_name and vote.emoji == emoji:
                self.votes.remove(vote)
                return True
        return False

    def tally_votes(self) -> LocalBoss:
        """Tally the votes, and return the boss with the most votes.
        If there is a tie, the first boss will be returned.
        If there are no votes, will return None"""
        #if no votes
        if len(self.votes) == 0:
            return None
        #tally votes
        vote_counts = {}
        for vote in self.votes:
            if vote.boss in vote_counts:
                vote_counts[vote.boss] += 1
            else:
                vote_counts[vote.boss] = 1
        #get the boss with the most votes
        max_votes = 0
        top_boss:LocalBoss = None
        for boss,votes in vote_counts.items():
            if votes > max_votes:
                max_votes = votes
                top_boss = boss
        self.selected_boss = top_boss
        return top_boss
    