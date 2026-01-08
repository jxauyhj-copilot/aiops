"""
Session Manager for ChatOps

Manages multiple chat sessions with JSON-based persistence.
Each session is stored as a separate JSON file in the sessions directory.
"""

import json
import os
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path
import uuid


class SessionManager:
    """Manages chat session lifecycle and persistence"""

    def __init__(self, storage_path: str):
        """
        Initialize SessionManager

        Args:
            storage_path: Directory path to store session files
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_session(self, title: str = "New Chat", first_message: str = "") -> str:
        """
        Create a new chat session

        Args:
            title: Session title
            first_message: Optional first message for title generation

        Returns:
            Session ID
        """
        session_id = self._generate_session_id()

        # Auto-generate title if this is a new chat with a first message
        if title == "New Chat" and first_message:
            title = self.generate_title(first_message)

        session_data = {
            "id": session_id,
            "title": title,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "messages": []
        }

        self._save_session(session_id, session_data)
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Load a session from disk

        Args:
            session_id: Session identifier

        Returns:
            Session data dictionary or None if not found
        """
        session_file = self._get_session_path(session_id)

        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, KeyError) as e:
            # Corrupt file - delete it
            print(f"Corrupted session file {session_file}, removing...")
            try:
                session_file.unlink()
            except:
                pass
            return None

    def update_session(self, session_id: str, messages: List[Dict], title: str = None) -> bool:
        """
        Update an existing session

        Args:
            session_id: Session identifier
            messages: List of message dictionaries
            title: Optional new title

        Returns:
            True if successful, False otherwise
        """
        session_data = self.get_session(session_id)

        if not session_data:
            return False

        # Update fields
        session_data["messages"] = messages
        session_data["last_updated"] = datetime.now().isoformat()

        if title is not None:
            session_data["title"] = title

        return self._save_session(session_id, session_data)

    def list_sessions(self) -> List[Dict]:
        """
        List all sessions with metadata

        Returns:
            List of session metadata (id, title, created_at, last_updated, message_count)
        """
        sessions = []

        for session_file in self.storage_path.glob("sess_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)

                # Return only metadata for lighter loading
                metadata = {
                    "id": session_data["id"],
                    "title": session_data["title"],
                    "created_at": session_data["created_at"],
                    "last_updated": session_data["last_updated"],
                    "message_count": len(session_data.get("messages", []))
                }
                sessions.append(metadata)

            except (json.JSONDecodeError, IOError, KeyError) as e:
                # Corrupt file - delete it to prevent future errors
                print(f"Corrupted session file {session_file}, removing...")
                try:
                    session_file.unlink()
                except:
                    pass
                continue

        # Sort by last_updated (most recent first)
        sessions.sort(key=lambda x: x["last_updated"], reverse=True)
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session

        Args:
            session_id: Session identifier

        Returns:
            True if successful, False otherwise
        """
        session_file = self._get_session_path(session_id)

        if not session_file.exists():
            return False

        try:
            session_file.unlink()
            return True
        except IOError as e:
            print(f"Error deleting session {session_id}: {e}")
            return False

    def generate_title(self, first_message: str) -> str:
        """
        Generate a concise title from the first user message

        Args:
            first_message: First message content

        Returns:
            Generated title
        """
        # Extract first 5-7 words for the title
        words = first_message.split()

        if len(words) <= 7:
            title = " ".join(words)
        else:
            title = " ".join(words[:7]) + "..."

        # Clean up and limit length
        title = title.strip().capitalize()
        title = title[:50]  # Max 50 characters

        return title if title else "New Chat"

    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"sess_{timestamp}_{unique_suffix}"

    def _get_session_path(self, session_id: str) -> Path:
        """Get the file path for a session"""
        return self.storage_path / f"{session_id}.json"

    def _save_session(self, session_id: str, session_data: Dict) -> bool:
        """
        Save session data to disk

        Args:
            session_id: Session identifier
            session_data: Session data dictionary

        Returns:
            True if successful, False otherwise
        """
        session_file = self._get_session_path(session_id)

        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            return True
        except (IOError, TypeError) as e:
            print(f"Error saving session {session_id}: {e}")
            return False
