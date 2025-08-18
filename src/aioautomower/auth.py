import orjson
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Auth:
    def __init__(self, token):
        self.token = token

    def parse_response(self, response):
        logger.info("Parsing response...")
        try:
            data = orjson.loads(response)
            logger.info("Response parsed successfully.")
            return data
        except orjson.JSONDecodeError as e:
            logger.error(f"Failed to parse response: {e}")
            return None

    def log_response(self, response):
        parsed_data = self.parse_response(response)
        if parsed_data:
            logger.info(f"Parsed Data: {parsed_data}")
        else:
            logger.warning("No data was parsed from the response.")
