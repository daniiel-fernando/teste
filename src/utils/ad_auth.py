"""
Utilitário para autenticação e consulta ao Active Directory (AD).
Inclui funções para autenticação, consulta de grupos e busca de computadores em OUs.
"""

import os
import logging
from ldap3 import Server, Connection, NTLM, SUBTREE
from ldap3.core.exceptions import LDAPException
from config import Config  # importa configs globais

# Configuração de logging local (evita sobrescrever global)
logger = logging.getLogger(__name__)
if not logger.hasHandlers():
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s", level=logging.INFO
    )


class ActiveDirectoryAuth:
    """
    Cliente de autenticação/consulta ao Active Directory.
    Fornece métodos para autenticação, busca de usuários e computadores.
    """

    def __init__(
        self,
        server_url: str | None = None,
        domain: str | None = None,
        base_dn: str | None = None,
    ):
        self.server_url = server_url or Config.AD_SERVER_URL  # ex: 192.168.79.201
        self.domain = domain or Config.AD_DOMAIN  # ex: jotanunes.net
        self.base_dn = base_dn or Config.AD_BASE_DN  # ex: DC=jotanunes,DC=net

        # Grupo obrigatório para acesso
        self.tech_group_name = Config.AD_TECH_GROUP  # GG_TECNOLOGIA
        self.tech_group_dn = f"CN={self.tech_group_name},CN=Users,{self.base_dn}"

        self.server: Server | None = None
        self.connection: Connection | None = None

    # ------------------------------------------------------------------ #
    # Conexão                                                             #
    # ------------------------------------------------------------------ #
    def connect(self, username: str, password: str) -> bool:
        """
        Realiza bind NTLM no AD.
        Retorna True se o bind foi bem‑sucedido.
        Nunca loga a senha!
        """
        try:
            # garante formato DOMÍNIO\usuario
            if "@" not in username and "\\" not in username:
                username = f"{self.domain.split('.')[0].upper()}\\{username}"

            # Não precisa de 'ldap://' no endereço
            self.server = Server(
                self.server_url,
                port=389,
                connect_timeout=5,
                get_info=None,  # não baixa o schema
            )
            self.connection = Connection(
                self.server,
                user=username,
                password=password,
                authentication=NTLM,
                auto_bind=True,
            )
            logger.info(f"Bind AD bem‑sucedido como {username}")
            return True

        except LDAPException as e:
            logger.error(f"LDAPException: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado no bind AD: {e}")
            return False

    def disconnect(self) -> None:
        """Fecha a conexão LDAP."""
        if self.connection:
            self.connection.unbind()
        self.connection = None
        self.server = None

    # ------------------------------------------------------------------ #
    # Operações de usuário                                               #
    # ------------------------------------------------------------------ #
    def _search(self, search_filter: str, attributes: list[str]):
        """
        Helper para buscas LDAP.
        """
        if not self.connection:
            return False
        return self.connection.search(
            search_base=self.base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attributes,
        )

    def get_user_info(self, username: str) -> dict | None:
        """
        Coleta atributos do usuário no AD.
        Nunca loga senha ou dados sensíveis.
        """
        try:
            clean_username = username.split("\\")[-1].split("@")[-1]
            filt = f"(&(objectClass=user)(sAMAccountName={clean_username}))"

            if not self._search(
                filt,
                ["sAMAccountName", "displayName", "mail", "department", "memberOf"],
            ):
                return None

            entry = self.connection.entries[0]
            return {
                "username": str(entry.sAMAccountName),
                "display_name": str(entry.displayName or entry.sAMAccountName),
                "email": str(entry.mail) if entry.mail else None,
                "department": str(entry.department) if entry.department else "TI",
                "groups": [str(g) for g in entry.memberOf] if entry.memberOf else [],
            }

        except Exception as e:
            logger.error(f"Erro get_user_info: {e}")
            return None

    def is_user_in_tech_group(self, user_info: dict) -> bool:
        """Confere se usuário pertence ao grupo GG_TECNOLOGIA ou depto TI."""
        group_candidates = [g.upper() for g in user_info.get("groups", [])]
        patterns = [
            self.tech_group_name.upper(),
            f"CN={self.tech_group_name}".upper(),
            "TECNOLOGIA",
            "TI",
        ]
        if any(p in g for p in patterns for g in group_candidates):
            return True

        return user_info.get("department", "").upper() in [
            "TI",
            "TECNOLOGIA",
            "TECHNOLOGY",
        ]

    # ------------------------------------------------------------------ #
    # Pipeline completo                                                  #
    # ------------------------------------------------------------------ #
    def authenticate_and_authorize(self, username: str, password: str) -> dict | None:
        """Bind + busca + verificação de grupo."""
        try:
            if not self.connect(username, password):
                return None

            user_info = self.get_user_info(username)
            if not user_info:
                return None

            # Removida a verificação obrigatória de grupo
            # Qualquer usuário autenticado no LDAP pode acessar
            logging.info(f"Usuário {username} autenticado com sucesso no LDAP")

            # Define permissões baseadas no grupo (opcional)
            user_info["is_admin"] = self.is_user_in_tech_group(user_info)
            user_info["is_authorized"] = True  # Todos os usuários LDAP são autorizados
            return user_info

        except Exception as e:
            logging.error(f"Erro authenticate_and_authorize: {e}")
            return None
        finally:
            self.disconnect()

    # ------------------------------------------------------------------ #
    # Diagnóstico                                                        #
    # ------------------------------------------------------------------ #
    def get_computers_in_ou(self, ou_dn: str) -> list[dict]:
        """Busca computadores dentro de uma OU específica no AD."""
        computers = []
        try:
            # Conecta usando as credenciais de bind
            if not self.connect(Config.AD_BIND_USER, Config.AD_BIND_PASSWORD):
                logging.error("Falha ao conectar ao AD com credenciais de bind.")
                return []

            # Filtro para objetos de computador dentro da OU especificada
            search_filter = "(objectClass=computer)"

            # Realiza a busca dentro da OU
            if self.connection.search(
                search_base=ou_dn,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=["name", "dn"],
            ):
                for entry in self.connection.entries:
                    if entry.name:
                        computers.append({"name": str(entry.name), "dn": str(entry.dn)})
            logging.info(f"Encontrados {len(computers)} computadores na OU {ou_dn}")
        except LDAPException as e:
            logging.error(f"Erro ao buscar computadores na OU {ou_dn}: {e}")
        except Exception as e:
            logging.error(f"Erro inesperado ao buscar computadores na OU {ou_dn}: {e}")
        finally:
            self.disconnect()  # Garante que a conexão seja fechada
        return computers

    # ---------------------------------------------------------------------- #
    # Helpers de alto nível                                                 #
    # ---------------------------------------------------------------------- #


ad_auth = ActiveDirectoryAuth()


def authenticate_ad_user(username: str, password: str) -> dict | None:
    """Interface externa para autenticação/autorizar AD."""
    return ad_auth.authenticate_and_authorize(username, password)


def is_ad_available() -> bool:
    """Checa disponibilidade do AD com as credenciais de teste."""
    return ad_auth.test_connection()


def get_computers_by_ou(ou_name: str) -> list[str]:
    """Retorna computadores de uma OU específica com base no nome amigável."""
    ou_map = {
        "TI": Config.AD_OU_TI,
        "GESTORES": Config.AD_OU_GESTORES,
        "OPERACIONAL": Config.AD_OU_OPERACIONAL,
        "DIRETORIA": Config.AD_OU_DIRETORIA,
    }
    ou_dn = ou_map.get(ou_name.upper())
    if not ou_dn:
        logging.warning(f"OU desconhecida: {ou_name}")
        return []

    computers = ad_auth.get_computers_in_ou(ou_dn)
    return computers
