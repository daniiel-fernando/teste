import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "m3#A7x@qP9!zT$wK2vFdLu&nBjXyR5Qe")
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "notifications.db")
    JWT_ACCESS_TOKEN_EXPIRES_HOURS = int(
        os.environ.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 2)
    )
    JWT_REFRESH_TOKEN_EXPIRES_DAYS = int(
        os.environ.get("JWT_REFRESH_TOKEN_EXPIRES_DAYS", 7)
    )
    NOTIFICATION_CHECK_INTERVAL_MS = int(
        os.environ.get("NOTIFICATION_CHECK_INTERVAL_MS", 30000)
    )
    HEARTBEAT_INTERVAL_MS = int(os.environ.get("HEARTBEAT_INTERVAL_MS", 60000))
    MESSAGE_CLEANUP_DAYS = int(os.environ.get("MESSAGE_CLEANUP_DAYS", 7))
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    AD_BIND_USER = os.environ.get(
        "AD_BIND_USER", "CN=binduser,CN=Users,DC=jotanunes,DC=net"
    )  # Usuário com permissão de leitura no AD
    AD_BIND_PASSWORD = os.environ.get(
        "AD_BIND_PASSWORD", "SuaSenhaSeguraAqui"
    )  # Senha do usuário de bind

    @staticmethod
    def get_db_path():
        """Retorna o caminho absoluto do banco de dados SQLite"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.abspath(os.path.join(base_dir, Config.DATABASE_PATH))


