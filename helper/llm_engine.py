import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from a .env file (for the API key)
load_dotenv()

# Set up a logger for monitoring
logger = logging.getLogger("llm_engine")
logger.setLevel(logging.INFO)

class LLMEngine:
    def __init__(self, model: str = "gpt-oss-120b"):
        """
        Initialize the LLM engine to use the Hugging Face Inference API.

        Args:
            model (str): The identifier of the model to use on the Hub.
                         The provider can be added, e.g., "mistralai/Mistral-7B-Instruct-v0.2:featherless-ai".
        """
        self.model = model
        self.client = self._initialize_client()
        if self.client:
            logger.info(f"LLM Engine initialized successfully for model: {self.model}")

    def _initialize_client(self):
        """Initializes the OpenAI client to point to Hugging Face's API."""
        try:
            # Get the Hugging Face token from environment variables
            api_key = os.environ.get("CEREBRAS_API_KEY")
            if not api_key:
                raise ValueError("CEREBRAS_API_KEY environment variable not found.")

            client = OpenAI(
                base_url="https://api.cerebras.ai/v1",
                api_key=api_key,
            )
            return client
        except Exception as e:
            logger.error(f"Error initializing OpenAI client for Hugging Face: {e}")
            return None

    def run(self, messages: list, max_tokens: int = 15360) -> str:
        """
        Run the inference by making an API call.

        Args:
            messages (list): A list of dictionaries in chat format.
            max_tokens (int): The maximum number of tokens to generate.

        Returns:
            str: The generated text content from the assistant.
        """
        logger.info(f"Running remote inference for model {self.model}...")
        if not self.client:
            raise RuntimeError("Client is not initialized. Please check initialization logs for errors.")

        # Default generation parameters can be overridden by kwargs
        generation_args = {
            "temperature": 0,
            "top_p": 0.95,
        }

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                **generation_args,
            )
            # Extract the content from the response object
            response = completion.choices[0].message.content
            logger.info("Remote inference completed successfully.")
            return response
        except Exception as e:
            logger.error(f"An error occurred during API call: {e}")
            return None