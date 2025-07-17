from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .user import db
import json


class Message(db.Model):
    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String(100), nullable=False)
    sender_name = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    message_type = db.Column(db.String(20), default="text")  # 'text', 'image', 'mixed'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    recipients = db.Column(
        db.Text, nullable=False
    )  # JSON string com lista de destinatários
    target_computers = db.Column(
        db.Text, nullable=True
    )  # JSON string com lista de computadores específicos
    status = db.Column(db.String(20), default="sent")  # 'sent', 'delivered', 'read'

    # 🔽 Novo campo: quem já recebeu a mensagem
    delivered_to = db.Column(db.Text, nullable=True)  # JSON string com IPs ou IDs

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender_name,
            "content": self.content,
            "image_url": self.image_url,
            "message_type": self.message_type,
            "timestamp": self.timestamp.isoformat(),
            "recipients": json.loads(self.recipients) if self.recipients else [],
            "target_computers": (
                json.loads(self.target_computers) if self.target_computers else []
            ),
            "status": self.status,
            "delivered_to": json.loads(self.delivered_to) if self.delivered_to else [],
        }
