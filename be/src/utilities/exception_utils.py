import logging

logger = logging.getLogger(__name__)

class NormalExceptions(Exception):
    def __init__(self, message:str, error:str, log:bool=False):
        self.message = message 
        self.error = error 
        if log:
            # Should implement a db logging logic here.
            # Skipped for now as it's fully local solution and it's the beta version
            logger.error("Error occurred, log will be posted to database")