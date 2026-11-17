"""Simple local AI that answers questions using saved memories."""

import re

try:
    from .memory_manager import MemoryManager
except ImportError:
    from memory_manager import MemoryManager

# Small words that do not help when searching (English and Swahili).
COMMON_WORDS = {
    # English
    "a", "about", "an", "and", "are", "can", "could", "did", "do", "does",
    "for", "from", "how", "i", "in", "is", "it", "know", "me", "my", "of",
    "on", "or", "please", "remember", "should", "tell", "that", "the", "this",
    "to", "use", "was", "what", "when", "where", "which", "who", "why", "will",
    "with", "you", "your",
    # Swahili
    "ya", "wa", "za", "la", "kwa", "na", "ni", "je", "nini", "gani", "vipi",
    "kuhusu", "kwenye", "katika", "hii", "hiyo", "huu", "mimi", "wewe",
    "nataka", "naomba", "tafadhali", "unakumbuka", "unajua",
}


class AIEngine:
    """Find relevant memories and build answers from them."""

    def __init__(self, memory_manager=None):
        self.memory_manager = memory_manager or MemoryManager()

    def _extract_keywords(self, user_question):
        """Pick useful search words from the user's question."""
        words = re.findall(r"[\w.+#-]+", user_question.lower())
        keywords = []
        for word in words:
            word = word.strip(".-")
            if len(word) > 2 and word not in COMMON_WORDS and word not in keywords:
                keywords.append(word)
        return keywords

    def find_relevant_memories(self, user_question, limit=3):
        """Return the best matching memories, best first.

        Each memory gets a score: +1 for every keyword it contains, and +1
        extra when the keyword is in the title or tags.
        """
        scores = {}
        memories = {}

        for keyword in self._extract_keywords(user_question):
            for memory in self.memory_manager.search_memory(keyword, limit=10):
                memory_id = memory["id"]
                memories[memory_id] = memory
                score = 1
                title_and_tags = f"{memory['title']} {memory.get('tags') or ''}".lower()
                if keyword in title_and_tags:
                    score += 1
                scores[memory_id] = scores.get(memory_id, 0) + score

        ranked = sorted(scores, key=lambda memory_id: scores[memory_id], reverse=True)
        return [memories[memory_id] for memory_id in ranked[:limit]]

    def build_context(self, user_question):
        """Search memory using words from the question and return relevant text."""
        if not user_question.strip():
            return ""

        memories = self.find_relevant_memories(user_question)
        if not memories:
            return "No relevant memories found."

        lines = []
        for memory in memories:
            tags = f" (tags: {memory['tags']})" if memory.get("tags") else ""
            lines.append(f"- {memory['title']}: {memory['content']}{tags}")
        return "\n".join(lines)

    def answer(self, user_question, language="english"):
        """Return a short answer from memory, or None if nothing matches."""
        memories = self.find_relevant_memories(user_question)
        if not memories:
            return None

        best = memories[0]
        if language == "swahili":
            text = f"Ninakumbuka: {best['content']}"
            others = "Pia nina kumbukumbu hizi:"
        else:
            text = f"From my memory: {best['content']}"
            others = "Related memories:"

        if len(memories) > 1:
            text += f"\n\n{others}"
            for memory in memories[1:]:
                text += f"\n  • {memory['title']}: {memory['content']}"
        return text

    def generate_response(self, user_question):
        """Combine memory context, the question, and a suggested answer."""
        if not user_question.strip():
            raise ValueError("Question cannot be empty.")

        memory_context = self.build_context(user_question)
        memories = self.find_relevant_memories(user_question, limit=1)
        if memories:
            suggestion = memories[0]["content"]
        else:
            suggestion = (
                "I don't have anything saved about that yet. "
                "Teach me with: remember <something>"
            )

        return f"""Based on what I remember:
{memory_context}

Your question:
{user_question}

Suggested answer:
{suggestion}"""
