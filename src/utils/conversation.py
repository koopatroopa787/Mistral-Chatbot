"""Conversation Management"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import uuid


@dataclass
class ConversationMessage:
    """A message in a conversation"""
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Conversation:
    """A conversation with metadata"""
    id: str
    title: str
    messages: List[ConversationMessage]
    created_at: str
    updated_at: str
    provider: str
    model: str
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "messages": [msg.to_dict() for msg in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "provider": self.provider,
            "model": self.model,
            "metadata": self.metadata or {}
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create from dictionary"""
        messages = [
            ConversationMessage(**msg) for msg in data.get("messages", [])
        ]
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            messages=messages,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            provider=data.get("provider"),
            model=data.get("model"),
            metadata=data.get("metadata")
        )


class ConversationManager:
    """Manager for saving/loading conversations"""

    def __init__(self, storage_path: Path = None):
        """
        Initialize conversation manager

        Args:
            storage_path: Directory for storing conversations
        """
        self.storage_path = storage_path or Path("conversations")
        self.storage_path.mkdir(exist_ok=True)

    def create_conversation(
        self,
        title: str,
        provider: str,
        model: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """
        Create a new conversation

        Args:
            title: Conversation title
            provider: AI provider name
            model: Model name
            metadata: Optional metadata

        Returns:
            New Conversation object
        """
        now = datetime.now().isoformat()
        return Conversation(
            id=str(uuid.uuid4()),
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
            provider=provider,
            model=model,
            metadata=metadata
        )

    def save_conversation(self, conversation: Conversation):
        """
        Save a conversation to disk

        Args:
            conversation: Conversation to save
        """
        conversation.updated_at = datetime.now().isoformat()
        file_path = self.storage_path / f"{conversation.id}.json"

        with open(file_path, 'w') as f:
            json.dump(conversation.to_dict(), f, indent=2)

    def load_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """
        Load a conversation from disk

        Args:
            conversation_id: ID of conversation to load

        Returns:
            Conversation object or None if not found
        """
        file_path = self.storage_path / f"{conversation_id}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            return Conversation.from_dict(data)
        except Exception as e:
            print(f"Error loading conversation {conversation_id}: {e}")
            return None

    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all saved conversations

        Returns:
            List of conversation metadata (id, title, created_at, updated_at)
        """
        conversations = []

        for file_path in self.storage_path.glob("*.json"):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                conversations.append({
                    "id": data["id"],
                    "title": data["title"],
                    "created_at": data["created_at"],
                    "updated_at": data["updated_at"],
                    "provider": data.get("provider"),
                    "model": data.get("model"),
                    "message_count": len(data.get("messages", []))
                })
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

        # Sort by updated_at descending
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation

        Args:
            conversation_id: ID of conversation to delete

        Returns:
            True if deleted, False if not found
        """
        file_path = self.storage_path / f"{conversation_id}.json"

        if file_path.exists():
            file_path.unlink()
            return True

        return False

    def export_conversation(self, conversation_id: str, export_path: Path) -> bool:
        """
        Export a conversation to a file

        Args:
            conversation_id: ID of conversation to export
            export_path: Path to export file

        Returns:
            True if successful, False otherwise
        """
        conversation = self.load_conversation(conversation_id)
        if not conversation:
            return False

        try:
            with open(export_path, 'w') as f:
                json.dump(conversation.to_dict(), f, indent=2)
            return True
        except Exception as e:
            print(f"Error exporting conversation: {e}")
            return False

    def import_conversation(self, import_path: Path) -> Optional[str]:
        """
        Import a conversation from a file

        Args:
            import_path: Path to import file

        Returns:
            ID of imported conversation or None if failed
        """
        try:
            with open(import_path, 'r') as f:
                data = json.load(f)

            conversation = Conversation.from_dict(data)
            # Generate new ID to avoid conflicts
            conversation.id = str(uuid.uuid4())
            conversation.updated_at = datetime.now().isoformat()

            self.save_conversation(conversation)
            return conversation.id
        except Exception as e:
            print(f"Error importing conversation: {e}")
            return None
