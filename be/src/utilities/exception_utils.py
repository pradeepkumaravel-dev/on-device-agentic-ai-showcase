import logging

logger = logging.getLogger(__name__)

class NormalExceptions(Exception):
    def __init__(self, message:str, error:str, log:bool=False):
        self.message = message 
        self.error = error 
        if log:
            logger.error("Error occurred, log will be posted to database")