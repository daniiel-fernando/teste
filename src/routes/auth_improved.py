import os
import logging
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import jwt
import sqlite3

# Importa gerenciador de tokens avançado
from src.utils.token_manager import TokenManager

# Configurações
from src.config import Config

# Importa a nova classe ActiveDirectoryAuth
from src.utils.ad_auth import ActiveDirectoryAuth, is_ad_available

auth_bp = Blueprint("auth_improved", __name__)

# Inicializa gerenciador de tokens
token_manager = TokenManager(
    secret_key=Config.SECRET_KEY,
    db_path=Config.DATABASE_PATH,
    access_token_expiry_hours=Config.JWT_ACCESS_TOKEN_EXPIRES_HOURS,
    refresh_token_expiry_days=Config.JWT_REFRESH_TOKEN_EXPIRES_DAYS,
)

# Configura log
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Instância global para autenticação AD
ad_auth_instance = ActiveDirectoryAuth(
    server_url=os.environ.get("AD_SERVER_URL"),
    domain=os.environ.get("AD_DOMAIN"),
    base_dn=os.environ.get("AD_BASE_DN"),
)

def get_db_connection():
    """Obtém conexão com o banco de dados"""
    db_path = Config.get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Garante que a tabela users existe
    try:
        conn.execute(
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
        conn.commit()
    except Exception as e:
        logger.error(f"Erro ao garantir tabela users: {e}")
    return conn


def authenticate_user(username: str, password: str) -> dict | None:
    """Autentica o usuário contra o Active Directory ou fallback local.
    """
    # Tenta autenticar via Active Directory (inclui fallback local para 'admin')
    user_info = ad_auth_instance.authenticate_and_authorize(username, password)
    return user_info


@auth_bp.route("/api/auth/login", methods=["POST"])
def login():
    """
    Endpoint de login melhorado com suporte a tokens JWT
    ✅ Implementa todas as correções do checklist
    """
    try:
        data = request.get_json()
        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return (
                jsonify(
                    {"success": False, "message": "Usuário e senha são obrigatórios"}
                ),
                400,
            )

        # Autentica usuário
        user_info = authenticate_user(username, password)

        if not user_info or not user_info.get("is_authorized"):
            logger.warning(f"Tentativa de login falhada para: {username}")
            return (
                jsonify({"success": False, "message": "Usuário ou senha inválidos"}),
                401,
            )

        # Busca ou cria usuário no banco local
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username = ?", (user_info["username"],)
        )
        db_user = cursor.fetchone()

        if db_user:
            # Atualiza dados do usuário existente
            cursor.execute(
                """
                UPDATE users 
                SET name = ?, email = ?, department = ?, last_login = ?
                WHERE username = ?
            """,
                (
                    user_info["display_name"],
                    user_info.get("email"),
                    user_info.get("department", "TI"),
                    datetime.now(),
                    user_info["username"],
                ),
            )
            user_id = db_user[0]
        else:
            # Cria novo usuário
            cursor.execute(
                """
                INSERT INTO users (username, name, email, department, last_login)
                VALUES (?, ?, ?, ?, ?)
            """,
                (
                    user_info["username"],
                    user_info["display_name"],
                    user_info.get("email"),
                    user_info.get("department"),
                    datetime.now(),
                ),
            )
            user_id = cursor.lastrowid

        conn.commit()
        conn.close()

        # Dados do usuário para resposta
        user_data = {
            "id": user_id,
            "username": user_info["username"],
            "name": user_info["display_name"],
            "email": user_info.get("email"),
            "department": user_info.get("department"),
        }

        # ✅ Gera tokens usando o gerenciador avançado
        access_token = token_manager.generate_access_token(user_data)
        refresh_token = token_manager.generate_refresh_token(
            user_id, request.headers.get("User-Agent", "Unknown Device")
        )

        # ✅ Salva na sessão do Flask (fallback)
        session["user_id"] = user_id
        session["username"] = user_info["username"]
        session["access_token"] = access_token

        logger.info(f"Login realizado com sucesso: {username}")

        return jsonify(
            {
                "success": True,
                "user": user_data,
                "access_token": access_token,  # ✅ Token de acesso
                "refresh_token": refresh_token,  # ✅ Token de renovação
                "token_type": "Bearer",
                "expires_in": int(token_manager.access_token_expiry.total_seconds()),
                "message": "Login realizado com sucesso",
            }
        )

    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return (
            jsonify(
                {"success": False, "message": f"Erro interno do servidor: {str(e)}"}
            ),
            500,
        )


@auth_bp.route("/api/auth/logout", methods=["POST"])
def logout():
    """
    Endpoint de logout melhorado
    ✅ Remove token e limpa sessão
    """
    username = session.get("username", "Desconhecido")

    # ✅ Revoga refresh token se fornecido
    try:
        data = request.get_json() or {}
        refresh_token = data.get("refresh_token")

        if refresh_token:
            token_manager.revoke_refresh_token(refresh_token)
    except Exception as e:
        logger.warning(f"Erro ao revogar refresh token: {e}")

    # ✅ Limpa sessão do Flask
    session.clear()

    logger.info(f"Logout realizado: {username}")

    return jsonify({"success": True, "message": "Logout realizado com sucesso"})


@auth_bp.route("/api/auth/verify", methods=["GET"])
def verify_auth():
    """
    ✅ Endpoint para verificar autenticação (implementação do checklist)
    Verifica token JWT ou sessão do Flask
    """
    try:
        # Verifica token JWT no header Authorization
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = token_manager.verify_access_token(token)

            if payload:
                # Token válido
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM users WHERE id = ?", (payload["user_id"],)
                )
                user = cursor.fetchone()
                conn.close()

                if user:
                    return jsonify(
                        {
                            "success": True,
                            "authenticated": True,
                            "user": {
                                "id": user[0],
                                "username": user[1],
                                "name": user[2],
                                "email": user[3],
                                "department": user[4],
                            },
                        }
                    )

        # Fallback: verifica sessão do Flask
        if "user_id" in session:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
            user = cursor.fetchone()
            conn.close()

            if user:
                return jsonify(
                    {
                        "success": True,
                        "authenticated": True,
                        "user": {
                            "id": user[0],
                            "username": user[1],
                            "name": user[2],
                            "email": user[3],
                            "department": user[4],
                        },
                    }
                )

        # Não autenticado
        return (
            jsonify(
                {
                    "success": True,
                    "authenticated": False,
                    "message": "Usuário não autenticado",
                }
            ),
            401,
        )

    except Exception as e:
        logger.error(f"Erro na verificação de autenticação: {e}")
        return (
            jsonify({"success": False, "message": "Erro ao verificar autenticação"}),
            500,
        )


@auth_bp.route("/api/auth/refresh", methods=["POST"])
def refresh_token():
    """
    ✅ Endpoint para renovar token (implementação do checklist)
    """
    try:
        data = request.get_json() or {}
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return (
                jsonify({"success": False, "message": "Refresh token não fornecido"}),
                400,
            )

        # ✅ Usa o gerenciador de tokens para renovar
        token_data = token_manager.refresh_access_token(refresh_token)

        if not token_data:
            return (
                jsonify(
                    {"success": False, "message": "Refresh token inválido ou expirado"}
                ),
                401,
            )

        return jsonify(
            {"success": True, **token_data, "message": "Token renovado com sucesso"}
        )

    except Exception as e:
        logger.error(f"Erro na renovação do token: {e}")
        return jsonify({"success": False, "message": "Erro ao renovar token"}), 500


def require_auth(f):
    """
    ✅ Decorator para proteger rotas (implementação do checklist)
    Verifica token JWT ou sessão do Flask
    """
    from functools import wraps

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Verifica token JWT
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            payload = token_manager.verify_access_token(token)

            if payload:
                request.current_user_id = payload["user_id"]
                request.current_username = payload["username"]
                return f(*args, **kwargs)

        # Fallback: verifica sessão do Flask
        if "user_id" in session:
            request.current_user_id = session["user_id"]
            request.current_username = session["username"]
            return f(*args, **kwargs)

        # Não autenticado
        return (
            jsonify(
                {"success": False, "message": "Acesso negado. Faça login novamente."}
            ),
            401,
        )

    return decorated_function


# ✅ Endpoints adicionais para gerenciamento de tokens


@auth_bp.route("/api/auth/tokens", methods=["GET"])
@require_auth
def list_user_tokens():
    """
    Lista tokens ativos do usuário
    """
    try:
        user_id = getattr(request, "current_user_id", session.get("user_id"))
        tokens = token_manager.get_user_active_tokens(user_id)

        return jsonify({"success": True, "tokens": tokens})

    except Exception as e:
        logger.error(f"Erro ao listar tokens: {e}")
        return jsonify({"success": False, "message": "Erro ao listar tokens"}), 500


@auth_bp.route("/api/auth/revoke-all", methods=["POST"])
@require_auth
def revoke_all_tokens():
    """
    Revoga todos os tokens do usuário
    """
    try:
        user_id = getattr(request, "current_user_id", session.get("user_id"))
        revoked_count = token_manager.revoke_all_user_tokens(user_id)

        # Limpa sessão atual também
        session.clear()

        return jsonify(
            {
                "success": True,
                "revoked_count": revoked_count,
                "message": f"{revoked_count} tokens revogados",
            }
        )

    except Exception as e:
        logger.error(f"Erro ao revogar tokens: {e}")
        return jsonify({"success": False, "message": "Erro ao revogar tokens"}), 500


@auth_bp.route("/api/auth/cleanup", methods=["POST"])
@require_auth
def cleanup_tokens():
    """
    Limpa tokens expirados (apenas para admins)
    """
    try:
        # Verifica se usuário é admin (implementar conforme necessário)
        deleted_count = token_manager.cleanup_expired_tokens()

        return jsonify(
            {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"{deleted_count} tokens expirados removidos",
            }
        )

    except Exception as e:
        logger.error(f"Erro na limpeza de tokens: {e}")
        return jsonify({"success": False, "message": "Erro na limpeza de tokens"}), 500


