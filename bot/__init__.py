from config import api_key
from typing import Dict, Tuple, Any, Generator
from openai import Client, BadRequestError, PermissionDeniedError, AuthenticationError
from openai.types.chat.chat_completion import ChatCompletion