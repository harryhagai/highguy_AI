#!/usr/bin/env python3
"""Terminal menu for the Highguy AI Assistant memory system."""

import sys

from ai_engine import AIEngine
from memory_manager import MemoryManager


def print_menu():
    print("\nHIGHGUY AI ASSISTANT")
    print("1. Add new memory")
    print("2. Search memory")
    print("3. Show all memories")
    print("4. Ask assistant")
    print("5. Delete memory")
    print("6. Exit")


def print_memory(memory):
    print(f"\nID: {memory['id']}")
    print(f"Title: {memory['title']}")
    print(f"Content: {memory['content']}")
    print(f"Tags: {memory['tags'] or 'None'}")
    print(f"Created: {memory['created_at']}")
    print(f"Updated: {memory['updated_at'] or 'Not updated'}")


def add_new_memory(memory_manager):
    title = input("Title: ").strip()
    content = input("Content: ").strip()
    tags = input("Tags: ").strip()

    if not title or not content:
        print("Title and content cannot be empty.")
        return

    try:
        memory_manager.add_memory(title, content, tags)
        print("Memory saved successfully.")
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}")


def search_memory(memory_manager):
    keyword = input("Search keyword: ").strip()

    if not keyword:
        print("Search keyword cannot be empty.")
        return

    try:
        memories = memory_manager.search_memory(keyword)
    except RuntimeError as error:
        print(f"Error: {error}")
        return

    if not memories:
        print("No memories found.")
        return

    for memory in memories:
        print_memory(memory)


def show_all_memories(memory_manager):
    try:
        memories = memory_manager.get_all_memories()
    except RuntimeError as error:
        print(f"Error: {error}")
        return

    if not memories:
        print("No memories saved yet.")
        return

    for memory in memories:
        print_memory(memory)


def ask_assistant(ai_engine):
    question = input("Question: ").strip()

    if not question:
        print("Question cannot be empty.")
        return

    try:
        response = ai_engine.generate_response(question)
        print("\nAssistant response:")
        print(response)
    except (RuntimeError, ValueError) as error:
        print(f"Error: {error}")


def delete_memory(memory_manager):
    memory_id_text = input("Memory ID to delete: ").strip()

    if not memory_id_text:
        print("Memory ID cannot be empty.")
        return

    try:
        memory_id = int(memory_id_text)
    except ValueError:
        print("Memory ID must be a number.")
        return

    try:
        deleted = memory_manager.delete_memory(memory_id)
    except RuntimeError as error:
        print(f"Error: {error}")
        return

    if deleted:
        print("Memory deleted successfully.")
    else:
        print("Memory not found.")


def main():
    try:
        memory_manager = MemoryManager()
        ai_engine = AIEngine(memory_manager)
    except RuntimeError as error:
        print(f"Failed to start assistant: {error}")
        sys.exit(1)

    while True:
        print_menu()
        choice = input("Choose an option: ").strip()

        if choice == "1":
            add_new_memory(memory_manager)
        elif choice == "2":
            search_memory(memory_manager)
        elif choice == "3":
            show_all_memories(memory_manager)
        elif choice == "4":
            ask_assistant(ai_engine)
        elif choice == "5":
            delete_memory(memory_manager)
        elif choice == "6":
            print("Goodbye.")
            break
        else:
            print("Invalid menu choice. Please enter a number from 1 to 6.")


if __name__ == "__main__":
    main()
