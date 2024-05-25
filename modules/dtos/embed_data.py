
class EmbedData:
    def __init__(self,
                channel_id: int,
                title:str,
                message:str,
                image_path:str):
        self.channel_id:int = channel_id
        self.title:str = title
        self.message:str = message
        self.image_path:str = image_path