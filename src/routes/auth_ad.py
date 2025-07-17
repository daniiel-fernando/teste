from flask import Blueprint, request, jsonify, session
from datetime import datetime
import logging

from src.models.user import User, db
from src.utils.ad_auth import authenticate_ad_user, is_ad_available

auth_ad_bp = Blueprint("auth_ad", __name__)

# Configura log
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)


@auth_ad_bp.route("/login-ad", methods=["POST"])
def login_ad():
    """
    Login com Active Directory.
    Requer que o usuário pertença ao grupo GG_TECNOLOGIA.
    """
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "Usuário e senha são obrigatórios"}), 400

        if not is_ad_available():
            logging.warning("Active Directory não está disponível.")
            return (
                jsonify(
                    {
                        "error": "Sistema de autenticação indisponível.",
                        "details": "O servidor Active Directory não está acessível no momento.",
                    }
                ),
                503,
            )

        ad_user = authenticate_ad_user(username, password)

        if not ad_user:
            return (
                jsonify(
                    {
                        "error": "Acesso negado. Apenas usuários do grupo GG_TECNOLOGIA podem acessar o sistema.",
                        "details": "Entre em contato com a TI para solicitar acesso.",
                    }
                ),
                403,
            )

        # Cria ou atualiza o usuário local
        local_user = User.query.filter_by(username=username).first()
        if not local_user:
            local_user = User(
                username=username,
                email=ad_user.get("email") or f"{username}@dominio.local",
                full_name=ad_user.get("display_name", username),
                department=ad_user.get("department", "TI"),
                is_active=True,
                is_admin=ad_user.get("is_admin", False),
            )
            db.session.add(local_user)
        else:
            # Atualiza dados
            local_user.email = ad_user.get("email") or local_user.email
            local_user.full_name = ad_user.get("display_name") or local_user.full_name
            local_user.department = ad_user.get(
                "department", local_user.department or "TI"
            )
            local_user.is_admin = ad_user.get("is_admin", local_user.is_admin)
            local_user.is_active = True

        local_user.last_login = datetime.utcnow()
        db.session.commit()

        # Inicia sessão
        session.update(
            {
                "authenticated": True,
                "user_id": str(local_user.id),
                "username": username,
                "user_name": local_user.full_name or username,
                "is_admin": local_user.is_admin,
                "auth_method": "active_directory",
            }
        )

        return jsonify(
            {
                "success": True,
                "message": "Autenticado via Active Directory",
                "user": {
                    "id": local_user.id,
                    "username": username,
                    "name": local_user.full_name or username,
                    "is_admin": local_user.is_admin,
                    "department": local_user.department,
                },
            }
        )

    except Exception as e:
        logging.error(f"Erro no login AD: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500


@auth_ad_bp.route("/ad-status", methods=["GET"])
def ad_status():
    """
    Verifica a disponibilidade do Active Directory.
    Acesso restrito a usuários administradores autenticados.
    """
    try:
        if not session.get("authenticated") or not session.get("is_admin"):
            return jsonify({"error": "Acesso negado"}), 403

        ad_available = is_ad_available()

        return jsonify(
            {
                "success": True,
                "ad_available": ad_available,
                "message": (
                    "Active Directory disponível"
                    if ad_available
                    else "Active Directory indisponível"
                ),
            }
        )

    except Exception as e:
        logging.error(f"Erro ao verificar status do AD: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500
