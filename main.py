"""
Main module for the AI Agent API.
This module sets up the FastAPI application
and defines the API endpoints for creating and retrieving AI agents.
It uses the AIManager class to manage the lifecycle of AI agents
and handle interactions with the AI model and MongoDB database.
The API includes logging for debugging and error handling to ensure robust operation.
"""
import json
import uuid
import logging
from fastapi import FastAPI, Request, Response
from src.ai_manager import AIManager

app = FastAPI()
logger = logging.getLogger("ai_agent_api")
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

file_handler = logging.FileHandler("ai_agent_api.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

ai_manager = AIManager(logger=logger)

@app.post("/v1/agents")
async def create_agent(request: Request) -> Response:
    """
    Create a new AI agent and execute a prompt.    

    Args:
        request (Request): The incoming request containing the prompt for the AI agent.

    Returns:
        Response: A JSON response containing the agent ID
        and the response from the AI agent,
        or an error message if the operation fails.
    """
    request_json = await request.json()
    prompt = request_json.get("prompt", "Hello")
    agent_id = str(uuid.uuid4())
    agent = await ai_manager.create_agent(agent_id)
    response = await agent.get_response(prompt)
    if not response:
        return Response(
            content=json.dumps({"error": "Failed to get response from AI Agent."}),
            status_code=500,
            media_type="application/json"
        )
    return Response(
        content=json.dumps({"agent_id": agent_id, "response": response}),
        status_code=200,
        media_type="application/json"
    )

@app.get("/v1/agents/{agent_id}")
async def get_agent_response(agent_id: str, request: Request) -> Response:
    """
    Retrieve the response from a specific AI agent.

    Args:
        agent_id (str): The ID of the AI agent.
        request (Request): The incoming request containing the prompt for the AI agent.

    Returns:
        Response: A JSON response containing the agent ID
        and the response from the AI agent,
        or an error message if the operation fails.
    """
    request_json = await request.json()
    prompt = request_json.get("prompt", "Hello")
    try:
        agent = await ai_manager.get_agent(agent_id)
        response = await agent.get_response(prompt)
        if not response:
            return Response(
                content=json.dumps({"error": "Failed to get response from AI Agent."}),
                status_code=500,
                media_type="application/json"
            )
        return Response(
            content=json.dumps({"agent_id": agent_id, "response": response}),
            status_code=200,
            media_type="application/json"
        )
    except ValueError as e:
        return Response(
            content=json.dumps({"error": str(e)}),
            status_code=404,
            media_type="application/json"
        )
