"""
Claude API integration for generating executive summary emails.
Supports single-client and parallel batch generation.
"""

import asyncio
import logging
import os
import time
from typing import Callable, Optional

import anthropic
from dotenv import load_dotenv

from models import Client
from prompt_builder import build_prompt

logger = logging.getLogger(__name__)

load_dotenv()

MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096
MAX_CONCURRENT = 5
MAX_RETRIES = 3


def _get_client() -> anthropic.Anthropic:
    """Get an Anthropic client. Checks Streamlit secrets first, then .env."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    # Also check Streamlit secrets (for cloud deployment)
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("ANTHROPIC_API_KEY")
        except Exception:
            pass
    if not api_key:
        raise ValueError(
            "ANTHROPIC_API_KEY not found. "
            "Set it in Streamlit secrets or create a .env file with: ANTHROPIC_API_KEY=sk-ant-..."
        )
    return anthropic.Anthropic(api_key=api_key)


def generate_summary(
    client: Client,
    greeting: str = "Morning",
    custom_instructions: str = "",
    diff_data: dict = None,
) -> str:
    """Generate a single executive summary email for a client."""
    system_prompt, user_message = build_prompt(
        client, greeting, custom_instructions=custom_instructions, diff_data=diff_data
    )

    anthropic_client = _get_client()

    for attempt in range(MAX_RETRIES):
        try:
            response = anthropic_client.messages.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            return response.content[0].text
        except anthropic.RateLimitError:
            wait = 2 ** attempt
            logger.warning(f"Rate limited, retrying in {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
        except anthropic.APIError as e:
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** attempt
                logger.warning(f"API error: {e}. Retrying in {wait}s (attempt {attempt + 1})")
                time.sleep(wait)
            else:
                raise

    raise RuntimeError(f"Failed to generate summary for {client.company_name} after {MAX_RETRIES} retries")


async def generate_all(
    clients: list[Client],
    greeting: str = "Morning",
    custom_instructions: str = "",
    diff_data: dict = None,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> dict[str, str]:
    """Generate summaries for all clients in parallel.

    Args:
        clients: List of Client objects to generate for.
        greeting: "Morning" or "Afternoon".
        custom_instructions: Optional additional instructions for the prompt.
        diff_data: Optional week-over-week diff data.
        progress_callback: Called with company_name after each completion.

    Returns:
        Dict mapping company_name to generated email text.
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    results: dict[str, str] = {}
    errors: dict[str, str] = {}

    async def gen_one(client: Client) -> tuple[str, str | None, str | None]:
        async with semaphore:
            try:
                result = await asyncio.to_thread(
                    generate_summary, client, greeting, custom_instructions, diff_data
                )
                if progress_callback:
                    progress_callback(client.company_name)
                return client.company_name, result, None
            except Exception as e:
                logger.error(f"Error generating for {client.company_name}: {e}")
                if progress_callback:
                    progress_callback(client.company_name)
                return client.company_name, None, str(e)

    tasks = [gen_one(c) for c in clients]

    for coro in asyncio.as_completed(tasks):
        name, text, error = await coro
        if text:
            results[name] = text
        if error:
            errors[name] = error

    if errors:
        logger.warning(f"Errors for {len(errors)} clients: {list(errors.keys())}")

    return results
