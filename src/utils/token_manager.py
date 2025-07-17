"""
Gerenciador de Tokens Avançado
Sistema de Notificações Jotanunes - Versão 2.2.0
✅ Implementa melhorias adicionais do checklist
"""

import jwt
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging
import secrets
import hashlib

logger = logging.getLogger(__name__)

class TokenManager:
    """
    ✅ Gerenciador avançado de tokens JWT com refresh tokens
    Implementação das melhorias adicionais do checklist
    """
    
    def __init__(self, secret_key: str, db_path: str = 'notifications.db', access_token_expiry_hours: int = 2, refresh_token_expiry_days: int = 7):
        self.secret_key = secret_key
        self.db_path = db_path
        self.access_token_expiry = timedelta(hours=access_token_expiry_hours)
        self.refresh_token_expiry = timedelta(days=refresh_token_expiry_days)
        self.init_refresh_tokens_table()
    
    def init_refresh_tokens_table(self):
        """Inicializa tabela de refresh tokens"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS refresh_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP,
                    is_revoked BOOLEAN DEFAULT 0,
                    device_info TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            # Índices para performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_hash ON refresh_tokens(token_hash)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at)')
            
            conn.commit()
            conn.close()
            
            logger.info("Tabela de refresh tokens inicializada")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar tabela de refresh tokens: {e}")
    
    def generate_access_token(self, user_data: Dict[str, Any]) -> str:
        """
        ✅ Gera token de acesso JWT com validade limitada
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_data['id'],
            'username': user_data['username'],
            'department': user_data.get('department'),
            'iat': now,
            'exp': now + self.access_token_expiry,
            'type': 'access'
        }
        
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def generate_refresh_token(self, user_id: int, device_info: str = None) -> str:
        """
        ✅ Gera refresh token seguro e armazena no banco
        """
        try:
            # Gera token aleatório seguro
            refresh_token = secrets.token_urlsafe(64)
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            
            # Armazena no banco
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = datetime.utcnow() + self.refresh_token_expiry
            
            cursor.execute('''
                INSERT INTO refresh_tokens (user_id, token_hash, expires_at, device_info)
                VALUES (?, ?, ?, ?)
            ''', (user_id, token_hash, expires_at, device_info))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Refresh token gerado para usuário {user_id}")
            return refresh_token
            
        except Exception as e:
            logger.error(f"Erro ao gerar refresh token: {e}")
            raise
    
    def verify_access_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        ✅ Verifica e decodifica token de acesso
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            
            # Verifica se é token de acesso
            if payload.get('type') != 'access':
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token de acesso expirado")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Token de acesso inválido: {e}")
            return None
    
    def verify_refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        ✅ Verifica refresh token e retorna dados do usuário
        """
        try:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Busca refresh token válido
            cursor.execute('''
                SELECT rt.user_id, rt.expires_at, rt.is_revoked,
                       u.username, u.name, u.email, u.department
                FROM refresh_tokens rt
                JOIN users u ON rt.user_id = u.id
                WHERE rt.token_hash = ? AND rt.is_revoked = 0
            ''', (token_hash,))
            
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return None
            
            user_id, expires_at, is_revoked, username, name, email, department = result
            
            # Verifica expiração
            if datetime.fromisoformat(expires_at.replace('Z', '+00:00')) < datetime.utcnow():
                # Token expirado, remove do banco
                cursor.execute('DELETE FROM refresh_tokens WHERE token_hash = ?', (token_hash,))
                conn.commit()
                conn.close()
                return None
            
            # Atualiza último uso
            cursor.execute('''
                UPDATE refresh_tokens 
                SET last_used = CURRENT_TIMESTAMP 
                WHERE token_hash = ?
            ''', (token_hash,))
            
            conn.commit()
            conn.close()
            
            return {
                'id': user_id,
                'username': username,
                'name': name,
                'email': email,
                'department': department
            }
            
        except Exception as e:
            logger.error(f"Erro ao verificar refresh token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        ✅ Gera novo token de acesso usando refresh token
        """
        user_data = self.verify_refresh_token(refresh_token)
        
        if not user_data:
            return None
        
        # Gera novo token de acesso
        new_access_token = self.generate_access_token(user_data)
        
        return {
            'access_token': new_access_token,
            'token_type': 'Bearer',
            'expires_in': int(self.access_token_expiry.total_seconds())
        }
    
    def revoke_refresh_token(self, refresh_token: str) -> bool:
        """
        ✅ Revoga refresh token (logout)
        """
        try:
            token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE refresh_tokens 
                SET is_revoked = 1 
                WHERE token_hash = ?
            ''', (token_hash,))
            
            revoked = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            if revoked:
                logger.info("Refresh token revogado")
            
            return revoked
            
        except Exception as e:
            logger.error(f"Erro ao revogar refresh token: {e}")
            return False
    
    def revoke_all_user_tokens(self, user_id: int) -> int:
        """
        ✅ Revoga todos os refresh tokens de um usuário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE refresh_tokens 
                SET is_revoked = 1 
                WHERE user_id = ? AND is_revoked = 0
            ''', (user_id,))
            
            revoked_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            logger.info(f"Revogados {revoked_count} tokens do usuário {user_id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Erro ao revogar tokens do usuário: {e}")
            return 0
    
    def cleanup_expired_tokens(self) -> int:
        """
        ✅ Remove tokens expirados do banco
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM refresh_tokens 
                WHERE expires_at < datetime('now') OR is_revoked = 1
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            if deleted_count > 0:
                logger.info(f"Removidos {deleted_count} tokens expirados/revogados")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Erro na limpeza de tokens: {e}")
            return 0
    
    def get_user_active_tokens(self, user_id: int) -> list:
        """
        ✅ Lista tokens ativos de um usuário
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT device_info, created_at, last_used, expires_at
                FROM refresh_tokens 
                WHERE user_id = ? AND is_revoked = 0 AND expires_at > datetime('now')
                ORDER BY last_used DESC
            ''', (user_id,))
            
            tokens = []
            for row in cursor.fetchall():
                tokens.append({
                    'device_info': row[0],
                    'created_at': row[1],
                    'last_used': row[2],
                    'expires_at': row[3]
                })
            
            conn.close()
            return tokens
            
        except Exception as e:
            logger.error(f"Erro ao buscar tokens do usuário: {e}")
            return []
    
    def is_token_about_to_expire(self, token: str, threshold_minutes: int = 5) -> bool:
        """
        ✅ Verifica se token está prestes a expirar
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'], options={"verify_exp": False})
            exp_timestamp = payload.get('exp')
            
            if not exp_timestamp:
                return True
            
            exp_datetime = datetime.utcfromtimestamp(exp_timestamp)
            threshold = datetime.utcnow() + timedelta(minutes=threshold_minutes)
            
            return exp_datetime <= threshold
            
        except Exception:
            return True

