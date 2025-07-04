from AI_ChatBot.config.configuration import ConfigurationManager
from AI_ChatBot.components.data_ingestion import DataIngestion
from AI_ChatBot.logging import logger

class DataIngestionTrainingPipeline:
    def __init__(self):
        pass

    def main(self):
        config = ConfigurationManager()
        data_ingestion_config = config.get_DataIngestionConfig()
        data_ingestion = DataIngestion(data_ingestion_config)
        data_ingestion.download_file()
