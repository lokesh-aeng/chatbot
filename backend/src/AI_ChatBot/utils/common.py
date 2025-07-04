import os
from box.exceptions import BoxValueError
import yaml
from AI_ChatBot.logging import logger
from ensure import ensure_annotations
from box import ConfigBox #configbox helps us to get values from a dict using mp.key rather than mp['key]
from pathlib import Path
from typing import Any

@ensure_annotations
def read_yaml(pathToYaml: Path)-> ConfigBox:
    """Reads yaml file and returs

    Args:
        pathToYaml (Path): path like input

    Raises:
        ValueError: if yaml file is empty
        e: empty file
        
    Returns:
        ConfigBox: ConfigBox tupe
    """
    try:
        with open(pathToYaml) as yamlFile:
            content = yaml.safe_load(yamlFile)
            logger.info(f"yaml file: {pathToYaml} loaded successfully")
            return ConfigBox(content)
    except BoxValueError:
        raise ValueError("Yaml file is empty")
    except Exception as e:
        raise e
    

@ensure_annotations
def createDir(pathToDir: list, verbose=True):
    """Create list of Directories

    Args:
        pathToDir (list): list of path os directories
        ignore_log (bool, optional): ignore if multiple dirs to be created. Defaults to False.
    """
    for path in pathToDir:
        os.makedirs(path,exist_ok=True)
        if verbose:
            logger.info(f"Created director at: {path}")
    

@ensure_annotations
def getFileSize(filePath: Path) -> str:
    """get size of file in KB

    Args:
        filePath (Path): path to the file

    Returns:
        str: size in KB
    """
    sizeInKb = round(os.path.getsize(filePath)/1024)
    return f"~ {sizeInKb} KB"
