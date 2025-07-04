from AI_ChatBot.logging import logger
from AI_ChatBot.pipeline.dataIngestion import DataIngestionTrainingPipeline
from AI_ChatBot.pipeline.data_transformation import DataTransformationTrainingPipeline
from AI_ChatBot.pipeline.data_vectorization import DataVectorizationPipeline
import joblib

stageName = "Data Ingestion stage"
 
try:
    logger.info(f">>>>>>> stage {stageName} started <<<<<<<") 
    dataIngestion = DataIngestionTrainingPipeline()
    dataIngestion.main()
    logger.info(f">>>>>>> stage {stageName} completed <<<<<<\n\nx===========x\n")
except Exception as e:
    logger.exception(e)
    raise e

stageName = "Data Transformation stage"

try:
    logger.info(f">>>>>>> stage {stageName} started <<<<<<<") 
    dataTransformation = DataTransformationTrainingPipeline()
    docs,chunks = dataTransformation.main()
    # joblib.dump(chunks, "artifacts/chunks.pkl")  # Use this only for local running
    logger.info(f">>>>>>> stage {stageName} completed <<<<<<\n\nx===========x\n")
except Exception as e:
    logger.exception(e)
    raise e

stageName = "Data Vectorization Stage"

try:
    logger.info(f">>>>>>> stage {stageName} started <<<<<<<") 
    dataVectorization = DataVectorizationPipeline()
    # chunks = joblib.load("artifacts/chunks.pkl")  # Only for local usage
    embedding_status = dataVectorization.main(chunks)
    print(embedding_status)
    logger.info(f">>>>>>> stage {stageName} completed <<<<<<\n\nx===========x\n")
except Exception as e:
    logger.exception(e)
    raise e

