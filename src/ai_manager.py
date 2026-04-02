"""
AIManager is responsible for managing the creation and retrieval of AI agents.
It interacts with a MongoDB database to store and retrieve agent information.
The class provides methods to load existing agents,
create new agents, and retrieve agents by their ID.
"""
import os
import logging
from src.ai_agent import AIAgent
from src.db_client import MongoDBClient

class AIManager(MongoDBClient):
    """
    Manages the creation and retrieval of AI agents.

    Args:
        MongoDBClient (_type_): The parent class for interacting with MongoDB.
    """
    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger
        super().__init__(logger=self.logger)
        self.dir_path = os.path.dirname(os.path.realpath(__file__))
        self.agent_collection = os.getenv("MONGO_COLLECTION_AGENTS")
        self.agents = {}

    async def load_agents(self) -> None:
        """
        Load existing agents from the agents.json file.
        If the file does not exist, it initializes an empty agents dictionary.
        """
        if self.agents:
            return
        agent_ids = await self.get_agent_ids(self.agent_collection)
        for agent_id in agent_ids:
            self.agents[agent_id] = AIAgent(logger=self.logger, agent_id=agent_id)
            self.agents[agent_id].update_history()

    async def dump_agent(self, agent_id: str) -> None:
        """
        Dump the current agents to the agents.json file.
        This method is called whenever a new agent is created to persist the updated agents list.
        """
        try:
            await super().insert_agent(
                collection_name=self.agent_collection,
                agent_id=agent_id
            )
            self.logger.info(
                "Agent %s dumped successfully to collection: %s",
                agent_id,
                self.agent_collection
            )
        except (ValueError, RuntimeError) as e:
            self.logger.error(
                "Failed to dump agent %s: %s",
                agent_id,
                e
            )

    async def create_agent(self, agent_id: str) -> AIAgent:
        """
        Creates a new AI agent with the specified ID.

        Args:
            agent_id (str): The unique identifier for the AI agent to be created.

        Raises:
            ValueError: If an agent with the specified ID already exists.

        Returns:
            AIAgent: The newly created AI agent.
        """
        # Reload agents to ensure we have the latest data before creating a new agent
        await self.load_agents()

        # Check if the agent already exists
        if agent_id in self.agents:
            raise ValueError(f"Agent with ID {agent_id} already exists.")

        # Create a new agent
        agent = AIAgent(logger=self.logger, agent_id=agent_id)

        # Store the agent instance in the agents dictionary
        self.agents[agent_id] = agent

        # Dump the updated agents list to the file
        await self.dump_agent(agent_id=agent_id)

        return agent

    async def get_agent(self, agent_id: str) -> AIAgent:
        """
        Retrieves an existing AI agent by its ID.

        Args:
            agent_id (str): The unique identifier for the AI agent to be retrieved.

        Raises:
            ValueError: If an agent with the specified ID does not exist.

        Returns:
            AIAgent: The retrieved AI agent.
        """
        # Reload agents to ensure we have the latest data before retrieving an agent
        await self.load_agents()

        # Check if the agent exists
        if agent_id not in self.agents:
            raise ValueError(f"Agent with ID {agent_id} does not exist.")

        # Return the agent instance
        return self.agents[agent_id]
