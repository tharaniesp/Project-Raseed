import logging
from typing import List
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from message_transaction import MessageTransaction

logger = logging.getLogger(__name__)

class MessageTransactionService:
    """Service for handling message-based transactions (e.g., from Gmail)"""

    @staticmethod
    def fetch_gmail_messages(user_id: str, credentials) -> List[dict]:
        """Fetch relevant Gmail messages for the user using Gmail API and OAuth2 credentials."""
        # Placeholder for Gmail API integration
        # In a real implementation, use google-auth, google-api-python-client, etc.
        # Example steps:
        # 1. Build Gmail API service with credentials
        # 2. Search for messages with transaction keywords (e.g., 'debited', 'purchase', 'spent')
        # 3. Fetch message content (snippet or full body)
        # 4. Return as list of dicts
        logger.info(f"Fetching Gmail messages for user: {user_id}")
        # TODO: Implement actual Gmail API logic
        return [
            {"id": "msg1", "snippet": "Your account was debited $50 at Amazon on 2024-07-01."},
            {"id": "msg2", "snippet": "You spent INR 1200 at Big Bazaar on 2024-07-02."}
        ]

    @staticmethod
    def extract_transactions_from_messages(messages: List[dict], user_id: str) -> List[MessageTransaction]:
        """Extract transaction data from Gmail messages using regex/NLP."""
        import re
        transactions = []
        for msg in messages:
            snippet = msg.get("snippet", "")
            # Simple regex for amount and merchant extraction (expand for real use)
            amount_match = re.search(r"(\$|INR)\s?(\d+[.,]?\d*)", snippet)
            merchant_match = re.search(r"at ([A-Za-z0-9 &]+)", snippet)
            date_match = re.search(r"on (\d{4}-\d{2}-\d{2})", snippet)
            if amount_match and merchant_match and date_match:
                currency = amount_match.group(1)
                amount = float(amount_match.group(2).replace(",", ""))
                merchant = merchant_match.group(1)
                date = date_match.group(1)
                transaction = MessageTransaction(
                    user_id=user_id,
                    merchant_name=merchant,
                    amount=amount,
                    currency=currency,
                    transaction_date=date,
                    message_content=snippet,
                    message_id=msg.get("id"),
                    raw_data=msg
                )
                transactions.append(transaction)
        return transactions

    @staticmethod
    def store_transactions(transactions: List[MessageTransaction]):
        """Store extracted transactions in the database (e.g., Firestore)."""
        # TODO: Implement Firestore or DB storage logic
        logger.info(f"Storing {len(transactions)} transactions.")
        pass 