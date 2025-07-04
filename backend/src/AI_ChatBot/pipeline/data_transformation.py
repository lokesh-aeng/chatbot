from AI_ChatBot.config.configuration import ConfigurationManager
from AI_ChatBot.components.data_transformation import DataTransformation
from AI_ChatBot.logging import logger

class DataTransformationTrainingPipeline:
    def __init__(self):
        pass

    def main(self):
        configuration_manager = ConfigurationManager()
        data_transformation_config = configuration_manager.get_DataTransformationConfig()
        data_transformation_params = configuration_manager.getDataTransformationParams()
        data_transformation = DataTransformation(data_transformation_config,data_transformation_params)
        docs,chunks = data_transformation.load_documents()
        return docs,chunks