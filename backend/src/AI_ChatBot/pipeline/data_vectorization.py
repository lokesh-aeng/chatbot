from AI_ChatBot.config.configuration import ConfigurationManager
from AI_ChatBot.components.data_vectorization import DataVectorization
from AI_ChatBot.logging import logger
from dotenv import load_dotenv
import os

class DataVectorizationPipeline:
    def __init__(self):
        pass

    def main(self, chunks):
        configuration_manager = ConfigurationManager()
        data_vectorization_config = configuration_manager.getVectorizationConfig()
        data_vectorization = DataVectorization(data_vectorization_config)
        embed_status = data_vectorization.ingest_chunks(chunks)
        return embed_status
    