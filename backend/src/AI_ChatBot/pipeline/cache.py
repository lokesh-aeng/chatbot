from AI_ChatBot.config.configuration import ConfigurationManager
from AI_ChatBot.components.cache import CacheManager
from AI_ChatBot.logging import logger

class CacheTrainingPipeline:
    def __init__(self):
        pass

    def main(self):
        configuration_manager = ConfigurationManager()
        cache_config = configuration_manager.get_CacheConfig()
        cache = CacheManager(cache_config)
        return cache