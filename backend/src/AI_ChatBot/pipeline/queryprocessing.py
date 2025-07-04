from AI_ChatBot.config.configuration import ConfigurationManager
from AI_ChatBot.components.query_processing import QueryProcessor
from AI_ChatBot.logging import logger

class QueryProcessingPipeline:
    def __init__(self):
        pass

    def main(self):
        configuration_manager = ConfigurationManager()
        query_config = configuration_manager.getQueryConfig()
        query_processor = QueryProcessor(query_config)

        return query_processor


        