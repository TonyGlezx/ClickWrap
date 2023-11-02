from requests.exceptions import HTTPError, RequestException, Timeout
import time
from collections import deque
import logging
import requests

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RateLimitExceeded(Exception):
    """Custom exception for rate limit exceeded."""

class APIRequestHandler:
    def __init__(self, token, base_url="https://api.clickup.com/api/v2", limit=100, retries=3, backoff_factor=1.5, request_lib=requests):
        self.token = token
        self.base_url = base_url
        self.limit = limit
        self.retries = retries
        self.backoff_factor = backoff_factor
        self.request_timestamps = deque()
        self.request_lib = request_lib
        logger.debug("APIRequestHandler initialized with token, base URL, rate limit, retries, and backoff factor.")

    def _is_rate_limited(self):
        now = time.time()
        while self.request_timestamps and now - self.request_timestamps[0] > 60:
            self.request_timestamps.popleft()
        return len(self.request_timestamps) >= self.limit

    def _make_request(self, endpoint, method="GET", headers=None, json=None, params=None):
        logger.info(f"Making a {method} request to endpoint: {endpoint}")
        if self._is_rate_limited():
            logger.error(f"You have exceeded the rate limit of {self.limit} requests per minute.")
            raise RateLimitExceeded(f"You have exceeded the rate limit of {self.limit} requests per minute.")

        url = f"{self.base_url}{endpoint}"
        headers = headers or {}
        headers["Authorization"] = self.token
        headers["Content-Type"] = "application/json"

        for attempt in range(self.retries):
            try:
                response = self.request_lib.request(method, url, headers=headers, json=json, params=params)
                response.raise_for_status()
                self.request_timestamps.append(time.time())
                logger.debug(f"Request successful. Response received: {response.json()}")
                return response.json()
            except (HTTPError, Timeout) as e:
                logger.error(f"HTTP Error or Timeout occurred: {e}")
                if attempt < self.retries - 1:
                    sleep_time = self.backoff_factor * (2 ** attempt)
                    logger.debug(f"Retrying after {sleep_time} seconds...")
                    time.sleep(sleep_time)
                    continue
                else:
                    raise
            except json.JSONDecodeError:
                logger.error("Error decoding the JSON response from the server.")
                raise
            except ConnectionError:
                logger.error("A network problem occurred, like refused connection or DNS failure.")
                raise
            except RequestException as e:
                logger.error(f"Request Exception occurred: {e}")
                raise
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                raise


    def _create_resource(self, endpoint, resource_name, **kwargs):
        """Abstract method to create a resource (folder, list, task)."""
        logger.info(f"Creating resource: {resource_name} at endpoint: {endpoint}")
        payload = {"name": resource_name}
        payload.update(kwargs)
        return self._make_request(endpoint, method="POST", json=payload)


class ClickUpAPI(APIRequestHandler):

    def create_folder(self, space_id, folder_name):
        logger.info(f"Creating folder: {folder_name} in space: {space_id}")
        endpoint = f"/space/{space_id}/folder"
        return self._create_resource(endpoint, folder_name)

    def create_list(self, folder_id, list_name, **kwargs):
        logger.info(f"Creating list: {list_name} in folder: {folder_id}")
        endpoint = f"/folder/{folder_id}/list"
        return self._create_resource(endpoint, list_name, **kwargs)

    def create_task(self, list_id, task_name, **kwargs):
        logger.info(f"Creating task: {task_name} in list: {list_id}")
        endpoint = f"/list/{list_id}/task"
        return self._create_resource(endpoint, task_name, **kwargs)

    def create_subtask(self, parent_task_id, list_id, subtask_name):
        logger.info(f"Creating subtask: {subtask_name} for parent task: {parent_task_id} in list: {list_id}")
        endpoint = f"/list/{list_id}/task"
        return self._create_resource(endpoint, subtask_name, parent=parent_task_id)
