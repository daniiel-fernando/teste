from flask import Blueprint, request, jsonify, session
from ldap3 import Server, Connection, ALL, SIMPLE
from datetime import datetime
import logging

from src.models.user import User, db
from config import Config  # Importa configurações

auth_bp = Blueprint("auth", __name__)

# Configura log
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)

# Configurações de AD vindas do config.py
AD_SERVER = Config.AD_SERVER_URL  # ex.: 192.168.79.201
AD_DOMAIN = Config.AD_DOMAIN  # ex.: jotanunes.net


@auth_bp.route("/api/login-ad", methods=["POST"])
def login_ad():
    """Autentica usuário via AD ou fallback admin/admin123"""
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Usuário e senha são obrigatórios"}), 400

    # 1️⃣  Fallback local (admin/admin123) ---------------------------------
    if username == "admin" and password == "admin123":
        user = User.query.filter_by(username="admin").first()
        if not user:
            user = User(
                username="admin",
                email="admin@jotanunes.net",
                full_name="Administrador Local",
                is_active=True,
                is_admin=True,
            )
            db.session.add(user)
            db.session.commit()

        _create_session(user)
        return _json_user(user, "Autenticado via fallback local")

    # 2️⃣  Autenticação no Active Directory -------------------------------
    try:
        server = Server(AD_SERVER, get_info=ALL, connect_timeout=5)
        # Usa UPN (usuario@dominio) com bind SIMPLE — evita erro MD4/NTLM
        conn = Connection(
            server,
            user=f"{username}@{AD_DOMAIN}",
            password=password,
            authentication=SIMPLE,
            auto_bind=True,
        )
    except Exception as e:
        logging.error(f"LDAP bind falhou: {e}")
        return jsonify({"error": "Falha na conexão com o Active Directory"}), 503

    if not conn.bound:
        return jsonify({"error": "Credenciais inválidas"}), 401

    # Consulta (ou cria) usuário local ------------------------------------
    try:
        # Garante que a tabela users existe
        db.engine.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                name TEXT,
                email TEXT,
                department TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """
        )
    except Exception as e:
        logging.error(f"Erro ao garantir tabela users: {e}")

    user = User.query.filter_by(username=username).first()
    if not user:
        user = User(
            username=username,
            email=f"{username}@{AD_DOMAIN}",
            full_name=username,
            is_active=True,
        )
        db.session.add(user)

    user.last_login = datetime.utcnow()
    db.session.commit()

    _create_session(user)
    return _json_user(user, "Autenticado com sucesso")


# -------------------------------------------------------------------------
# Helpers internos
# -------------------------------------------------------------------------


def _create_session(user: User):
    session.update(
        {
            "authenticated": True,
            "user_id": str(user.id),
            "username": user.username,
            "user_name": user.full_name or user.username,
            "is_admin": user.is_admin,
        }
    )


def _json_user(user: User, msg: str):
    return jsonify(
        {
            "success": True,
            "message": msg,
            "user": {
                "id": user.id,
                "username": user.username,
                "name": user.full_name or user.username,
                "is_admin": user.is_admin,
            },
        }
    )
