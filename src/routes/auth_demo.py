from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging
from src.models.user import User, db

auth_demo_bp = Blueprint("auth_demo", __name__)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)


@auth_demo_bp.route("/login-demo", methods=["POST"])
def login_demo():
    """Login de demonstração sem Active Directory"""
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

        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Usuário e senha são obrigatórios"}), 400

        # Para demonstração, aceita admin/123456
        if username == "admin" and password == "123456":
            # Busca usuário no banco local
            user = User.query.filter_by(username=username).first()

            if not user:
                return jsonify({"error": "Usuário não encontrado"}), 401

            # Atualiza último login
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Cria sessão
            session["authenticated"] = True
            session["user_id"] = str(user.id)
            session["username"] = username
            session["user_name"] = user.full_name or username
            session["is_admin"] = user.is_admin

            return jsonify(
                {
                    "success": True,
                    "message": "Autenticado com sucesso",
                    "user": {
                        "id": user.id,
                        "username": username,
                        "name": user.full_name or username,
                        "is_admin": user.is_admin,
                    },
                }
            )
        else:
            return jsonify({"error": "Credenciais inválidas"}), 401

    except Exception as e:
        logging.error(f"Erro no login demo: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
