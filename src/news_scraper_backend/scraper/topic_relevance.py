from __future__ import annotations

import logging

from news_scraper_backend.scraper.selector_inference import OllamaSelectorClient

logger = logging.getLogger("news_scraper.topic_relevance")

TOPIC_RELEVANCE_SCHEMA = {
    "type": "object",
    "properties": {
        "is_relevant": {"type": "boolean"},
        "matched_topics": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
    "required": ["is_relevant", "matched_topics", "reason"],
}


class TopicRelevanceService:
    def __init__(self, *, ollama: OllamaSelectorClient) -> None:
        self.ollama = ollama

    async def is_relevant(
        self,
        *,
        url: str,
        title: str,
        description: str,
        target_topics: str | None,
    ) -> bool:
        topics = " ".join((target_topics or "").split())
        if not topics:
            return True

        try:
            result = await self.ollama.generate_json(
                prompt=_relevance_prompt(
                    url=url,
                    title=title,
                    description=description,
                    target_topics=topics,
                ),
                schema=TOPIC_RELEVANCE_SCHEMA,
            )
        except Exception as exc:
            logger.warning("topic_relevance_ollama_failed", extra={"url": url, "error": str(exc)})
            return False

        is_relevant = result.get("is_relevant")
        matched_topics = result.get("matched_topics")
        reason = result.get("reason")
        if (
            not isinstance(is_relevant, bool)
            or not isinstance(matched_topics, list)
            or not all(isinstance(topic, str) for topic in matched_topics)
            or not isinstance(reason, str)
        ):
            logger.warning("topic_relevance_invalid_response", extra={"url": url})
            return False
        return is_relevant


def _relevance_prompt(
    *,
    url: str,
    title: str,
    description: str,
    target_topics: str,
) -> str:
    return (
        "You are filtering news article candidates before crawling. Return JSON only.\n"
        "Decide whether the article title and short description are related to any of the target topics.\n"
        "A candidate is relevant if it clearly belongs to at least one target topic, including close synonyms.\n"
        "Do not mark an article relevant only because the topic word appears in unrelated navigation or branding.\n\n"
        f"Target topics: {target_topics}\n"
        f"URL: {url}\n"
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        "Return exactly this shape: "
        "{\"is_relevant\":true,\"matched_topics\":[\"...\"],\"reason\":\"...\"}"
    )
