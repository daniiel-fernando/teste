from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import json
import atexit

scheduler = BackgroundScheduler()
scheduler.start()

# Registra função para parar o scheduler quando a aplicação encerrar
atexit.register(lambda: scheduler.shutdown())

def init_scheduler(app):
    """Inicializa o scheduler com o contexto da aplicação"""
    with app.app_context():
        try:
            # Carrega agendamentos existentes do banco
            from src.models.scheduled_message import ScheduledMessage
            active_schedules = ScheduledMessage.query.filter_by(is_active=True).all()
            
            for schedule in active_schedules:
                schedule_message_job(schedule)
        except Exception as e:
            # Tabelas ainda não foram criadas, ignora o erro
            print(f"Scheduler initialization skipped: {e}")

def schedule_message_job(scheduled_message):
    """Agenda um job para enviar mensagem"""
    job_id = f'scheduled_msg_{scheduled_message.id}'
    
    # Remove job existente se houver
    try:
        scheduler.remove_job(job_id)
    except:
        pass
    
    if not scheduled_message.is_active:
        return
    
    # Cria trigger baseado na configuração
    if scheduled_message.schedule_days == 'daily':
        trigger = CronTrigger(
            hour=int(scheduled_message.schedule_time.split(':')[0]),
            minute=int(scheduled_message.schedule_time.split(':')[1])
        )
    elif scheduled_message.schedule_days == 'weekdays':
        trigger = CronTrigger(
            day_of_week='mon-fri',
            hour=int(scheduled_message.schedule_time.split(':')[0]),
            minute=int(scheduled_message.schedule_time.split(':')[1])
        )
    elif scheduled_message.schedule_days == 'weekends':
        trigger = CronTrigger(
            day_of_week='sat-sun',
            hour=int(scheduled_message.schedule_time.split(':')[0]),
            minute=int(scheduled_message.schedule_time.split(':')[1])
        )
    else:
        # Para dias específicos da semana
        trigger = CronTrigger(
            day_of_week=scheduled_message.schedule_days,
            hour=int(scheduled_message.schedule_time.split(':')[0]),
            minute=int(scheduled_message.schedule_time.split(':')[1])
        )
    
    # Agenda o job
    scheduler.add_job(
        func=send_scheduled_message,
        trigger=trigger,
        id=job_id,
        args=[scheduled_message.id],
        replace_existing=True
    )

def send_scheduled_message(scheduled_message_id):
    """Envia uma mensagem agendada"""
    from src.models.scheduled_message import ScheduledMessage
    from src.models.message import Message, db
    from src.main import app
    
    with app.app_context():
        try:
            scheduled_msg = ScheduledMessage.query.get(scheduled_message_id)
            if not scheduled_msg or not scheduled_msg.is_active:
                return
            
            # Cria uma nova mensagem baseada no agendamento
            message = Message(
                sender_id=scheduled_msg.created_by,
                sender_name='Sistema Agendado',
                content=scheduled_msg.content,
                image_url=scheduled_msg.image_url,
                message_type=scheduled_msg.message_type,
                recipients=scheduled_msg.recipients,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(message)
            
            # Atualiza informações do agendamento
            scheduled_msg.last_sent = datetime.utcnow()
            scheduled_msg.next_send = calculate_next_send_time(scheduled_msg)
            
            db.session.commit()
            
            print(f"Mensagem agendada enviada: {scheduled_msg.title}")
            
            # Aqui você pode implementar a lógica real de envio
            # (WebSocket, email, notificação push, etc.)
            
        except Exception as e:
            print(f"Erro ao enviar mensagem agendada {scheduled_message_id}: {e}")
            db.session.rollback()

def calculate_next_send_time(scheduled_msg):
    """Calcula o próximo horário de envio"""
    from datetime import datetime, timedelta
    
    now = datetime.now()
    time_parts = scheduled_msg.schedule_time.split(':')
    hour, minute = int(time_parts[0]), int(time_parts[1])
    
    # Próximo envio baseado na configuração
    if scheduled_msg.schedule_days == 'daily':
        next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_send <= now:
            next_send += timedelta(days=1)
    elif scheduled_msg.schedule_days == 'weekdays':
        next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_send <= now:
            next_send += timedelta(days=1)
        # Ajusta para próximo dia útil
        while next_send.weekday() > 4:  # 0-6, onde 0=segunda
            next_send += timedelta(days=1)
    elif scheduled_msg.schedule_days == 'weekends':
        next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_send <= now:
            next_send += timedelta(days=1)
        # Ajusta para próximo fim de semana
        while next_send.weekday() < 5:  # 5=sábado, 6=domingo
            next_send += timedelta(days=1)
    else:
        # Para configurações específicas, agenda para próximo dia
        next_send = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_send <= now:
            next_send += timedelta(days=1)
    
    return next_send

