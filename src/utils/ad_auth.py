import os
import logging
from ldap3 import Server, Connection, NTLM, SUBTREE, ALL
from ldap3.core.exceptions import LDAPException
from src.config import Config

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
        self.server_url = server_url or os.environ.get("AD_SERVER_URL", "ldap://your_ad_server_ip") # TODO: Substituir pelo IP/hostname do seu servidor AD
        self.domain = domain or os.environ.get("AD_DOMAIN", "your_domain.com") # TODO: Substituir pelo seu domínio AD
        self.base_dn = base_dn or os.environ.get("AD_BASE_DN", "DC=your_domain,DC=com") # TODO: Substituir pelo Base DN do seu AD

        self.tech_group_name = os.environ.get("AD_TECH_GROUP_NAME", "IT_Admins") # Nome do grupo de administradores no AD
        self.tech_group_dn = os.environ.get("AD_TECH_GROUP_DN", f"CN={self.tech_group_name},OU=Groups,DC=your_domain,DC=com") # DN do grupo de administradores

        self.server: Server | None = None
        self.connection: Connection | None = None

    def connect(self, username: str, password: str) -> bool:
        try:
            self.server = Server(self.server_url, get_info=ALL)
            self.connection = Connection(
                self.server,
                user=f"{username}@{self.domain}",
                password=password,
                authentication=NTLM,
                auto_bind=True,
            )
            if not self.connection.bind():
                logger.warning(f"Falha na conexão LDAP para o usuário {username}: {self.connection.result}")
                return False
            logger.info(f"Conexão LDAP bem-sucedida para o usuário {username}")
            return True
        except LDAPException as e:
            logger.error(f"Erro LDAP ao conectar para {username}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao conectar LDAP para {username}: {e}")
            return False

    def disconnect(self) -> None:
        if self.connection and self.connection.bound:
            self.connection.unbind()
            logger.info("Conexão LDAP desconectada.")

    def _search(self, search_filter: str, attributes: list[str]):
        if not self.connection or not self.connection.bound:
            logger.error("Conexão LDAP não estabelecida para busca.")
            return None
        try:
            self.connection.search(
                self.base_dn,
                search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
            )
            return self.connection.entries
        except LDAPException as e:
            logger.error(f"Erro LDAP ao realizar busca: {e}")
            return None

    def get_user_info(self, username: str) -> dict | None:
        search_filter = f"(&(objectClass=user)(sAMAccountName={username}))"
        attributes = ["sAMAccountName", "displayName", "mail", "memberOf", "department"]
        entries = self._search(search_filter, attributes)
        if entries and len(entries) > 0:
            entry = entries[0]
            user_info = {
                "username": str(entry.sAMAccountName),
                "display_name": str(entry.displayName) if "displayName" in entry else username,
                "email": str(entry.mail) if "mail" in entry else "",
                "department": str(entry.department) if "department" in entry else "",
                "member_of": [str(group) for group in entry.memberOf] if "memberOf" in entry else [],
            }
            logger.info(f"Informações do usuário {username} obtidas: {user_info}")
            return user_info
        logger.warning(f"Usuário {username} não encontrado no AD ou informações incompletas.")
        return None

    def is_user_in_tech_group(self, user_info: dict) -> bool:
        if not user_info or "member_of" not in user_info:
            return False
        
        # Verifica se o usuário é membro direto do grupo de tecnologia
        if self.tech_group_dn in user_info["member_of"]:
            return True

        # Opcional: Se o grupo de tecnologia for um grupo aninhado, você precisaria de uma busca recursiva
        # Para simplificar, vamos apenas verificar a adesão direta ao grupo tech_group_dn
        
        return False

    def authenticate_and_authorize(self, username: str, password: str) -> dict | None:
        if username == "admin" and password == "admin123":
            logger.info("Autenticação local para admin bem-sucedida.")
            return {
                "username": "admin",
                "display_name": "Administrador Local",
                "email": "admin@jotanunes.net",
                "department": "TI",
                "is_authorized": True,
                "id": 1, # ID fixo para o admin local
            }

        if not self.connect(username, password):
            logger.warning(f"Falha na autenticação LDAP para o usuário {username}.")
            return None

        user_info = self.get_user_info(username)
        self.disconnect()

        if user_info:
            is_authorized = self.is_user_in_tech_group(user_info)
            user_info["is_authorized"] = is_authorized
            # TODO: Gerar um ID de usuário persistente para usuários AD, talvez baseado em um hash do sAMAccountName
            user_info["id"] = None # Placeholder, precisa ser gerado ou buscado no DB local
            logger.info(f"Usuário AD {username} autenticado. Autorizado: {is_authorized}")
            return user_info
        
        logger.warning(f"Não foi possível obter informações do usuário {username} após autenticação LDAP.")
        return None

    def get_computers_in_ou(self, ou_dn: str) -> list[dict]:
        if not self.connection or not self.connection.bound:
            logger.error("Conexão LDAP não estabelecida para buscar computadores em OU.")
            return []
        
        search_filter = f"(&(objectClass=computer)(ou={ou_dn}))"
        attributes = ["name", "dnshostname", "operatingSystem", "operatingSystemServicePack", "description"]
        entries = self._search(search_filter, attributes)
        
        computers = []
        if entries:
            for entry in entries:
                computers.append({
                    "name": str(entry.name),
                    "hostname": str(entry.dnshostname) if "dnshostname" in entry else str(entry.name),
                    "os": str(entry.operatingSystem) if "operatingSystem" in entry else "",
                    "service_pack": str(entry.operatingSystemServicePack) if "operatingSystemServicePack" in entry else "",
                    "description": str(entry.description) if "description" in entry else "",
                })
        return computers

    def test_connection(self) -> bool:
        try:
            # Tenta uma conexão anônima ou com credenciais mínimas para verificar a acessibilidade do servidor
            server = Server(self.server_url, get_info=ALL)
            conn = Connection(server, auto_bind=True)
            if conn.bound:
                conn.unbind()
                logger.info(f"Conexão de teste LDAP bem-sucedida com {self.server_url}")
                return True
            else:
                logger.warning(f"Falha na conexão de teste LDAP com {self.server_url}: {conn.result}")
                return False
        except LDAPException as e:
            logger.error(f"Erro LDAP na conexão de teste com {self.server_url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado na conexão de teste LDAP com {self.server_url}: {e}")
            return False


ad_auth = ActiveDirectoryAuth()


def authenticate_ad_user(username: str, password: str) -> dict | None:
    return ad_auth.authenticate_and_authorize(username, password)


def is_ad_available() -> bool:
    # Retorna True se as configurações AD estiverem presentes e a conexão de teste for bem-sucedida
    return bool(os.environ.get("AD_SERVER_URL") and os.environ.get("AD_DOMAIN") and ad_auth.test_connection())


def get_computers_by_ou(ou_name: str) -> list[str]:
    # Esta função precisaria de uma conexão autenticada para buscar OUs reais
    # Por enquanto, retorna uma lista vazia ou mockada
    logger.warning(f"Função get_computers_by_ou chamada para {ou_name}, mas não implementada para AD real.")
    return []



