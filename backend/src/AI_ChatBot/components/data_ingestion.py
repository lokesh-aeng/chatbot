import os
import gdown
from AI_ChatBot.logging import logger
from AI_ChatBot.entity import DataIngestionConfig

class DataIngestion:
    def __init__(self,config:DataIngestionConfig):
        self.config = config

    def download_file(self)->str:
        try:
            if not os.path.exists(self.config.local_data_file) or len(os.listdir(self.config.local_data_file))==0:
                os.makedirs(self.config.root_dir,exist_ok=True)
                url = self.config.source_url
                zip_location = self.config.local_data_file
                logger.info(f'Downloading Data from {url} to the location {zip_location}')
                gdown.download_folder(url=url,output=zip_location)
                logger.info(f'Data Download Completed')
            else:
                logger.info("Files already exist")
        except Exception as e:
            raise e
    