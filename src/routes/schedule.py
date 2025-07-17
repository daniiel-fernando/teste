from flask import Blueprint, request, jsonify, session
from datetime import datetime, time, timedelta
import json
from src.models.scheduled_message import ScheduledMessage, db
from src.utils.scheduler import scheduler, schedule_message_job

schedule_bp = Blueprint('schedule', __name__)

@schedule_bp.route('/schedule-message', methods=['POST'])
def schedule_message():
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Verifica se o usuário está logado
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        image_url = data.get('image_url', '').strip()
        schedule_time = data.get('schedule_time', '').strip()
        schedule_days = data.get('schedule_days', 'daily')
        recipients = data.get('recipients', [])
        
        # Validações
        if not title:
            return jsonify({'error': 'Título é obrigatório'}), 400
        
        if not content and not image_url:
            return jsonify({'error': 'Mensagem deve conter texto ou imagem'}), 400
        
        if not schedule_time:
            return jsonify({'error': 'Horário é obrigatório'}), 400
        
        # Valida formato do horário
        try:
            time_obj = datetime.strptime(schedule_time, '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de horário inválido. Use HH:MM'}), 400
        
        # Determina o tipo de mensagem
        message_type = 'text'
        if image_url and content:
            message_type = 'mixed'
        elif image_url:
            message_type = 'image'
        
        # Calcula próximo envio
        next_send = calculate_next_send(schedule_time, schedule_days)
        
        # Cria o agendamento
        scheduled_msg = ScheduledMessage(
            title=title,
            content=content if content else None,
            image_url=image_url if image_url else None,
            message_type=message_type,
            schedule_time=schedule_time,
            schedule_days=schedule_days,
            recipients=json.dumps(recipients) if recipients else None,
            created_by=session['user_id'],
            next_send=next_send
        )
        
        db.session.add(scheduled_msg)
        db.session.commit()
        
        # Agenda o job
        schedule_message_job(scheduled_msg)
        
        return jsonify({
            'success': True,
            'message': 'Mensagem agendada com sucesso',
            'data': scheduled_msg.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@schedule_bp.route('/scheduled-messages', methods=['GET'])
def get_scheduled_messages():
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        messages = ScheduledMessage.query.filter_by(
            created_by=session['user_id']
        ).order_by(ScheduledMessage.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'messages': [msg.to_dict() for msg in messages]
        })
        
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar agendamentos: {str(e)}'}), 500

@schedule_bp.route('/scheduled-messages/<int:message_id>', methods=['PUT'])
def update_scheduled_message(message_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        data = request.get_json()
        scheduled_msg = ScheduledMessage.query.get_or_404(message_id)
        
        # Verifica permissão
        if scheduled_msg.created_by != session['user_id']:
            return jsonify({'error': 'Sem permissão para editar este agendamento'}), 403
        
        # Atualiza campos
        if 'is_active' in data:
            scheduled_msg.is_active = data['is_active']
        
        if 'title' in data:
            scheduled_msg.title = data['title']
        
        if 'content' in data:
            scheduled_msg.content = data['content']
        
        if 'image_url' in data:
            scheduled_msg.image_url = data['image_url']
        
        if 'schedule_time' in data:
            scheduled_msg.schedule_time = data['schedule_time']
            scheduled_msg.next_send = calculate_next_send(
                data['schedule_time'], 
                scheduled_msg.schedule_days
            )
        
        if 'schedule_days' in data:
            scheduled_msg.schedule_days = data['schedule_days']
            scheduled_msg.next_send = calculate_next_send(
                scheduled_msg.schedule_time, 
                data['schedule_days']
            )
        
        db.session.commit()
        
        # Reagenda o job
        schedule_message_job(scheduled_msg)
        
        return jsonify({
            'success': True,
            'message': 'Agendamento atualizado com sucesso',
            'data': scheduled_msg.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao atualizar agendamento: {str(e)}'}), 500

@schedule_bp.route('/scheduled-messages/<int:message_id>', methods=['DELETE'])
def delete_scheduled_message(message_id):
    try:
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        
        scheduled_msg = ScheduledMessage.query.get_or_404(message_id)
        
        # Verifica permissão
        if scheduled_msg.created_by != session['user_id']:
            return jsonify({'error': 'Sem permissão para deletar este agendamento'}), 403
        
        # Remove job do scheduler
        try:
            scheduler.remove_job(f'scheduled_msg_{message_id}')
        except:
            pass  # Job pode não existir
        
        db.session.delete(scheduled_msg)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Agendamento deletado com sucesso'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Erro ao deletar agendamento: {str(e)}'}), 500

def calculate_next_send(schedule_time, schedule_days):
    """Calcula o próximo horário de envio"""
    now = datetime.now()
    time_obj = datetime.strptime(schedule_time, '%H:%M').time()
    
    # Combina data atual com horário agendado
    next_send = datetime.combine(now.date(), time_obj)
    
    # Se o horário já passou hoje, agenda para amanhã
    if next_send <= now:
        next_send += timedelta(days=1)
    
    # Ajusta baseado nos dias da semana
    if schedule_days == 'weekdays':
        # Segunda a sexta (0-4)
        while next_send.weekday() > 4:
            next_send += timedelta(days=1)
    elif schedule_days == 'weekends':
        # Sábado e domingo (5-6)
        while next_send.weekday() < 5:
            next_send += timedelta(days=1)
    
    return next_send

