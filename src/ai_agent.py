"""
This module defines the AIAgent class,
which generates an AI Agent and keeps the history of interactions.
It inherits from AsyncSingletonPromptExecutor,
allowing it to execute prompts asynchronously while maintaining a singleton instance.
The AIAgent class also includes logging capabilities for debugging purposes.
"""
import os
import logging
import json
from src.ai_client import AsyncSingletonPromptExecutor
from src.db_client import MongoDBClient

class AIAgent(AsyncSingletonPromptExecutor):
    """
    Generates an AI Agent and keeps the history

    Args:
        AsyncSingletonPromptExecutor: The parent class for executing prompts.
        MongoDBClient: The parent class for interacting with MongoDB.
    """
    def __init__(
            self,
            logger=logging.getLogger(__name__),
            agent_id: str = "default_agent"
        ):
        self.logger = logger
        super().__init__(logger=self.logger)
        self.db_client = MongoDBClient(logger=self.logger)
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.collection = os.getenv("MONGO_COLLECTION_HISTORY")
        self.messages = []
        self.agent_id = agent_id

    async def get_response(self, prompt: str) -> str:
        """
        Execute a prompt and return the response.

        Args:
            prompt (str): The prompt to execute.

        Returns:
            str: The response from the AI model.
        """
        self.logger.info("Executing prompt: %s", prompt)
        await super().init(max_concurrent_calls=1)
        response, self.messages = await super().execute_prompt(prompt, self.messages)
        self.logger.info("Received response: %s", response)
        await self.save_history()
        return response

    async def save_history(self) -> None:
        """
        Save the chat history to a file.
        """
        try:
            await self.db_client.insert_prompt_history(
                collection_name=self.collection,
                agent_id=self.agent_id,
                prompt=json.dumps(self.messages)
            )
        except (OSError, ValueError, TypeError) as e:
            self.logger.error("Error saving chat history: %s", e)

    async def update_history(self) -> None:
        """
        Retrieve the chat history from the database.

        Returns:
            list[dict[str, str]]: The chat history as a list of dictionaries.
        """
        try:
            history = await self.db_client.get_last_agent_history(
                collection_name=self.collection,
                agent_id=self.agent_id
            )
            self.messages = history.get("prompt", [])
            self.logger.info("Chat history updated successfully.")
        except (OSError, ValueError, TypeError) as e:
            self.logger.error("Error retrieving chat history: %s", e)
