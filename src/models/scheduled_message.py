from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from .user import db

class ScheduledMessage(db.Model):
    __tablename__ = 'scheduled_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    message_type = db.Column(db.String(20), default='text')  # 'text', 'image', 'mixed'
    schedule_time = db.Column(db.String(10), nullable=False)  # Formato HH:MM
    schedule_days = db.Column(db.String(20), nullable=False)  # 'daily', 'weekdays', 'weekends', ou dias específicos
    recipients = db.Column(db.Text, nullable=False)  # JSON string com lista de destinatários
    target_computers = db.Column(db.Text, nullable=True)  # JSON string com lista de computadores específicos
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_sent = db.Column(db.DateTime, nullable=True)
    next_send = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_url': self.image_url,
            'message_type': self.message_type,
            'schedule_time': self.schedule_time,
            'schedule_days': self.schedule_days,
            'recipients': json.loads(self.recipients) if self.recipients else [],
            'target_computers': json.loads(self.target_computers) if self.target_computers else [],
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat(),
            'last_sent': self.last_sent.isoformat() if self.last_sent else None,
            'next_send': self.next_send.isoformat() if self.next_send else None
        }