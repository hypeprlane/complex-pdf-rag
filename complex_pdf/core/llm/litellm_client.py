import logging
import os
from typing import Any, Dict, List, Optional

from litellm import completion, completion_cost

logger = logging.getLogger(__name__)


class LitellmConfigError(Exception):
    """Raised when required environment/configuration for litellm is missing."""


class CostTracker:
    """Track costs across multiple API calls."""

    def __init__(self):
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.cost_breakdown = []

    def add_call(
        self, response: Dict[str, Any], model_name: str, call_type: str = "unknown"
    ):
        """Add cost information from a single API call."""
        try:
            # Calculate cost using LiteLLM's completion_cost function
            cost = completion_cost(completion_response=response)

            # Extract token usage
            usage = response.get("usage", {})
            prompt_tokens = usage.get("prompt_tokens", 0)
            completion_tokens = usage.get("completion_tokens", 0)
            total_tokens = usage.get("total_tokens", 0)

            # Update totals
            self.total_cost += cost
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
            self.total_tokens += total_tokens
            self.call_count += 1

            # Store breakdown
            self.cost_breakdown.append(
                {
                    "call_type": call_type,
                    "model": model_name,
                    "cost": cost,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                }
            )

            logger.info(
                f"API Call Cost: ${cost:.6f} | "
                f"Tokens: {prompt_tokens}p + {completion_tokens}c = {total_tokens}t | "
                f"Model: {model_name} | Type: {call_type}"
            )

        except Exception as e:
            logger.warning(f"Could not calculate cost for call: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all costs."""
        return {
            "total_cost": self.total_cost,
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": self.total_tokens,
            "call_count": self.call_count,
            "cost_breakdown": self.cost_breakdown,
        }

    def reset(self):
        """Reset all cost tracking."""
        self.total_cost = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_tokens = 0
        self.call_count = 0
        self.cost_breakdown = []


class LitellmClient:
    """
    A generic wrapper around litellm.completion with cost tracking.

    Responsibilities:
    1. Read credentials from environment (or raise if missing).
    2. Expose a .chat(...) method that accepts ANY well‐formed "messages" payload.
    3. (Optional) Allow customizing model_name, defaulting to a sensible value.
    4. Log requests and responses uniformly.
    5. Track costs across all API calls.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        provider: Optional[str] = None,
    ) -> None:
        """
        Args:
            model_name: The default model you want to call (e.g. "gpt-4o").
                        If None, you must pass model_name in chat().
            provider: The provider to use (e.g., "openai", "azure", "anthropic").
                      If None, will be inferred from model_name or environment.

        """
        self.model_name = model_name
        self.provider = provider
        self.cost_tracker = CostTracker()

        # Check if we have the basic requirements for litellm
        if not self._has_valid_config():
            raise LitellmConfigError(
                "Missing required environment variables. Please set appropriate "
                "API keys for your chosen provider (e.g., OPENAI_API_KEY, "
                "ANTHROPIC_API_KEY, etc.) before instantiating LitellmClient."
            )

        logger.info(
            "LitellmClient initialized (provider=%s, model=%s)",
            self.provider or "<auto>",
            self.model_name or "<none>",
        )

    def _has_valid_config(self) -> bool:
        """Check if we have valid configuration for any supported provider."""
        # Common API key environment variables
        api_keys = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GOOGLE_API_KEY",
            "AZURE_OPENAI_KEY",
            "COHERE_API_KEY",
            "TOGETHER_API_KEY",
        ]

        # Check if at least one API key is set
        has_api_key = any(os.getenv(key) for key in api_keys)

        # For Azure, also check for endpoint and version
        if os.getenv("AZURE_OPENAI_KEY"):
            has_azure_config = os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv(
                "AZURE_OPENAI_API_VERSION"
            )
            if not has_azure_config:
                logger.warning(
                    "AZURE_OPENAI_KEY found but missing AZURE_OPENAI_ENDPOINT "
                    "or AZURE_OPENAI_API_VERSION"
                )
                return False

        return has_api_key

    def chat(
        self,
        messages: List[Dict[str, Any]],
        *,
        model_name: Optional[str] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        call_type: str = "chat",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Send a chat-style request to litellm.completion with cost tracking.

        Args:
            messages: A list of dicts matching litellm's expected "messages" format.
                      e.g. [
                              {
                                "role": "user",
                                "content": [
                                  {"type": "text", "text": "Hello"},
                                  {"type": "image_url",
                                   "image_url": {"url": "..."}}
                                ]
                              }
                           ]
            model_name: Override the client's default model_name. If neither is set,
                       raises.
            temperature, top_p, max_tokens, etc.: Passed through to
            litellm.completion.
            call_type: Label for cost tracking (e.g., "query_decomposition", "answer_generation")
            **kwargs: Any other litellm.completion parameters (stream=True, etc.).

        Returns:
            The parsed JSON/dict response from litellm.completion.

        Raises:
            LitellmConfigError: if no model_name was provided anywhere.
            Exception: if completion() itself fails.
        """
        chosen_model = model_name or self.model_name
        if not chosen_model:
            raise LitellmConfigError(
                "No model_name specified. Either pass it to __init__ or to chat()."
            )

        payload: Dict[str, Any] = {"model": chosen_model, "messages": messages}
        # Optionally add other parameters if provided
        if temperature is not None:
            payload["temperature"] = temperature
        if top_p is not None:
            payload["top_p"] = top_p
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        # Merge any additional kwargs
        payload.update(kwargs)

        logger.debug("Sending payload to litellm: %s", payload)

        try:
            response = completion(**payload)
            logger.debug("Received response from litellm: %s", response)

            # Track cost for this call
            self.cost_tracker.add_call(response, chosen_model, call_type)

            return response
        except Exception as ex:
            logger.exception("Error while calling litellm.completion: %s", ex)
            raise

    def get_cost_summary(self) -> Dict[str, Any]:
        """Get a summary of all costs tracked by this client."""
        return self.cost_tracker.get_summary()

    def reset_cost_tracking(self):
        """Reset cost tracking for this client."""
        self.cost_tracker.reset()


# Example usage within this module (but typically you'd import LitellmClient elsewhere):
if __name__ == "__main__":
    # (For demonstration—won't run unless you call python …/client.py)

    try:
        client = LitellmClient(model_name="gpt-4o")
    except LitellmConfigError as e:
        logger.error("Configuration problem: %s", e)
        exit(1)

    test_messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": "Say hello in JSON."}],
        }
    ]
    resp = client.chat(
        test_messages,
        temperature=0.7,
        max_tokens=64,
        call_type="test",
    )
    recommendations_resp_string = resp.choices[0].message.content
    # recommendations_resp_json = json.loads(recommendations_resp_string)
    print(recommendations_resp_string)

    # Print cost summary
    cost_summary = client.get_cost_summary()
    print(f"\n💰 Total Cost: ${cost_summary['total_cost']:.6f}")
    print(f"📊 Total Tokens: {cost_summary['total_tokens']}")
    print(f"📞 Total Calls: {cost_summary['call_count']}")
