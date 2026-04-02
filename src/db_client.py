"""
MongoDB client module for connecting to a MongoDB database and performing operations
such as inserting prompt history. This module defines the MongoDBClient class,
which provides methods for connecting to the database, retrieving collections,
and inserting documents. The class is designed to handle connection errors and
ensure that the database client is properly closed after operations.
"""
import os
import logging
import datetime
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient

class MongoDBClient:
    """
    Client for connecting to a MongoDB database
    and performing operations such as inserting prompt history.
    """
    _instance = None # Singleton instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
        return cls._instance

    def __init__(
            self,
            logger=logging.getLogger(__name__),
            *args,
            **kwargs):
        if getattr(self, '_initialized', False):
            return # Avoid reinitialization in singleton pattern
        self._initialized = True
        self._client = None # MongoDB client instance
        self.logger = logger
        self.username = os.getenv("MONGO_USER")
        self.password = os.getenv("MONGO_PASSWORD")
        self.host = os.getenv("MONGO_HOST", "localhost")
        self.port = os.getenv("MONGO_PORT", "27017")
        self.database_name = os.getenv("MONGO_DB", "ai_agents_db")
        super().__init__(*args, **kwargs)

    def get_client(self) -> MongoClient:
        """Create and return a MongoDB client instance."""
        if self._client is not None:
            return self._client
        try:
            uri = f"mongodb://{self.username}:{self.password}@{self.host}:{self.port}/?authSource={self.username}"
            self._client = MongoClient(uri)
            self.logger.info("Successfully connected to MongoDB at %s:%s", self.host, self.port)
            return self._client
        except Exception as e:
            self.logger.error("Failed to connect to MongoDB: %s", e)
            raise ConnectionError(f"Failed to connect to MongoDB: {e}") from e

    def get_database(self) -> MongoClient:
        """Get the specified database from the MongoDB client."""
        client = self.get_client()
        return client[self.database_name]

    def get_collection(self, collection_name: str) -> MongoClient:
        """Get a specific collection from the database."""
        db = self.get_database()
        return db[collection_name]

    async def close_client(self) -> None:
        """Close the MongoDB client connection."""
        try:
            await self._client.close()
            self.logger.info("MongoDB client connection closed successfully.")
            self._client = None
        except Exception as e:
            raise ConnectionError(f"Failed to close MongoDB client: {e}") from e

    async def insert_agent(
            self,
            collection_name: str,
            agent_id: str
        ) -> None:
        """Insert a new agent document into the specified collection."""
        collection = self.get_collection(collection_name)
        document = {
            "agent_id": agent_id,
            "created_at": datetime.datetime.now()
        }
        try:
            result_id = await collection.insert_one(document)
            self.logger.info(
                "Inserted document with ID: %s into collection: %s",
                result_id.inserted_id,
                collection_name
            )
        except Exception as e:
            self.logger.error("Failed to insert document into MongoDB: %s", e)
            raise RuntimeError(f"Failed to insert document into MongoDB: {e}") from e

    async def get_agent_ids(
            self,
            collection_name: str
        ) -> list[str]:
        """Retrieve an agent document by its ID from the specified collection."""
        collection = self.get_collection(collection_name)
        try:
            agent_list = await collection.distinct("agent_id")
            if agent_list is None:
                self.logger.warning("No documents found in collection: %s", collection_name)
                raise ValueError(f"No documents found in collection: {collection_name}")
            self.logger.info(
                "Retrieved agent IDs from collection: %s",
                collection_name
            )
            return agent_list
        except Exception as e:
            self.logger.error("Failed to retrieve documents from MongoDB: %s", e)
            raise RuntimeError(f"Failed to retrieve documents from MongoDB: {e}") from e

    async def insert_prompt_history(
            self,
            collection_name: str,
            agent_id: str,
            prompt: str
        ) -> None:
        """Insert a prompt and response history into the specified collection."""
        collection = self.get_collection(collection_name)
        document = {
            "agent_id": agent_id,
            "prompt": prompt,
            "timestamp": datetime.datetime.now()
        }
        try:
            result_id = await collection.insert_one(document)
            self.logger.info(
                "Inserted document with ID: %s into collection: %s",
                result_id.inserted_id,
                collection_name
            )
        except Exception as e:
            self.logger.error("Failed to insert document into MongoDB: %s", e)
            raise RuntimeError(f"Failed to insert document into MongoDB: {e}") from e

    async def get_last_agent_history(
            self,
            collection_name: str,
            agent_id: str
        ) -> list[dict]:
        """Retrieve the last prompt history for a specific agent."""
        collection = self.get_collection(collection_name)
        try:
            history = await collection.find(
                {
                    "agent_id": agent_id
                },
                sort=[("timestamp", -1)]
            )
            self.logger.info(
                "Retrieved %d documents for agent_id: %s from collection: %s",
                len(history),
                agent_id,
                collection_name)
            return history.get("prompt", [])
        except Exception as e:
            self.logger.error("Failed to retrieve documents from MongoDB: %s", e)
            raise RuntimeError(f"Failed to retrieve documents from MongoDB: {e}") from e
