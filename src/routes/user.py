from flask import Blueprint, jsonify, request, session
from src.models.user import User, db

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    """Retorna lista de usuários"""
    if not session.get("authenticated"):
        return jsonify({"error": "Não autenticado"}), 401
    
    try:
        users = User.query.filter_by(is_active=True).all()
        return jsonify({
            "success": True,
            "users": [user.to_dict() for user in users]
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar usuários: {str(e)}"}), 500

@user_bp.route('/users', methods=['POST'])
def create_user():
    """Cria novo usuário (apenas admins)"""
    if not session.get("authenticated") or not session.get("is_admin"):
        return jsonify({"error": "Sem permissão"}), 403
    
    try:
        data = request.get_json()
        
        # Validações
        if not data.get('username') or not data.get('email'):
            return jsonify({"error": "Username e email são obrigatórios"}), 400
        
        # Verifica se usuário já existe
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({"error": "Usuário ou email já existe"}), 400
        
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data.get('full_name'),
            department=data.get('department'),
            is_admin=data.get('is_admin', False)
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Usuário criado com sucesso",
            "user": user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao criar usuário: {str(e)}"}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Retorna dados de um usuário específico"""
    if not session.get("authenticated"):
        return jsonify({"error": "Não autenticado"}), 401
    
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            "success": True,
            "user": user.to_dict()
        })
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar usuário: {str(e)}"}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Atualiza dados do usuário"""
    if not session.get("authenticated"):
        return jsonify({"error": "Não autenticado"}), 401
    
    # Usuário pode editar próprio perfil ou admin pode editar qualquer um
    current_user_id = int(session.get("user_id", 0))
    is_admin = session.get("is_admin", False)
    
    if user_id != current_user_id and not is_admin:
        return jsonify({"error": "Sem permissão"}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # Campos que podem ser atualizados
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'email' in data:
            user.email = data['email']
        if 'department' in data:
            user.department = data['department']
        
        # Apenas admin pode alterar status e permissões
        if is_admin:
            if 'is_active' in data:
                user.is_active = data['is_active']
            if 'is_admin' in data:
                user.is_admin = data['is_admin']
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Usuário atualizado com sucesso",
            "user": user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao atualizar usuário: {str(e)}"}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Desativa usuário (apenas admins)"""
    if not session.get("authenticated") or not session.get("is_admin"):
        return jsonify({"error": "Sem permissão"}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Não permite deletar próprio usuário
        current_user_id = int(session.get("user_id", 0))
        if user_id == current_user_id:
            return jsonify({"error": "Não é possível deletar próprio usuário"}), 400
        
        # Desativa ao invés de deletar
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Usuário desativado com sucesso"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Erro ao desativar usuário: {str(e)}"}), 500

@user_bp.route('/profile', methods=['GET'])
def get_profile():
    """Retorna perfil do usuário logado"""
    if not session.get("authenticated"):
        return jsonify({"error": "Não autenticado"}), 401
    
    try:
        user_id = int(session.get("user_id"))
        user = User.query.get_or_404(user_id)
        
        return jsonify({
            "success": True,
            "user": user.to_dict()
        })
        
    except Exception as e:
        return jsonify({"error": f"Erro ao buscar perfil: {str(e)}"}), 500

