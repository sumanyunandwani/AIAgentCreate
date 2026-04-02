import os
import logging

class AIStorage:
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        self.dir_path = os.path.dirname(os.path.realpath(__file__))

    def create_agent(self, agent_id: str) -> str:
        """
        Create a new AI agent's state file.

        Args:
            agent_id (str): The unique identifier for the AI agent.
        """
        try:
            file_path = os.path.join(self.dir_path, "agents", f"{agent_id}.json")
            open(file_path, encoding="utf-8", mode="w+").close()
            return file_path
        except Exception as e:
            raise ValueError(f"Error creating agent state: {e}") from e
