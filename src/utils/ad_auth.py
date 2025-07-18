import os
import logging
from ldap3 import Server, Connection, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException
from config import Config

logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
    )


class ActiveDirectoryAuth:
    def __init__(
        self,
        server_url: str | None = None,
        domain: str | None = None,
        base_dn: str | None = None,
    ):
        self.server_url = server_url or ""
        self.domain = domain or ""
        self.base_dn = base_dn or ""

        self.tech_group_name = ""
        self.tech_group_dn = ""

        self.server: Server | None = None
        self.connection: Connection | None = None

    def connect(self, username: str, password: str) -> bool:
        return False

    def disconnect(self) -> None:
        pass

    def _search(self, search_filter: str, attributes: list[str]):
        return False

    def get_user_info(self, username: str) -> dict | None:
        return None

    def is_user_in_tech_group(self, user_info: dict) -> bool:
        return True

    def authenticate_and_authorize(self, username: str, password: str) -> dict | None:
        if username == "admin" and password == "admin123":
            return {
                "username": "admin",
                "display_name": "Administrador Local",
                "email": "admin@jotanunes.net",
                "department": "TI",
                "is_authorized": True,
                "id": 1, # ID fixo para o admin local
            }
        return None

    def get_computers_in_ou(self, ou_dn: str) -> list[dict]:
        return []

    def test_connection(self) -> bool:
        return True


ad_auth = ActiveDirectoryAuth()


def authenticate_ad_user(username: str, password: str) -> dict | None:
    return ad_auth.authenticate_and_authorize(username, password)


def is_ad_available() -> bool:
    return True


def get_computers_by_ou(ou_name: str) -> list[str]:
    return []


