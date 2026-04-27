"""Simple local AI response builder using saved memories."""

import re

try:
    from .memory_manager import MemoryManager
except ImportError:
    from memory_manager import MemoryManager


class AIEngine:
    """Build placeholder assistant answers from local memory."""

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager or MemoryManager()

    def _extract_keywords(self, user_question):
        """Pick useful search words from the user's question."""
        words = re.findall(r"[A-Za-z0-9_]+", user_question.lower())
        common_words = {
            "a",
            "an",
            "and",
            "are",
            "for",
            "i",
            "in",
            "is",
            "it",
            "of",
            "on",
            "should",
            "the",
            "to",
            "use",
            "what",
            "which",
            "with",
            "you",
        }
        return [word for word in words if len(word) > 2 and word not in common_words]

    def build_context(self, user_question):
        """Search memory using words from the question and return relevant text."""
        if not user_question.strip():
            return ""

        keywords = self._extract_keywords(user_question)
        memories_by_id = {}

        for keyword in keywords:
            for memory in self.memory_manager.search_memory(keyword, limit=3):
                memories_by_id[memory["id"]] = memory

        if not memories_by_id:
            return "No relevant memories found."

        memory_lines = []
        for memory in memories_by_id.values():
            tags = f" Tags: {memory['tags']}" if memory.get("tags") else ""
            memory_lines.append(
                f"- {memory['title']}: {memory['content']}{tags}"
            )

        return "\n".join(memory_lines)

    def generate_response(self, user_question):
        """Combine memory context, the question, and a placeholder answer."""
        if not user_question.strip():
            raise ValueError("Question cannot be empty.")

        memory_context = self.build_context(user_question)

        return f"""Based on what I remember:
{memory_context}

Your question:
{user_question}

Suggested answer:
This is a placeholder answer. A future version can connect this context to an external AI API."""
