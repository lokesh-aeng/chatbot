from AI_ChatBot.constants import configFilePath,paramsFilePath
from AI_ChatBot.utils.common import read_yaml,createDir
from pathlib import Path
from AI_ChatBot.entity import (
    DataIngestionConfig, 
    DataTransformationConfig, 
    LoaderConfig, 
    RecursiveConfig, 
    SemanticConfig, 
    DataTransformationParams,
    VectorizationConfig,
    QueryConfig,
    CacheConfig
    )


class ConfigurationManager:
    def __init__(self,config_path = configFilePath,params_path=paramsFilePath):
        self.config = read_yaml(config_path)
        self.params = read_yaml(params_path)

        createDir([self.config.artifacts_root])
    
    def get_DataIngestionConfig(self) -> DataIngestionConfig:
        config = self.config.data_ingestion

        createDir([config.root_dir])
        data_ingestion_config = DataIngestionConfig(
            root_dir=(config.root_dir),
            source_url=(config.source_url),
            local_data_file=(config.local_data_file),
            unzip_dir=(config.unzip_dir)
        )
        return data_ingestion_config
    
    def get_DataTransformationConfig(self) -> DataTransformationConfig:
        config = self.config.data_transformation

        createDir([config.root_dir])
        data_transformation_config = DataTransformationConfig(
            root_dir= Path(config.root_dir),
            text_dir= Path(config.text_dir),
            video_dir= Path(config.video_dir),
            source_dir= Path(config.source_dir)
        )
        return data_transformation_config

    def getLoaderConfig(self)->LoaderConfig:
        params = self.params.loader

        return LoaderConfig(
            mode=str(params.mode),
            strategy=str(params.strategy)
        )

    def getRecursiveConfig(self)->RecursiveConfig:
        params = self.params.recursive

        return RecursiveConfig(
            chunk_size=int(params.chunk_size),
            chunk_overlap=int(params.chunk_overlap)
        )

    def getSemanticConfig(self)->SemanticConfig:
        params = self.params.semantic

        return SemanticConfig(
            percentile = int(params.percentile),
            breakpoint_threshold_type = str(params.breakpoint_threshold_type),
            breakpoint_threshold_amount = int(params.breakpoint_threshold_amount),
            buffer_size = int(params.buffer_size)
        )

    def getDataTransformationParams(self)->DataTransformationParams:

        return DataTransformationParams(
            loader = self.getLoaderConfig(),
            recursive = self.getRecursiveConfig(),
            semantic = self.getSemanticConfig()
        )

    def getVectorizationConfig(self)->VectorizationConfig:
        params = self.params.supabase

        return VectorizationConfig(
            batch_embed=int(params.batch_embed),
            batch_table=int(params.batch_table),
            docs=str(params.docs),
            chunks=str(params.chunks)
        )
    
    def getQueryConfig(self)->QueryConfig:
        params = self.params.query

        return QueryConfig(
            similarity_threshold=params.similarity_threshold,
            top_k=params.top_k
        )    

    def get_CacheConfig(self) -> CacheConfig:
        config = self.config.cache
        params = self.params.cache

        Path(config.json_dir).mkdir(parents=True,exist_ok=True)
        
        return CacheConfig(
            json_dir=config.json_dir,
            query_dir=config.query_dir,
            vectors_max_size=params.vectors_max_size,
            response_ttl=params.response_ttl,
            json_max_bytes=params.json_max_bytes
        )