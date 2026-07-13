import os
import sys
import tempfile
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

os.environ["CHATBOT_DB_PATH"] = os.path.join(
    tempfile.gettempdir(),
    "khub_chatbot_test.db",
)

from database import (
    add_message,
    create_conversation,
    delete_conversation,
    get_conversation_messages,
    init_db,
)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "chatbot.db")
        if os.path.exists(db_path):
            os.remove(db_path)
        init_db()

    def test_create_and_fetch_conversation(self):
        conversation_id = create_conversation("Test chat")
        add_message(conversation_id, "user", "Hello")
        add_message(conversation_id, "assistant", "Hi there")

        messages = get_conversation_messages(conversation_id)

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[1]["role"], "assistant")

    def test_delete_conversation(self):
        conversation_id = create_conversation("Delete me")
        self.assertTrue(delete_conversation(conversation_id))
        self.assertEqual(get_conversation_messages(conversation_id), [])


if __name__ == "__main__":
    unittest.main()
