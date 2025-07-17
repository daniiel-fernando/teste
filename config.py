"""
Configurações do Sistema de Notificações Corporativas
"""

import os
from datetime import timedelta


class Config:
    """Configurações base"""

    # Chave secreta para sessões Flask
    SECRET_KEY = os.environ.get("SECRET_KEY") or "m3#A7x@qP9!zT$wK2vFdLu&nBjXyR5Qe"

    # Banco de dados
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL") or "sqlite:///notifications.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Active Directory
    AD_SERVER_URL = os.environ.get("AD_SERVER_URL") or "192.168.79.201"
    AD_DOMAIN = os.environ.get("AD_DOMAIN") or "jotanunes.net"
    AD_BASE_DN = os.environ.get("AD_BASE_DN") or "DC=jotanunes,DC=net"
    AD_OU_TI = "OU=TI,OU=MATRIZ,OU=@Computadores,OU=SERGIPE.SEDE,OU=JOTANUNES.NET,DC=jotanunes,DC=net"
    AD_OU_OPERACIONAL = "OU=OPERACIONAL,OU=MATRIZ,OU=@Computadores,OU=SERGIPE.SEDE,OU=JOTANUNES.NET,DC=jotanunes,DC=net"
    AD_OU_GESTORES = "OU=GESTORES,OU=MATRIZ,OU=@Computadores,OU=SERGIPE.SEDE,OU=JOTANUNES.NET,DC=jotanunes,DC=net"
    AD_OU_DIRETORIA = "OU=DIRETORIA,OU=MATRIZ,OU=@Computadores,OU=SERGIPE.SEDE,OU=JOTANUNES.NET,DC=jotanunes,DC=net"
    AD_TECH_GROUP = os.environ.get("AD_TECH_GROUP") or "GG_TECNOLOGIA"
    AD_BIND_USER = os.environ.get("AD_BIND_USER") or "jotanunes\daniel.fernando"
    AD_BIND_PASSWORD = os.environ.get("AD_BIND_PASSWORD") or "1112dlF@"

    # Sessão
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "jotanunes_notifications:"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)

    # Uploads
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or "uploads"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # Agendamento
    SCHEDULER_TIMEZONE = os.environ.get("SCHEDULER_TIMEZONE") or "America/Sao_Paulo"

    # Log
    LOG_LEVEL = os.environ.get("LOG_LEVEL") or "INFO"
    LOG_FILE = os.environ.get("LOG_FILE") or "notifications.log"

    # Email (futuro uso)
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 587)
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")

    # Segurança (CORS)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*").split(",")

    @staticmethod
    def get_db_path():
        """Retorna o caminho absoluto do banco de dados SQLite"""
        db_uri = Config.SQLALCHEMY_DATABASE_URI
        if db_uri.startswith("sqlite:///"):
            rel_path = db_uri.replace("sqlite:///", "")
            return os.path.abspath(os.path.join(os.path.dirname(__file__), rel_path))
        return db_uri  # Para outros bancos, retorna a URI

    @staticmethod
    def init_app(app):
        """Inicializa configurações específicas da aplicação"""
        pass


class ProductionConfig(Config):
    """Configurações para produção"""

    DEBUG = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    CORS_ORIGINS = ["https://notifications.jotanunes.net"]

    @staticmethod
    def init_app(app):
        Config.init_app(app)
        import logging
        from logging.handlers import SysLogHandler

        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


# Mapeamento de configurações
config = {
    "production": ProductionConfig,
    "default": ProductionConfig,
}


def get_config():
    """Retorna a configuração baseada na variável de ambiente"""
    return config[os.environ.get("FLASK_ENV", "default")]
