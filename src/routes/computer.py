from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta
import socket
import platform
import logging
from src.models.computer import Computer, db

computer_bp = Blueprint("computer", __name__)

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO)

@computer_bp.route("/computers", methods=["GET"])
def get_computers():
    """Lista todos os computadores registrados"""
    try:
        if not session.get("authenticated"):
            return jsonify({"error": "Não autenticado"}), 401
        
        # Parâmetros de filtro
        department = request.args.get('department')
        online_only = request.args.get('online_only', 'false').lower() == 'true'
        
        query = Computer.query
        
        if department:
            query = query.filter_by(department=department)
        
        if online_only:
            query = query.filter_by(is_online=True)
        
        computers = query.order_by(Computer.computer_name).all()
        
        return jsonify({
            "success": True,
            "computers": [computer.to_dict() for computer in computers]
        })
        
    except Exception as e:
        logging.error(f"Erro ao listar computadores: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@computer_bp.route("/computers/register", methods=["POST"])
def register_computer():
    """Registra um computador no sistema"""
    try:
        data = request.get_json()
        
        computer_name = data.get("computer_name") or platform.node()
        ip_address = data.get("ip_address") or request.remote_addr
        mac_address = data.get("mac_address")
        department = data.get("department", "TI")
        user_name = data.get("user_name")
        
        if not computer_name:
            return jsonify({"error": "Nome do computador é obrigatório"}), 400
        
        computer = Computer.register_computer(
            computer_name=computer_name,
            ip_address=ip_address,
            mac_address=mac_address,
            department=department,
            user_name=user_name
        )
        
        return jsonify({
            "success": True,
            "message": "Computador registrado com sucesso",
            "computer": computer.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Erro ao registrar computador: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@computer_bp.route("/computers/<int:computer_id>", methods=["PUT"])
def update_computer(computer_id):
    """Atualiza informações de um computador"""
    try:
        if not session.get("authenticated"):
            return jsonify({"error": "Não autenticado"}), 401
        
        computer = Computer.query.get_or_404(computer_id)
        data = request.get_json()
        
        # Campos atualizáveis
        if "department" in data:
            computer.department = data["department"]
        if "user_name" in data:
            computer.user_name = data["user_name"]
        if "is_online" in data:
            computer.is_online = data["is_online"]
        
        computer.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Computador atualizado com sucesso",
            "computer": computer.to_dict()
        })
        
    except Exception as e:
        logging.error(f"Erro ao atualizar computador: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@computer_bp.route("/computers/<int:computer_id>", methods=["DELETE"])
def delete_computer(computer_id):
    """Remove um computador do sistema"""
    try:
        if not session.get("authenticated"):
            return jsonify({"error": "Não autenticado"}), 401
        
        if not session.get("is_admin"):
            return jsonify({"error": "Acesso negado"}), 403
        
        computer = Computer.query.get_or_404(computer_id)
        
        db.session.delete(computer)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Computador removido com sucesso"
        })
        
    except Exception as e:
        logging.error(f"Erro ao remover computador: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@computer_bp.route("/computers/heartbeat", methods=["POST"])
def computer_heartbeat():
    """Endpoint para computadores enviarem heartbeat"""
    try:
        data = request.get_json() or {}
        
        computer_name = data.get("computer_name") or platform.node()
        ip_address = request.remote_addr
        mac_address = data.get("mac_address")
        department = data.get("department", "TI")
        user_name = data.get("user_name")
        
        # Registra ou atualiza o computador
        computer = Computer.register_computer(
            computer_name=computer_name,
            ip_address=ip_address,
            mac_address=mac_address,
            department=department,
            user_name=user_name
        )
        
        return jsonify({
            "success": True,
            "message": "Heartbeat recebido",
            "computer_id": computer.id
        })
        
    except Exception as e:
        logging.error(f"Erro no heartbeat: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@computer_bp.route("/computers/cleanup", methods=["POST"])
def cleanup_offline_computers():
    """Remove computadores offline há mais de X dias"""
    try:
        if not session.get("authenticated"):
            return jsonify({"error": "Não autenticado"}), 401
        
        if not session.get("is_admin"):
            return jsonify({"error": "Acesso negado"}), 403
        
        days = request.json.get("days", 30)  # Padrão: 30 dias
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Marca como offline computadores que não enviaram heartbeat
        offline_computers = Computer.query.filter(
            Computer.last_seen < cutoff_date
        ).all()
        
        count = 0
        for computer in offline_computers:
            computer.mark_offline()
            count += 1
        
        return jsonify({
            "success": True,
            "message": f"{count} computadores marcados como offline"
        })
        
    except Exception as e:
        logging.error(f"Erro na limpeza: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

@computer_bp.route("/computers/departments", methods=["GET"])
def get_departments():
    """Lista departamentos únicos dos computadores"""
    try:
        if not session.get("authenticated"):
            return jsonify({"error": "Não autenticado"}), 401
        
        departments = db.session.query(Computer.department).distinct().all()
        department_list = [dept[0] for dept in departments if dept[0]]
        
        return jsonify({
            "success": True,
            "departments": sorted(department_list)
        })
        
    except Exception as e:
        logging.error(f"Erro ao listar departamentos: {e}")
        return jsonify({"error": "Erro interno do servidor"}), 500

