"""
This module provides an asynchronous singleton class to execute prompts using OpenAI's API.
It uses a semaphore to limit the number of concurrent calls to the API.
It is designed to be initialized with a maximum number of concurrent calls,
and it allows for executing prompts with an optional chat history.
It is designed to be used in an asynchronous environment, allowing for efficient
execution of multiple prompts without blocking the event loop.
"""
import os
import asyncio
import logging
from typing import Optional, List, Dict
from huggingface_hub import InferenceClient

# Ensure that the Hugging Face API key is set in the environment
client = InferenceClient(token=os.getenv("HF_TOKEN"))

class AsyncSingletonPromptExecutor:
    """
    A singleton class to execute prompts using OpenAI's API with concurrency control.
    This class ensures that only one instance exists and provides a method to execute prompts
    with a semaphore to limit the number of concurrent calls.
    
    Methods:
        execute_prompt(
            prompt: str, 
            chat_history: Optional[List[Dict[str, str]]] = None
        ) -> tuple[str, List[Dict[str, str]]]:
            Executes a prompt using OpenAI's API with concurrency control.

    """
    _instance = None
    _lock = asyncio.Lock()  # Lock for thread-safe singleton instantiation

    def __new__(cls, *args, **kwargs) -> 'AsyncSingletonPromptExecutor':

        # Asynchronous singleton enforcement
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, logger: Optional[logging.Logger] = None, *args, **kwargs) -> None:
        """
        Initialize the singleton instance.
        This method sets up the semaphore and initializes the chat model and token count.
        """
        # Ensure that the singleton is initialized only once
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._semaphore = None
            self._model = None
            self.logger = logger or logging.getLogger(__name__)
            super().__init__(*args, **kwargs)

    async def init(self, max_concurrent_calls : int = 1) -> None:
        """        
        Initialize the singleton instance with a semaphore to limit concurrent calls.
        Args:
            max_concurrent_calls (int): Maximum number of concurrent calls allowed.
        """
        # Ensure that the semaphore is initialized only once
        async with self._lock:
            if self._semaphore is None:
                self.logger.info("Initializing AsyncSingleton...")
                self._semaphore = asyncio.Semaphore(max_concurrent_calls)
                self._model = "meta-llama/Llama-3.1-8B-Instruct:fastest"
                self.logger.debug(
                    "Semaphore initialized with max_concurrent_calls: %d",
                    max_concurrent_calls)
                self.logger.debug("Model set to: %s", self._model)

    async def execute_prompt(
            self, prompt: str,
            chat_history: Optional[List[Dict[str, str]]] = None
        ) -> tuple[str, List[Dict[str, str]]]:
        """Execute a prompt using OpenAI's API with concurrency control.
        
        Args:
            prompt (str): The prompt to be executed.
            chat_history (list[dict[str: str]]): The chat history to maintain context.
        Returns:
            tuple[str, list[dict[str: str]]]: 
            The previous responses from the OpenAI API and the updated chat history.
        Raises:
            Exception: If there is an error during the API call.
        """
        async with self._semaphore:

            # Prepare the chat history for the prompt
            if chat_history is None or len(chat_history) == 0:

                self.logger.debug("No chat history provided, starting with a system message.")
                # If no chat history, start with a system message
                messages = [{"role": "system", "content": "You are a helpful assistant."}]

            else:

                self.logger.debug("Using existing chat history.")
                # If chat history exists, use it as the context
                messages = chat_history.copy()

            # Append the user prompt to the messages
            messages.append({"role": "user", "content": prompt})

            try:

                self.logger.debug("Executing prompt with LLama API.: %s", prompt)
                # Call the LLama API to get the response
                response = client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    stream=False,
                    temperature=0.7
                )

                self.logger.info(response)
                # Append the assistant's response to the messages
                messages.append({
                    "role": "assistant",
                    "content": response.choices[0].message.content
                })

                # Return the assistant's response and the updated chat history
                self.logger.debug("Prompt executed successfully.")
                return str(response.choices[0].message.content), messages

            except (ValueError, ConnectionError, TimeoutError) as e:

                # Handle any exceptions that occur during the API call
                self.logger.debug("Error executing prompt: %s", e)
                return str(e), messages
