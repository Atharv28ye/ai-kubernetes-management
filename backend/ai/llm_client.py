import httpx
import json
import os
import re
from typing import Dict, Any, Optional
from loguru import logger
import time


class LLMClient:
    """Client for interacting with OpenRouter LLM API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 90,
        max_retries: int = 3
    ):
        """
        Initialize LLM client.

        Args:
            api_key: OpenRouter API key.
            model: OpenRouter model name.
            timeout: Request timeout in seconds.
            max_retries: Maximum retry attempts.
        """

        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")

        self.model = model or os.getenv(
            "OPENROUTER_MODEL",
            "openrouter/free"
        )

        self.timeout = timeout
        self.max_retries = max_retries

        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

        if not self.api_key:
            logger.warning(
                "OPENROUTER_API_KEY not set - AI features will not work"
            )

        logger.info(
            f"LLM Client initialized with model: {self.model}"
        )

    # =========================================================
    # OPENROUTER REQUEST
    # =========================================================

    def _make_request(
        self,
        messages: list[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Make request to OpenRouter.
        """

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "AI Kubernetes Agent",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        for attempt in range(self.max_retries):

            try:
                logger.info(
                    f"Making LLM request "
                    f"(attempt {attempt + 1}/{self.max_retries})"
                )

                with httpx.Client(timeout=self.timeout) as client:

                    response = client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )

                    response.raise_for_status()

                    data = response.json()

                    logger.debug(
                        f"OpenRouter response received "
                        f"from model: "
                        f"{data.get('model', self.model)}"
                    )

                    # Log finish reason because this tells us
                    # whether the model was cut off.
                    choices = data.get("choices", [])

                    if choices:
                        finish_reason = choices[0].get(
                            "finish_reason"
                        )

                        logger.info(
                            f"LLM finish reason: "
                            f"{finish_reason}"
                        )

                        if finish_reason == "length":
                            logger.warning(
                                "LLM response reached the "
                                "maximum token limit"
                            )

                    return data

            except httpx.TimeoutException:

                logger.warning(
                    f"Request timeout on attempt "
                    f"{attempt + 1}"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(
                        "LLM request timed out after "
                        "all retries"
                    )

            except httpx.HTTPStatusError as e:

                logger.error(
                    f"HTTP error: {e.response.status_code} - "
                    f"{e.response.text}"
                )

                if e.response.status_code == 429:

                    if attempt < self.max_retries - 1:

                        wait_time = 5 + (2 ** attempt)

                        logger.info(
                            f"Rate limited. Waiting "
                            f"{wait_time} seconds"
                        )

                        time.sleep(wait_time)

                    else:
                        raise Exception(
                            "Rate limit exceeded after "
                            "all retries"
                        )

                else:

                    raise Exception(
                        f"LLM request failed: "
                        f"{e.response.status_code}"
                    )

            except httpx.RequestError as e:

                logger.error(
                    f"Request error: {str(e)}"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(
                        "LLM request failed after "
                        f"all retries: {str(e)}"
                    )

            except Exception as e:

                logger.error(
                    f"Unexpected error: {str(e)}"
                )

                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise Exception(
                        f"LLM request failed: {str(e)}"
                    )

        raise Exception("LLM request failed")

    # =========================================================
    # JSON PARSER
    # =========================================================

    def _parse_json_response(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Parse JSON returned by the model.

        Handles:

        1. Normal JSON
        2. Markdown JSON blocks
        3. JSON surrounded by text
        4. Nested JSON
        5. Partially truncated JSON
        """

        if not content:
            return {}

        content = content.strip()

        # -----------------------------------------------------
        # 1. Direct JSON
        # -----------------------------------------------------

        try:

            parsed = json.loads(content)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        # -----------------------------------------------------
        # 2. Remove markdown fences
        # -----------------------------------------------------

        cleaned = re.sub(
            r"^```(?:json)?\s*",
            "",
            content,
            flags=re.IGNORECASE
        )

        cleaned = re.sub(
            r"\s*```$",
            "",
            cleaned
        )

        cleaned = cleaned.strip()

        try:

            parsed = json.loads(cleaned)

            if isinstance(parsed, dict):
                return parsed

        except json.JSONDecodeError:
            pass

        # -----------------------------------------------------
        # 3. Extract complete JSON object from surrounding text
        # -----------------------------------------------------

        first_brace = cleaned.find("{")
        last_brace = cleaned.rfind("}")

        if first_brace != -1 and last_brace > first_brace:

            possible_json = cleaned[
                first_brace:last_brace + 1
            ]

            try:

                parsed = json.loads(possible_json)

                if isinstance(parsed, dict):
                    return parsed

            except json.JSONDecodeError:
                pass

        # -----------------------------------------------------
        # 4. Attempt recovery from truncated JSON
        # -----------------------------------------------------

        recovered = self._recover_partial_json(cleaned)

        if recovered:
            logger.warning(
                "Recovered useful fields from "
                "partially truncated LLM JSON"
            )

            return recovered

        # -----------------------------------------------------
        # 5. Nothing recoverable
        # -----------------------------------------------------

        logger.warning(
            "Could not parse LLM response as JSON"
        )

        logger.debug(
            f"Raw LLM response: {content[:4000]}"
        )

        return {
            "raw_response": content
        }

    # =========================================================
    # PARTIAL JSON RECOVERY
    # =========================================================

    def _recover_partial_json(
        self,
        content: str
    ) -> Dict[str, Any]:
        """
        Recover important diagnosis fields from incomplete JSON.

        This is useful when a free model reaches its token limit
        in the middle of a JSON response.
        """

        recovered: Dict[str, Any] = {}

        # -----------------------------------------------------
        # String fields
        # -----------------------------------------------------

        string_fields = [
            "root_cause",
            "rootCause",
            "cause",
            "diagnosis",
            "explanation",
            "reason",
            "details",
            "prevention",
            "confidence_reasoning",
            "reasoning",
        ]

        for field in string_fields:

            pattern = (
                rf'"{re.escape(field)}"\s*:\s*"'
                rf'((?:\\.|[^"\\])*)'
            )

            match = re.search(
                pattern,
                content,
                flags=re.DOTALL
            )

            if match:

                try:

                    value = json.loads(
                        '"' + match.group(1) + '"'
                    )

                except Exception:

                    value = match.group(1)

                if value:
                    recovered[field] = value

        # -----------------------------------------------------
        # Confidence
        # -----------------------------------------------------

        confidence_match = re.search(
            r'"(?:confidence|confidence_score)"\s*:\s*'
            r'([0-9]+(?:\.[0-9]+)?)',
            content
        )

        if confidence_match:

            try:
                recovered["confidence"] = float(
                    confidence_match.group(1)
                )
            except ValueError:
                pass

        # -----------------------------------------------------
        # Array fields
        # -----------------------------------------------------

        array_fields = [
            "fix",
            "suggested_fix",
            "recommendation",
            "recommendations",
            "kubectl_commands",
            "commands",
        ]

        for field in array_fields:

            pattern = (
                rf'"{re.escape(field)}"\s*:\s*\['
                rf'(.*?)(?=\]\s*,|\]\s*}}|$)'
            )

            match = re.search(
                pattern,
                content,
                flags=re.DOTALL
            )

            if not match:
                continue

            array_content = match.group(1)

            items = re.findall(
                r'"((?:\\.|[^"\\])*)"',
                array_content
            )

            if items:

                parsed_items = []

                for item in items:

                    try:

                        parsed_items.append(
                            json.loads('"' + item + '"')
                        )

                    except Exception:

                        parsed_items.append(item)

                recovered[field] = parsed_items

        return recovered

    # =========================================================
    # COMPLETION
    # =========================================================

    def generate_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4000
    ) -> Dict[str, Any]:
        """
        Generate completion from OpenRouter.
        """

        if not self.api_key:

            return {
                "success": False,
                "error": "OPENROUTER_API_KEY not configured",
                "content": None
            }

        try:

            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]

            logger.info("Sending request to LLM")

            response = self._make_request(
                messages,
                temperature,
                max_tokens
            )

            choices = response.get("choices", [])

            if not choices:
                raise Exception(
                    "OpenRouter returned no choices"
                )

            choice = choices[0]

            message = choice.get(
                "message",
                {}
            )

            content = message.get(
                "content",
                ""
            )

            # Some OpenRouter models return content as a list.
            if isinstance(content, list):

                text_parts = []

                for item in content:

                    if isinstance(item, dict):

                        text = item.get("text")

                        if text:
                            text_parts.append(text)

                    elif isinstance(item, str):

                        text_parts.append(item)

                content = "".join(text_parts)

            if not isinstance(content, str):
                content = str(content)

            logger.debug(
                f"LLM raw response: {content[:4000]}"
            )

            # -------------------------------------------------
            # Check whether response was truncated.
            # -------------------------------------------------

            finish_reason = choice.get(
                "finish_reason"
            )

            if finish_reason == "length":

                logger.warning(
                    "LLM response was truncated because "
                    "max_tokens was reached"
                )

            # -------------------------------------------------
            # Parse response.
            # -------------------------------------------------

            parsed_content = self._parse_json_response(
                content
            )

            # -------------------------------------------------
            # Detect whether useful diagnosis fields exist.
            # -------------------------------------------------

            useful_fields = [
                "root_cause",
                "rootCause",
                "cause",
                "diagnosis",
                "explanation",
                "fix",
                "kubectl_commands",
                "prevention",
                "confidence",
            ]

            has_useful_content = any(
                field in parsed_content
                for field in useful_fields
            )

            if not has_useful_content:

                logger.warning(
                    "LLM response did not contain "
                    "recognizable diagnosis fields"
                )

            else:

                logger.info(
                    "Successfully extracted diagnosis "
                    "fields from LLM response"
                )

            logger.info(
                "LLM request successful"
            )

            return {
                "success": True,
                "content": parsed_content,
                "raw_content": content,
                "model": response.get(
                    "model",
                    self.model
                ),
                "finish_reason": finish_reason,
                "usage": response.get(
                    "usage",
                    {}
                )
            }

        except Exception as e:

            logger.error(
                f"LLM generation failed: {str(e)}"
            )

            return {
                "success": False,
                "error": str(e),
                "content": None
            }

    # =========================================================
    # STREAMING
    # =========================================================

    def generate_streaming_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Generate completion.

        Currently uses normal non-streaming request.
        """

        return self.generate_completion(
            system_prompt,
            user_prompt,
            temperature
        )

    # =========================================================
    # HEALTH CHECK
    # =========================================================

    def health_check(self) -> Dict[str, Any]:
        """
        Check LLM configuration.
        """

        return {
            "configured": bool(self.api_key),
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }