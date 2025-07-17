from flask import Blueprint, request, jsonify, session
from datetime import datetime
import json
import os
from src.models.message import Message, db
from src.models.user import User

message_bp = Blueprint("message", __name__)


@message_bp.route("/send-message", methods=["POST"])
def send_message():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Dados não fornecidos"}), 400

        if "user_id" not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401

        sender_id = session["user_id"]
        sender_name = session.get("user_name", "Usuário Desconhecido")

        content = data.get("content", "").strip()
        image_url = data.get("image_url", "").strip()
        recipients = data.get("recipients", [])  # Lista de IPs ou identificadores

        message_type = "text"
        if image_url and content:
            message_type = "mixed"
        elif image_url:
            message_type = "image"

        if not content and not image_url:
            return jsonify({"error": "Mensagem deve conter texto ou imagem"}), 400

        # Cria a mensagem com delivered_to vazio inicialmente
        message = Message(
            sender_id=sender_id,
            sender_name=sender_name,
            content=content if content else None,
            image_url=image_url if image_url else None,
            message_type=message_type,
            recipients=json.dumps(recipients),
            delivered_to=json.dumps([]),
            timestamp=datetime.utcnow(),
            status="sent",  # Status será atualizado pelo polling do cliente
        )

        db.session.add(message)
        db.session.commit()

        return jsonify(
            {
                "success": True,
                "message": "Mensagem enviada com sucesso",
                "data": message.to_dict(),
            }
        )

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro interno: {str(e)}"}), 500


@message_bp.route("/messages", methods=["GET"])
def get_messages():
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)

        messages = Message.query.order_by(Message.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify(
            {
                "success": True,
                "messages": [msg.to_dict() for msg in messages.items],
                "total": messages.total,
                "pages": messages.pages,
                "current_page": page,
            }
        )

    except Exception as e:
        return jsonify({"error": f"Erro ao buscar mensagens: {str(e)}"}), 500


@message_bp.route("/messages/<int:message_id>", methods=["DELETE"])
def delete_message(message_id):
    try:
        if "user_id" not in session:
            return jsonify({"error": "Usuário não autenticado"}), 401

        message = Message.query.get_or_404(message_id)

        if message.sender_id != session["user_id"]:
            return jsonify({"error": "Sem permissão para deletar esta mensagem"}), 403

        if message.image_url:
            try:
                image_path = os.path.join(
                    "uploads", os.path.basename(message.image_url)
                )
                if os.path.exists(image_path):
                    os.remove(image_path)
            except Exception as e:
                print(f"Erro ao remover imagem: {e}")

        db.session.delete(message)
        db.session.commit()

        return jsonify({"success": True, "message": "Mensagem deletada com sucesso"})

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao deletar mensagem: {str(e)}"}), 500
