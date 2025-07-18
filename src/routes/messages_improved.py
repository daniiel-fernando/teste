"""
Rotas de Mensagens Melhoradas
Sistema de Notificações Jotanunes - Versão 2.2.0
✅ Implementa correções para notificações repetidas
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
import sqlite3
import os
import json

# Importa decorator de autenticação
from src.routes.auth_improved import require_auth

from src.config import Config

messages_bp = Blueprint("messages_improved", __name__)

# Configura log
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_db_connection():
    """Obtém conexão com o banco de dados"""
    conn = sqlite3.connect(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", Config.DATABASE_PATH
        )
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_message_status_table():
    """
    ✅ Inicializa tabela para controle de status de leitura das mensagens
    Implementação do checklist para evitar notificações repetidas
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabela para controlar status de leitura por computador
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS message_read_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            computer_id INTEGER NOT NULL,
            computer_name TEXT NOT NULL,
            status TEXT DEFAULT 'unread', -- 'unread', 'delivered', 'read'
            delivered_at TIMESTAMP,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (message_id) REFERENCES messages (id),
            FOREIGN KEY (computer_id) REFERENCES computers (id),
            UNIQUE(message_id, computer_id)
        )
    """
    )

    # Índices para performance
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_message_read_status_message_id 
        ON message_read_status(message_id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_message_read_status_computer_id 
        ON message_read_status(computer_id)
    """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_message_read_status_status 
        ON message_read_status(status)
    """
    )

    conn.commit()
    conn.close()

    logger.info("Tabela de status de leitura inicializada")


@messages_bp.route("/api/messages/for-computer/<computer_name>")
def get_unread_messages_for_computer(computer_name):
    """
    ✅ Busca apenas mensagens NÃO LIDAS para um computador específico
    Implementação do checklist para evitar notificações repetidas
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca dados do computador
        cursor.execute(
            "SELECT id, department FROM computers WHERE computer_name = ?",
            (computer_name,),
        )
        computer = cursor.fetchone()

        if not computer:
            return (
                jsonify({"success": False, "message": "Computador não encontrado"}),
                404,
            )

        computer_id = computer[0]
        department = computer[1]

        # ✅ Busca apenas mensagens NÃO LIDAS para este computador
        cursor.execute(
            """
            SELECT DISTINCT m.id, m.title, m.content, m.image_path, m.urgent, 
                   m.confirmation_required, m.sound_enabled, m.created_at,
                   u.name as sender_name
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            LEFT JOIN message_read_status mrs ON m.id = mrs.message_id AND mrs.computer_id = ?
            WHERE (
                -- Mensagem direcionada para este departamento ou "all"
                (m.recipients LIKE ? OR m.recipients LIKE ?)
                -- E ainda não foi lida por este computador
                AND (mrs.status IS NULL OR mrs.status = 'unread')
                -- Mensagens das últimas 24 horas
                AND m.created_at > datetime('now', '-1 day')
            )
            ORDER BY m.urgent DESC, m.created_at DESC
            LIMIT 50
        """,
            (computer_id, f'%"{department}"%', '%"all"%'),
        )

        messages = []
        for row in cursor.fetchall():
            message = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "image_url": f"/uploads/{row[3]}" if row[3] else None,
                "urgent": bool(row[4]),
                "confirmation_required": bool(row[5]),
                "sound_enabled": bool(row[6]),
                "timestamp": row[7],
                "sender_name": row[8],
            }
            messages.append(message)

            # ✅ Marca como entregue automaticamente
            cursor.execute(
                """
                INSERT OR REPLACE INTO message_read_status 
                (message_id, computer_id, computer_name, status, delivered_at)
                VALUES (?, ?, ?, 'delivered', ?)
            """,
                (row[0], computer_id, computer_name, datetime.now()),
            )

        conn.commit()
        conn.close()

        logger.info(
            f"Entregues {len(messages)} mensagens não lidas para {computer_name}"
        )

        return jsonify({"success": True, "messages": messages, "count": len(messages)})

    except Exception as e:
        logger.error(f"Erro ao buscar mensagens para {computer_name}: {e}")
        return jsonify({"success": False, "message": "Erro ao buscar mensagens"}), 500


@messages_bp.route("/api/messages/<int:message_id>/read", methods=["POST"])
def mark_message_as_read(message_id):
    """
    ✅ Marca mensagem como lida por um computador específico
    Implementação do checklist - POST /api/messages/:id/read
    """
    try:
        data = request.get_json() or {}
        computer_name = data.get("computer_name")

        if not computer_name:
            return (
                jsonify(
                    {"success": False, "message": "Nome do computador é obrigatório"}
                ),
                400,
            )

        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca ID do computador
        cursor.execute(
            "SELECT id FROM computers WHERE computer_name = ?", (computer_name,)
        )
        computer = cursor.fetchone()

        if not computer:
            return (
                jsonify({"success": False, "message": "Computador não encontrado"}),
                404,
            )

        computer_id = computer[0]

        # ✅ Marca mensagem como lida
        cursor.execute(
            """
            INSERT OR REPLACE INTO message_read_status 
            (message_id, computer_id, computer_name, status, delivered_at, read_at)
            VALUES (?, ?, ?, 'read', 
                    COALESCE((SELECT delivered_at FROM message_read_status 
                             WHERE message_id = ? AND computer_id = ?), ?),
                    ?)
        """,
            (
                message_id,
                computer_id,
                computer_name,
                message_id,
                computer_id,
                datetime.now(),
                datetime.now(),
            ),
        )

        conn.commit()
        conn.close()

        logger.info(f"Mensagem {message_id} marcada como lida por {computer_name}")

        return jsonify({"success": True, "message": "Mensagem marcada como lida"})

    except Exception as e:
        logger.error(f"Erro ao marcar mensagem {message_id} como lida: {e}")
        return (
            jsonify({"success": False, "message": "Erro ao marcar mensagem como lida"}),
            500,
        )


@messages_bp.route("/api/messages/<int:message_id>/status")
@require_auth
def get_message_status(message_id):
    """
    ✅ Obtém status de leitura de uma mensagem
    Mostra quais computadores leram a mensagem
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Busca status da mensagem
        cursor.execute(
            """
            SELECT mrs.computer_name, mrs.status, mrs.delivered_at, mrs.read_at,
                   c.department, c.user_name
            FROM message_read_status mrs
            LEFT JOIN computers c ON mrs.computer_id = c.id
            WHERE mrs.message_id = ?
            ORDER BY mrs.read_at DESC, mrs.delivered_at DESC
        """,
            (message_id,),
        )

        status_list = []
        for row in cursor.fetchall():
            status_list.append(
                {
                    "computer_name": row[0],
                    "status": row[1],
                    "delivered_at": row[2],
                    "read_at": row[3],
                    "department": row[4],
                    "user_name": row[5],
                }
            )

        # Estatísticas
        total_delivered = len(
            [s for s in status_list if s["status"] in ["delivered", "read"]]
        )
        total_read = len([s for s in status_list if s["status"] == "read"])

        conn.close()

        return jsonify(
            {
                "success": True,
                "message_id": message_id,
                "status_list": status_list,
                "statistics": {
                    "total_delivered": total_delivered,
                    "total_read": total_read,
                    "read_percentage": round(
                        (
                            (total_read / total_delivered * 100)
                            if total_delivered > 0
                            else 0
                        ),
                        2,
                    ),
                },
            }
        )

    except Exception as e:
        logger.error(f"Erro ao buscar status da mensagem {message_id}: {e}")
        return (
            jsonify({"success": False, "message": "Erro ao buscar status da mensagem"}),
            500,
        )


@messages_bp.route("/api/messages/cleanup", methods=["POST"])
@require_auth
def cleanup_old_messages():
    """
    ✅ Remove mensagens antigas para evitar acúmulo
    Implementação do checklist - limpeza de mensagens
    """
    try:
        data = request.get_json() or {}
        days_old = data.get(
            "days_old", Config.MESSAGE_CLEANUP_DAYS
        )  # Remove mensagens com mais de 7 dias por padrão

        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove status de leitura de mensagens antigas
        cursor.execute(
            """
            DELETE FROM message_read_status 
            WHERE message_id IN (
                SELECT id FROM messages 
                WHERE created_at < datetime('now', '-{} days')
            )
        """.format(
                days_old
            )
        )

        status_removed = cursor.rowcount

        # Remove mensagens antigas
        cursor.execute(
            """
            DELETE FROM messages 
            WHERE created_at < datetime('now', '-{} days')
        """.format(
                days_old
            )
        )

        messages_removed = cursor.rowcount

        conn.commit()
        conn.close()

        logger.info(
            f"Limpeza concluída: {messages_removed} mensagens e {status_removed} status removidos"
        )

        return jsonify(
            {
                "success": True,
                "messages_removed": messages_removed,
                "status_removed": status_removed,
                "message": f"Limpeza concluída: {messages_removed} mensagens antigas removidas",
            }
        )

    except Exception as e:
        logger.error(f"Erro na limpeza de mensagens: {e}")
        return (
            jsonify({"success": False, "message": "Erro na limpeza de mensagens"}),
            500,
        )


@messages_bp.route("/api/messages/statistics")
@require_auth
def get_message_statistics():
    """
    ✅ Estatísticas de entrega e leitura de mensagens
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Estatísticas gerais
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_messages,
                COUNT(CASE WHEN created_at > datetime('now', '-1 day') THEN 1 END) as today_messages,
                COUNT(CASE WHEN created_at > datetime('now', '-7 days') THEN 1 END) as week_messages
            FROM messages
        """
        )

        general_stats = cursor.fetchone()

        # Estatísticas de leitura
        cursor.execute(
            """
            SELECT 
                COUNT(*) as total_deliveries,
                COUNT(CASE WHEN status = 'read' THEN 1 END) as total_reads,
                COUNT(CASE WHEN status = 'delivered' THEN 1 END) as total_delivered_only
            FROM message_read_status
        """
        )

        read_stats = cursor.fetchone()

        # Top departamentos
        cursor.execute(
            """
            SELECT 
                c.department,
                COUNT(mrs.id) as message_count,
                COUNT(CASE WHEN mrs.status = 'read' THEN 1 END) as read_count
            FROM message_read_status mrs
            LEFT JOIN computers c ON mrs.computer_id = c.id
            WHERE mrs.delivered_at > datetime('now', '-7 days')
            GROUP BY c.department
            ORDER BY message_count DESC
        """
        )

        department_stats = []
        for row in cursor.fetchall():
            department_stats.append(
                {
                    "department": row[0],
                    "message_count": row[1],
                    "read_count": row[2],
                    "read_percentage": round(
                        (row[2] / row[1] * 100) if row[1] > 0 else 0, 2
                    ),
                }
            )

        conn.close()

        return jsonify(
            {
                "success": True,
                "general": {
                    "total_messages": general_stats[0],
                    "today_messages": general_stats[1],
                    "week_messages": general_stats[2],
                },
                "reading": {
                    "total_deliveries": read_stats[0],
                    "total_reads": read_stats[1],
                    "total_delivered_only": read_stats[2],
                    "read_percentage": round(
                        (
                            (read_stats[1] / read_stats[0] * 100)
                            if read_stats[0] > 0
                            else 0
                        ),
                        2,
                    ),
                },
                "departments": department_stats,
            }
        )

    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return (
            jsonify({"success": False, "message": "Erro ao buscar estatísticas"}),
            500,
        )


# Inicializa tabela ao importar o módulo
init_message_status_table()


@messages_bp.route("/api/messages/send", methods=["POST"])
@require_auth
def send_message():
    """
    Envia uma nova mensagem para os computadores.
    """
    try:
        title = request.form.get("title")
        content = request.form.get("content")
        recipients = request.form.getlist("recipients")
        target_ou = request.form.get("target_ou")
        urgent = request.form.get("urgent") == "true"
        confirmation_required = request.form.get("require_read_confirmation") == "true"
        sound_enabled = request.form.get("sound") == "true"
        image_file = request.files.get("image")

        if not title or not content:
            return jsonify({"success": False, "message": "Título e conteúdo são obrigatórios"}), 400

        if not recipients and target_ou != "all":
            return jsonify({"success": False, "message": "Selecione pelo menos um destinatário ou 'Todas as OUs'"}), 400

        image_path = None
        if image_file:
            # Salvar imagem (simplificado, em um ambiente real, faria validações e armazenamento seguro)
            upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "uploads")
            os.makedirs(upload_folder, exist_ok=True)
            image_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image_file.filename}"
            image_path = os.path.join(upload_folder, image_filename)
            image_file.save(image_path)
            image_path = image_filename # Salva apenas o nome do arquivo no DB

        conn = get_db_connection()
        cursor = conn.cursor()

        # Inserir mensagem no banco de dados
        cursor.execute(
            """
            INSERT INTO messages (title, content, image_path, urgent, confirmation_required, sound_enabled, recipients, target_ou, sender_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                content,
                image_path,
                urgent,
                confirmation_required,
                sound_enabled,
                json.dumps(recipients), # Armazena como JSON string
                target_ou,
                request.user.get("id") # Obtém o ID do usuário logado
            ),
        )
        message_id = cursor.lastrowid

        # Para cada computador que deve receber a mensagem, insere um registro em message_read_status
        if target_ou == "all":
            cursor.execute("SELECT id, computer_name FROM computers")
            computers_to_notify = cursor.fetchall()
        else:
            # Busca computadores pelos departamentos selecionados
            placeholders = ", ".join(["?"] * len(recipients))
            cursor.execute(f"SELECT id, computer_name FROM computers WHERE department IN ({placeholders})", recipients)
            computers_to_notify = cursor.fetchall()

        for comp_id, comp_name in computers_to_notify:
            cursor.execute(
                "INSERT INTO message_read_status (message_id, computer_id, computer_name, status) VALUES (?, ?, ?, ?)",
                (message_id, comp_id, comp_name, "unread"),
            )

        conn.commit()
        conn.close()

        logger.info(f"Mensagem '{title}' enviada com sucesso para {len(computers_to_notify)} computadores.")
        return jsonify({"success": True, "message": "Mensagem enviada com sucesso!"}), 200

    except Exception as e:
        logger.error(f"Erro ao enviar mensagem: {e}")
        return jsonify({"success": False, "message": "Erro ao enviar mensagem. Verifique sua conexão e tente novamente."}), 500





@messages_bp.route("/api/messages/history")
@require_auth
def get_message_history():
    """
    Obtém o histórico de mensagens enviadas.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT m.id, m.title, m.content, m.image_path, m.urgent, m.confirmation_required, m.sound_enabled, m.created_at, u.name as sender_name, m.recipients
            FROM messages m
            LEFT JOIN users u ON m.sender_id = u.id
            ORDER BY m.created_at DESC
            LIMIT 100
            """
        )
        messages = []
        for row in cursor.fetchall():
            message = {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "image_path": row[3],
                "urgent": bool(row[4]),
                "confirmation_required": bool(row[5]),
                "sound_enabled": bool(row[6]),
                "timestamp": row[7],
                "sender_name": row[8],
                "recipients": json.loads(row[9]) if row[9] else [] # Carrega de JSON string
            }
            messages.append(message)

        conn.close()
        return jsonify({"success": True, "messages": messages}), 200

    except Exception as e:
        logger.error(f"Erro ao obter histórico de mensagens: {e}")
        return jsonify({"success": False, "message": "Erro ao obter histórico de mensagens"}), 500


