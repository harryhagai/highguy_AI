PROJECT: Highguy AI Assistant - SQLite Memory System

Goal:
Implement a local AI assistant memory system using SQLite in my existing Python project.

Project path:
C:\Users\hngob\highguy_ai

Python version:
Python 3.11

Main objective:
Create a memory/reference system where the AI assistant can:
1. Save new knowledge/facts.
2. Store user preferences.
3. Store project references.
4. Search saved memories.
5. Retrieve relevant memory before answering a user.
6. Keep everything local using SQLite.

Required database:
Use SQLite database file:
highguy_ai.db

Required folder structure:

highguy_ai/
│
├── src/
│   ├── main.py
│   ├── memory_manager.py
│   ├── ai_engine.py
│   ├── voice_handler.py
│   └── config.py
│
├── highguy_ai.db
└── requirements.txt

Create/Update these files:

1. src/memory_manager.py

Implement a MemoryManager class with these methods:

- __init__(db_path="highguy_ai.db")
- create_tables()
- add_memory(title, content, tags="")
- search_memory(keyword, limit=5)
- get_all_memories()
- delete_memory(memory_id)
- update_memory(memory_id, title=None, content=None, tags=None)

SQLite table:

memory:
- id INTEGER PRIMARY KEY AUTOINCREMENT
- title TEXT NOT NULL
- content TEXT NOT NULL
- tags TEXT
- created_at TEXT NOT NULL
- updated_at TEXT

2. src/ai_engine.py

Create an AIEngine class.

For now, do not connect external AI API yet.
Create simple methods:

- build_context(user_question)
  This should search memory using keywords from user_question.
  It should return relevant memory text.

- generate_response(user_question)
  This should combine:
  - retrieved memory context
  - user question
  - simple placeholder response

Example response format:
Based on what I remember:
[retrieved memory]

Your question:
[user question]

Suggested answer:
[placeholder answer]

3. src/main.py

Create a terminal menu system:

When the app starts, show:

HIGHGUY AI ASSISTANT
1. Add new memory
2. Search memory
3. Show all memories
4. Ask assistant
5. Delete memory
6. Exit

Each option should work.

4. requirements.txt

Add only necessary packages for now:

SpeechRecognition
PyAudio

Do not add heavy AI libraries yet.

5. Error handling

Add proper try/except blocks for:
- database connection errors
- empty user inputs
- invalid menu choices
- memory not found

6. Coding style

Use clean beginner-friendly Python.
Add comments explaining important parts.
Make the code easy to understand.
Do not overcomplicate it.
Use only sqlite3 built-in module for database.

7. Expected behavior

Example:

User selects:
1. Add new memory

Input:
Title: Python audio setup
Content: Use Python 3.11 for SpeechRecognition and PyAudio.
Tags: python,audio,speech

System:
Memory saved successfully.

Then user selects:
4. Ask assistant

Question:
Which Python version should I use for audio?

Assistant should retrieve the saved memory and include it in the answer.

8. Important

Make sure imports work correctly inside src folder.
Make sure running this command works:

python src/main.py

9. Bonus if possible

Add automatic database creation if highguy_ai.db does not exist.
Add created_at and updated_at timestamps automatically.
Make search work with title, content, and tags.