"""
Fahamika Voice Pipeline — LLM Simplification
Supports both DeepSeek API (cloud) and Ollama (local).
"""

import logging
from openai import OpenAI
from shared.config import config

logger = logging.getLogger(__name__)

# The system prompt enforces the core design principle:
#   The AI NEVER generates civic facts. It only simplifies/translates
#   pre-approved content retrieved from Pinecone.

SYSTEM_PROMPT = """You are Fahamika, an AI assistant for citizens in Kenya, including persons 
with disabilities. Your job is to SIMPLIFY and TRANSLATE pre-approved civic information.

CRITICAL RULES:
1. ONLY use the content provided in the user's message. NEVER invent facts, policies, 
   dates, phone numbers, or procedures.
2. Simplify complex legal/official language into clear, everyday Swahili or English.
3. If the content includes both languages, respond in the language the caller used.
4. Keep responses under 3 spoken sentences (roughly 30 seconds when read aloud).
5. If the provided content does not answer the question, say:
   "Samahani, sijapata taarifa hiyo kwa sasa. Tafadhali jaribu swali lingine."
   (I'm sorry, I don't have that information right now. Please try another question.)
6. NEVER mention that you are an AI, a model, or that content "was retrieved." 
   Speak naturally as a helpful civic information service.
7. Always be respectful, warm, and encouraging."""


def _get_deepseek_client() -> OpenAI:
    """Return an OpenAI-compatible client pointed at DeepSeek."""
    return OpenAI(
        api_key=config.DEEPSEEK_API_KEY,
        base_url=config.DEEPSEEK_BASE_URL,
    )


def _get_ollama_client() -> OpenAI:
    """Return an OpenAI-compatible client pointed at local Ollama."""
    return OpenAI(
        api_key="ollama",  # Ollama doesn't check the key
        base_url=f"{config.OLLAMA_BASE_URL}/v1",
    )


def simplify(
    question: str,
    retrieved_content: str,
    provider: str | None = None,
) -> str:
    """
    Simplify and translate retrieved civic content into a spoken response.

    Args:
        question: The caller's transcribed question.
        retrieved_content: Pre-approved content matched from Pinecone.
        provider: "deepseek" or "ollama" (defaults to config.LLM_PROVIDER).

    Returns:
        A simplified, spoken-word-friendly response.
    """
    provider = provider or config.LLM_PROVIDER

    if provider == "ollama":
        client = _get_ollama_client()
        model = config.OLLAMA_MODEL
    else:
        client = _get_deepseek_client()
        model = config.DEEPSEEK_MODEL

    user_message = f"""CALLER QUESTION: {question}

RETRIEVED CONTENT (use ONLY this to answer):
{retrieved_content}

Now simplify this into a spoken response following all the rules."""

    logger.info(f"Calling {provider} ({model}) for simplification ...")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,  # Low temperature for factual consistency
        max_tokens=300,   # Short spoken responses
    )

    answer = response.choices[0].message.content.strip()
    logger.info(f"LLM response ({len(answer)} chars): {answer[:100]}...")
    return answer
