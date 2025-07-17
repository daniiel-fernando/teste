from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Computer(db.Model):
    __tablename__ = 'computers'
    
    id = db.Column(db.Integer, primary_key=True)
    computer_name = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)  # Suporta IPv4 e IPv6
    mac_address = db.Column(db.String(17), nullable=True)
    department = db.Column(db.String(50), nullable=False)
    user_name = db.Column(db.String(100), nullable=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'computer_name': self.computer_name,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'department': self.department,
            'user_name': self.user_name,
            'is_online': self.is_online,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @staticmethod
    def register_computer(computer_name, ip_address=None, mac_address=None, department='TI', user_name=None):
        """Registra ou atualiza informações de um computador"""
        computer = Computer.query.filter_by(computer_name=computer_name).first()
        
        if computer:
            # Atualiza computador existente
            computer.ip_address = ip_address or computer.ip_address
            computer.mac_address = mac_address or computer.mac_address
            computer.department = department or computer.department
            computer.user_name = user_name or computer.user_name
            computer.is_online = True
            computer.last_seen = datetime.utcnow()
            computer.updated_at = datetime.utcnow()
        else:
            # Cria novo computador
            computer = Computer(
                computer_name=computer_name,
                ip_address=ip_address,
                mac_address=mac_address,
                department=department,
                user_name=user_name,
                is_online=True,
                last_seen=datetime.utcnow()
            )
            db.session.add(computer)
        
        db.session.commit()
        return computer
    
    @staticmethod
    def get_computers_by_department(department):
        """Retorna computadores de um departamento específico"""
        return Computer.query.filter_by(department=department).all()
    
    @staticmethod
    def get_online_computers():
        """Retorna apenas computadores online"""
        return Computer.query.filter_by(is_online=True).all()
    
    def mark_offline(self):
        """Marca computador como offline"""
        self.is_online = False
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<Computer {self.computer_name}>'

