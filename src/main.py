#!/usr/bin/env python3
"""
Sistema de Notificações Corporativas - Jotanunes
Servidor Flask Melhorado - Versão 2.1.0
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path


# ===============================
# Sistema de Notificações Jotanunes
# Arquivo principal do backend Flask
# ===============================


# Adiciona o diretório raiz ao sys.path para facilitar imports absolutos
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import (
    Flask,
    send_from_directory,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for,
)
from flask_session import Session
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
import sqlite3
import json


# Importa módulos utilitários do sistema
from src.utils.ad_auth import ActiveDirectoryAuth, get_computers_by_ou
from src.utils.timezone_converter import format_datetime_to_brasilia

# Instância global para consultas AD
ad_auth_instance = ActiveDirectoryAuth()


# Importa configurações globais
from src.config import Config

# Log do caminho do banco de dados usado
print(f"USANDO BANCO DE DADOS EM: {Config.get_db_path()}")
logger = logging.getLogger(__name__)


# Configuração de logging (arquivo + console)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("notifications_server.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def create_app():
    """
    Factory function para criar a aplicação Flask.
    Responsável por configurar extensões, rotas, banco de dados e middlewares.
    """

    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
    )

    # Configurações
    app.config.from_object(Config)

    # Cria diretórios necessários para uploads e sessões
    upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
    os.makedirs(upload_folder, exist_ok=True)
    session_dir = os.path.join(os.path.dirname(__file__), "sessions")
    os.makedirs(session_dir, exist_ok=True)

    # CORS - permite todas as origens para desenvolvimento (ajuste para produção!)
    CORS(
        app,
        supports_credentials=True,
        origins=["*"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Configurações de sessão
    app.config["SESSION_TYPE"] = "filesystem"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_FILE_DIR"] = session_dir
    Session(app)

    # Inicializa banco de dados ANTES de registrar blueprints
    init_database()

    # Inicializa banco de dados e rotas
    register_routes(app)
    register_error_handlers(app)
    register_middleware(app)

    logger.info("Aplicação Flask criada com sucesso")
    return app


def init_database():
    """
    Inicializa o banco de dados SQLite, criando tabelas se necessário.
    """
    db_path = Config.get_db_path()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
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

        # Tabela de computadores
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS computers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                computer_name TEXT UNIQUE NOT NULL,
                ip_address TEXT,
                mac_address TEXT,
                department TEXT NOT NULL,
                user_name TEXT,
                status TEXT DEFAULT 'offline',
                client_version TEXT,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Tabela de mensagens
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                image_path TEXT,
                sender_id INTEGER,
                recipients TEXT, -- JSON array
                urgent BOOLEAN DEFAULT 0,
                confirmation_required BOOLEAN DEFAULT 0,
                sound_enabled BOOLEAN DEFAULT 1,
                status TEXT DEFAULT 'sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (id)
            )
        """
        )

        # Tabela de agendamentos
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scheduled_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                content TEXT NOT NULL,
                image_path TEXT,
                recipients TEXT, -- JSON array
                schedule_time TEXT NOT NULL,
                frequency TEXT, -- 'once', 'daily', 'weekdays', 'weekends'
                is_active BOOLEAN DEFAULT 1,
                sender_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_executed TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users (id)
            )
        """
        )

        # Tabela de logs de entrega
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS delivery_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER,
                computer_id INTEGER,
                status TEXT, -- 'delivered', 'failed', 'read'
                delivered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages (id),
                FOREIGN KEY (computer_id) REFERENCES computers (id)
            )
        """
        )

        # Tabela de status de leitura das mensagens (message_read_status)
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

        conn.commit()
        conn.close()
        logger.info(f"Banco de dados inicializado com sucesso em {db_path}")
    except Exception as e:
        logger.error(f"Erro ao inicializar banco de dados: {e}")


def register_routes(app):
    """
    Registra todas as rotas e blueprints da aplicação Flask.
    """

    @app.route("/")
    def index():
        """Página principal"""
        return render_template("index_improved.html")

    @app.route("/api/health")
    def health_check():
        """
        Health check para monitoramento externo.
        """
        return jsonify(
            {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "version": "2.2.0",
                "ldap_available": False,  # Ajuste para True se desejar testar AD
            }
        )

    # === ROTAS DE AUTENTICAÇÃO ===

    # Importa e registra blueprints de autenticação e mensagens
    from src.routes.auth_improved import auth_bp as auth_improved_bp, require_auth

    app.register_blueprint(auth_improved_bp)
    from src.routes.messages_improved import messages_bp as messages_improved_bp

    app.register_blueprint(messages_improved_bp)

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        """Redireciona para a rota melhorada"""
        from src.routes.auth_improved import login as improved_login

        return improved_login()

    @app.route("/api/auth/logout", methods=["POST"])
    def logout():
        """Redireciona para a rota melhorada"""
        from src.routes.auth_improved import logout as improved_logout

        return improved_logout()

    # === ROTAS DE COMPUTADORES ===

    @app.route("/api/computers", methods=["GET"])
    def get_computers():
        """
        Lista todos os computadores cadastrados no banco local.
        """
        try:
            conn = sqlite3.connect(Config.get_db_path())
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, computer_name, ip_address, mac_address, department, 
                       user_name, status, client_version, last_seen, created_at
                FROM computers
                ORDER BY computer_name
            """
            )

            computers = []
            for row in cursor.fetchall():
                computers.append(
                    {
                        "id": row[0],
                        "computer_name": row[1],
                        "ip_address": row[2],
                        "mac_address": row[3],
                        "department": row[4],
                        "user_name": row[5],
                        "status": row[6],
                        "client_version": row[7],
                        "last_seen": row[8],
                        "created_at": row[9],
                    }
                )

            conn.close()

            return jsonify(
                {"success": True, "computers": computers, "total": len(computers)}
            )

        except Exception as e:
            logger.error(f"Erro ao buscar computadores: {e}")
            return (
                jsonify({"success": False, "message": "Erro ao buscar computadores"}),
                500,
            )

    @app.route("/api/computers/register", methods=["POST"])
    def register_computer():
        """
        Registra ou atualiza um computador no banco de dados.
        """
        try:
            data = request.get_json()

            computer_name = data.get("computer_name")
            ip_address = data.get("ip_address")
            mac_address = data.get("mac_address")
            department = data.get("department", "TI")
            user_name = data.get("user_name")
            client_version = data.get("client_version", "2.1.0")

            if not computer_name:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Nome do computador é obrigatório",
                        }
                    ),
                    400,
                )

            conn = sqlite3.connect(Config.get_db_path())
            cursor = conn.cursor()

            # Verifica se já existe
            cursor.execute(
                "SELECT id FROM computers WHERE computer_name = ?", (computer_name,)
            )
            existing = cursor.fetchone()

            if existing:
                # Atualiza dados existentes
                cursor.execute(
                    """
                    UPDATE computers 
                    SET ip_address = ?, mac_address = ?, department = ?, 
                        user_name = ?, status = 'online', client_version = ?,
                        last_seen = CURRENT_TIMESTAMP
                    WHERE computer_name = ?
                """,
                    (
                        ip_address,
                        mac_address,
                        department,
                        user_name,
                        client_version,
                        computer_name,
                    ),
                )

                computer_id = existing[0]
            else:
                # Insere novo
                cursor.execute(
                    """
                    INSERT INTO computers (computer_name, ip_address, mac_address, 
                                         department, user_name, status, client_version)
                    VALUES (?, ?, ?, ?, ?, 'online', ?)
                """,
                    (
                        computer_name,
                        ip_address,
                        mac_address,
                        department,
                        user_name,
                        client_version,
                    ),
                )

                computer_id = cursor.lastrowid

            conn.commit()

            # Busca dados completos
            cursor.execute("SELECT * FROM computers WHERE id = ?", (computer_id,))
            computer_data = cursor.fetchone()

            computer = {
                "id": computer_data[0],
                "computer_name": computer_data[1],
                "ip_address": computer_data[2],
                "mac_address": computer_data[3],
                "department": computer_data[4],
                "user_name": computer_data[5],
                "status": computer_data[6],
                "client_version": computer_data[7],
                "last_seen": computer_data[8],
                "created_at": computer_data[9],
            }

            conn.close()

            logger.info(f"Computador registrado: {computer_name}")
            return jsonify(
                {
                    "success": True,
                    "computer": computer,
                    "message": "Computador registrado com sucesso",
                }
            )

        except Exception as e:
            logger.error(f"Erro ao registrar computador: {e}")
            return (
                jsonify({"success": False, "message": "Erro ao registrar computador"}),
                500,
            )

    @app.route("/api/computers/heartbeat", methods=["POST"])
    def computer_heartbeat():
        """
        Recebe heartbeat de computador e atualiza status.
        """
        try:
            data = request.get_json()
            computer_name = data.get("computer_name")

            if not computer_name:
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": "Nome do computador é obrigatório",
                        }
                    ),
                    400,
                )

            conn = sqlite3.connect(Config.get_db_path())
            cursor = conn.cursor()

            # Atualiza último heartbeat
            cursor.execute(
                """
                UPDATE computers 
                SET status = 'online', last_seen = CURRENT_TIMESTAMP,
                    ip_address = ?, user_name = ?
                WHERE computer_name = ?
            """,
                (data.get("ip_address"), data.get("user_name"), computer_name),
            )

            # Busca ID do computador
            cursor.execute(
                "SELECT id FROM computers WHERE computer_name = ?", (computer_name,)
            )
            result = cursor.fetchone()
            computer_id = result[0] if result else None

            conn.commit()
            conn.close()

            return jsonify(
                {
                    "success": True,
                    "computer_id": computer_id,
                    "message": "Heartbeat recebido",
                }
            )

        except Exception as e:
            logger.error(f"Erro no heartbeat: {e}")
            return jsonify({"success": False, "message": "Erro no heartbeat"}), 500

    # === ROTAS DE MENSAGENS ===

    

    @app.route("/api/messages/for-computer/<computer_name>")
    def get_messages_for_computer_redirect(computer_name):
        """
        Redireciona para a rota melhorada
        """
        from src.routes.messages_improved import get_unread_messages_for_computer

        return get_unread_messages_for_computer(computer_name)

    @app.route("/api/messages/history")
    def get_message_history():
        """
        Busca histórico de mensagens
        """
        try:
            conn = sqlite3.connect(Config.get_db_path())
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT m.id, m.title, m.content, m.recipients, m.urgent,
                       m.created_at, u.name as sender_name, m.status
                FROM messages m
                LEFT JOIN users u ON m.sender_id = u.id
                ORDER BY m.created_at DESC
                LIMIT 100
            """
            )

            messages = []
            for row in cursor.fetchall():
                recipients = json.loads(row[3]) if row[3] else []
                message = {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "recipients": recipients,
                    "urgent": bool(row[4]),
                    "timestamp": format_datetime_to_brasilia(row[5]),
                    "sender_name": row[6],
                    "status": row[7],
                }
                messages.append(message)

            conn.close()

            return jsonify({"success": True, "messages": messages})

        except Exception as e:
            logger.error(f"Erro ao buscar histórico: {e}")
            return (
                jsonify({"success": False, "message": "Erro ao buscar histórico"}),
                500,
            )

    # === ROTAS DE AGENDAMENTOS ===

    @app.route("/api/schedules")
    def get_schedules():
        """
        Lista agendamentos
        """
        try:
            conn = sqlite3.connect(Config.get_db_path())
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT id, title, content, recipients, schedule_time, 
                       frequency, is_active, created_at, last_executed
                FROM scheduled_messages
                ORDER BY created_at DESC
            """
            )

            schedules = []
            for row in cursor.fetchall():
                schedule = {
                    "id": row[0],
                    "title": row[1],
                    "content": row[2],
                    "recipients": json.loads(row[3]) if row[3] else [],
                    "schedule_time": row[4],
                    "frequency": row[5],
                    "active": bool(row[6]),
                    "created_at": format_datetime_to_brasilia(row[7]),
                    "last_executed": format_datetime_to_brasilia(row[8]),
                }
                schedules.append(schedule)

            conn.close()

            return jsonify({"success": True, "schedules": schedules})

        except Exception as e:
            logger.error(f"Erro ao buscar agendamentos: {e}")
            return (
                jsonify({"success": False, "message": "Erro ao buscar agendamentos"}),
                500,
            )

    # === ROTAS DE ARQUIVOS ===

    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        """
        Serve arquivos de upload
        """
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def allowed_file(filename):
    """
    Verifica se o arquivo possui extensão permitida para upload.
    Protege contra uploads de arquivos potencialmente perigosos.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    allowed = getattr(Config, "ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "gif"})
    return ext in allowed


def register_error_handlers(app):
    """
    Registra handlers globais para erros HTTP e exceções.
    """

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return (
                jsonify({"success": False, "message": "Endpoint não encontrado"}),
                404,
            )
        return render_template("index_improved.html")

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Erro interno: {error}")
        if request.path.startswith("/api/"):
            return (
                jsonify({"success": False, "message": "Erro interno do servidor"}),
                500,
            )
        return render_template("index_improved.html")

    @app.errorhandler(RequestEntityTooLarge)
    def file_too_large(error):
        return (
            jsonify(
                {"success": False, "message": "Arquivo muito grande. Máximo 16MB."}
            ),
            413,
        )


def register_middleware(app):
    """
    Registra middlewares para logging de requisições e headers de segurança.
    """

    @app.before_request
    def log_request():
        if request.path.startswith("/api/"):
            logger.info(f"{request.method} {request.path} - {request.remote_addr}")

    @app.after_request
    def after_request(response):
        # Headers de segurança
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # CORS headers
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"

        return response


def main():
    """
    Função principal para inicializar o servidor Flask.
    """
    app = create_app()

    # Configurações de execução
    host = "0.0.0.0"  # Permite acesso externo
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    logger.info(f"Iniciando servidor em http://{host}:{port}")
    logger.info(f"Modo debug: {debug}")

    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        logger.info("Servidor interrompido pelo usuário")
    except Exception as e:
        logger.error(f"Erro ao iniciar servidor: {e}")


if __name__ == "__main__":
    main()
