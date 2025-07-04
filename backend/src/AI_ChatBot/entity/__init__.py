from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class DataIngestionConfig:
    root_dir: Path
    source_url: str
    local_data_file: Path
    unzip_dir: Path

@dataclass(frozen=True)
class DataTransformationConfig:
    root_dir: Path
    text_dir: Path
    video_dir: Path
    source_dir: Path

@dataclass(frozen=True)
class LoaderConfig:
    mode: str
    strategy: str

@dataclass(frozen=True)
class RecursiveConfig:
    chunk_size: int
    chunk_overlap: int

@dataclass(frozen=True)
class SemanticConfig:
    percentile: int
    breakpoint_threshold_type: str
    breakpoint_threshold_amount: int
    buffer_size: int

@dataclass(frozen=True)
class DataTransformationParams:
    loader: LoaderConfig
    recursive: RecursiveConfig
    semantic: SemanticConfig

@dataclass
class VectorizationConfig:
    batch_embed: int
    batch_table: int
    docs: str
    chunks: str

@dataclass
class QueryConfig:
    similarity_threshold: int
    top_k: int

@dataclass(frozen=True)
class CacheConfig:
    json_dir: Path
    query_dir: Path
    vectors_max_size: int
    response_ttl: int
    json_max_bytes: int