from __future__ import annotations

import logging

from news_scraper_backend.scraper.selector_inference import OllamaSelectorClient, OllamaSelectorError

logger = logging.getLogger("news_scraper.content_quality")

CONTENT_QUALITY_SCHEMA = {
    "type": "object",
    "properties": {
        "keep_indexes": {"type": "array", "items": {"type": "integer"}},
        "remove_indexes": {"type": "array", "items": {"type": "integer"}},
    },
    "required": ["keep_indexes", "remove_indexes"],
}


class ContentQualityService:
    def __init__(
        self,
        *,
        ollama: OllamaSelectorClient,
        max_blocks: int = 80,
        min_block_chars: int = 40,
    ) -> None:
        self.ollama = ollama
        self.max_blocks = max_blocks
        self.min_block_chars = min_block_chars

    async def filter_blocks(
        self,
        *,
        url: str,
        title: str,
        description: str,
        blocks: list[str],
    ) -> list[str]:
        candidates = [
            (index, text)
            for index, text in enumerate(blocks)
            if len(text) >= self.min_block_chars
        ][: self.max_blocks]
        if not candidates:
            return blocks

        try:
            result = await self.ollama.generate_json(
                prompt=_quality_prompt(
                    url=url,
                    title=title,
                    description=description,
                    candidates=candidates,
                ),
                schema=CONTENT_QUALITY_SCHEMA,
            )
        except OllamaSelectorError as exc:
            logger.warning("content_quality_ollama_failed", extra={"url": url, "error": str(exc)})
            return blocks
        except Exception:
            logger.exception("content_quality_failed", extra={"url": url})
            return blocks

        remove_indexes = _explicit_remove_indexes(result, {index for index, _ in candidates})
        if not remove_indexes:
            return blocks

        filtered = [text for index, text in enumerate(blocks) if index not in remove_indexes]
        if not filtered:
            logger.warning("content_quality_rejected_all_blocks", extra={"url": url})
            return blocks
        return filtered


def _quality_prompt(
    *,
    url: str,
    title: str,
    description: str,
    candidates: list[tuple[int, str]],
) -> str:
    block_lines = "\n".join(f"{index}: {text}" for index, text in candidates)
    return (
        "You are checking extracted news article text. Return JSON only.\n"
        "Decide which numbered text blocks are unrelated to the article title and short description.\n"
        "Remove embedded related-story headlines, promos, ads, navigation, social widgets, and unrelated teasers.\n"
        "Keep normal article paragraphs, even when they add details not present in the title.\n"
        "Only put a block index in remove_indexes when it is clearly not part of the article body.\n\n"
        f"URL: {url}\n"
        f"Title: {title}\n"
        f"Description: {description}\n\n"
        f"Blocks:\n{block_lines}\n\n"
        "Return exactly this shape: {\"keep_indexes\":[...],\"remove_indexes\":[...]}"
    )


def _explicit_remove_indexes(result: dict, allowed_indexes: set[int]) -> set[int]:
    raw_remove_indexes = result.get("remove_indexes")
    if not isinstance(raw_remove_indexes, list):
        return set()
    remove_indexes: set[int] = set()
    for value in raw_remove_indexes:
        if isinstance(value, int) and value in allowed_indexes:
            remove_indexes.add(value)
    return remove_indexes
