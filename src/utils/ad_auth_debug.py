"""
Utilitário para autenticação e validação de grupos no Active Directory - Versão Debug
"""

import os
import logging
from ldap3 import Server, Connection, NTLM, SUBTREE, ALL
from ldap3.core.exceptions import LDAPException

from config import Config  # importa configs globais

# Configuração de logging mais detalhada
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(message)s", level=logging.DEBUG
)


class ActiveDirectoryAuthDebug:
    """
    Cliente de autenticação/consulta ao Active Directory com debug detalhado.
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
        
        logging.info(f"Inicializando ActiveDirectoryAuthDebug:")
        logging.info(f"  - Server URL: {self.server_url}")
        logging.info(f"  - Domain: {self.domain}")
        logging.info(f"  - Base DN: {self.base_dn}")
        logging.info(f"  - Tech Group: {self.tech_group_name}")

    # ------------------------------------------------------------------ #
    # Conexão                                                             #
    # ------------------------------------------------------------------ #
    def connect(self, username: str, password: str) -> bool:
        """
        Faz bind NTLM no AD com debug detalhado.

        Retorna True se o bind foi bem‑sucedido.
        """
        try:
            logging.info(f"Tentando conectar com usuário: {username}")
            
            # garante formato DOMÍNIO\usuario
            original_username = username
            if "@" not in username and "\\" not in username:
                username = f"{self.domain.split('.')[0].upper()}\\{username}"
            
            logging.info(f"Formato do usuário ajustado: {original_username} -> {username}")

            # Cria servidor com informações detalhadas
            logging.info(f"Criando conexão com servidor: {self.server_url}:389")
            self.server = Server(
                self.server_url,
                port=389,
                connect_timeout=10,  # Aumentando timeout
                get_info=ALL,  # Obtém informações do servidor para debug
            )
            
            logging.info(f"Informações do servidor LDAP: {self.server.info}")
            
            logging.info(f"Tentando bind NTLM com usuário: {username}")
            self.connection = Connection(
                self.server,
                user=username,
                password=password,
                authentication=NTLM,
                auto_bind=True,
                raise_exceptions=True  # Para capturar exceções mais específicas
            )
            
            logging.info(f"Bind AD bem‑sucedido como {username}")
            logging.info(f"Status da conexão: {self.connection.bound}")
            logging.info(f"Informações da conexão: {self.connection}")
            return True

        except LDAPException as e:
            logging.error(f"LDAPException detalhada: {type(e).__name__}: {e}")
            logging.error(f"Detalhes do erro: {e.args}")
            return False
        except Exception as e:
            logging.error(f"Erro inesperado no bind AD: {type(e).__name__}: {e}")
            logging.error(f"Detalhes do erro: {e.args}")
            return False

    def disconnect(self) -> None:
        """Fecha a conexão LDAP."""
        if self.connection:
            logging.info("Fechando conexão LDAP")
            self.connection.unbind()
        self.connection = None
        self.server = None

    # ------------------------------------------------------------------ #
    # Operações de usuário                                               #
    # ------------------------------------------------------------------ #
    def _search(self, search_filter: str, attributes: list[str]):
        """Helper para buscas LDAP com debug."""
        if not self.connection:
            logging.error("Tentativa de busca sem conexão ativa")
            return False
            
        logging.info(f"Executando busca LDAP:")
        logging.info(f"  - Base DN: {self.base_dn}")
        logging.info(f"  - Filtro: {search_filter}")
        logging.info(f"  - Atributos: {attributes}")
        
        result = self.connection.search(
            search_base=self.base_dn,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=attributes,
        )
        
        logging.info(f"Resultado da busca: {result}")
        if result:
            logging.info(f"Número de entradas encontradas: {len(self.connection.entries)}")
            for i, entry in enumerate(self.connection.entries):
                logging.info(f"Entrada {i}: {entry.entry_dn}")
        
        return result

    def get_user_info(self, username: str) -> dict | None:
        """Coleta atributos do usuário no AD com debug."""
        try:
            clean_username = username.split("\\")[-1].split("@")[0]
            logging.info(f"Buscando informações do usuário: {clean_username}")
            
            filt = f"(&(objectClass=user)(sAMAccountName={clean_username}))"

            if not self._search(
                filt,
                ["sAMAccountName", "displayName", "mail", "department", "memberOf"],
            ):
                logging.error("Busca do usuário falhou")
                return None

            if not self.connection.entries:
                logging.error("Nenhuma entrada encontrada para o usuário")
                return None

            entry = self.connection.entries[0]
            logging.info(f"Entrada do usuário encontrada: {entry.entry_dn}")
            
            user_info = {
                "username": str(entry.sAMAccountName),
                "display_name": str(entry.displayName or entry.sAMAccountName),
                "email": str(entry.mail) if entry.mail else None,
                "department": str(entry.department) if entry.department else "TI",
                "groups": [str(g) for g in entry.memberOf] if entry.memberOf else [],
            }
            
            logging.info(f"Informações do usuário coletadas:")
            logging.info(f"  - Username: {user_info['username']}")
            logging.info(f"  - Display Name: {user_info['display_name']}")
            logging.info(f"  - Email: {user_info['email']}")
            logging.info(f"  - Department: {user_info['department']}")
            logging.info(f"  - Grupos ({len(user_info['groups'])}): {user_info['groups']}")
            
            return user_info

        except Exception as e:
            logging.error(f"Erro get_user_info: {type(e).__name__}: {e}")
            return None

    def is_user_in_tech_group(self, user_info: dict) -> bool:
        """Confere se usuário pertence ao grupo GG_TECNOLOGIA ou depto TI com debug."""
        logging.info(f"Verificando se usuário pertence ao grupo de tecnologia")
        
        group_candidates = [g.upper() for g in user_info.get("groups", [])]
        patterns = [
            self.tech_group_name.upper(),
            f"CN={self.tech_group_name}".upper(),
            "TECNOLOGIA",
            "TI",
        ]
        
        logging.info(f"Padrões de grupo procurados: {patterns}")
        logging.info(f"Grupos do usuário (maiúsculo): {group_candidates}")
        
        # Verifica grupos
        for pattern in patterns:
            for group in group_candidates:
                if pattern in group:
                    logging.info(f"Usuário encontrado no grupo: {group} (padrão: {pattern})")
                    return True
        
        # Verifica departamento
        dept = user_info.get("department", "").upper()
        logging.info(f"Departamento do usuário: {dept}")
        
        if dept in ["TI", "TECNOLOGIA", "TECHNOLOGY"]:
            logging.info(f"Usuário autorizado pelo departamento: {dept}")
            return True

        logging.warning(f"Usuário {user_info.get('username')} não encontrado no grupo {self.tech_group_name} nem em departamento de TI")
        return False

    # ------------------------------------------------------------------ #
    # Pipeline completo                                                  #
    # ------------------------------------------------------------------ #
    def authenticate_and_authorize(self, username: str, password: str) -> dict | None:
        """Bind + busca + verificação de grupo com debug detalhado."""
        try:
            logging.info(f"=== Iniciando autenticação completa para {username} ===")
            
            if not self.connect(username, password):
                logging.error("Falha na conexão LDAP")
                return None

            user_info = self.get_user_info(username)
            if not user_info:
                logging.error("Falha ao obter informações do usuário")
                return None

            if not self.is_user_in_tech_group(user_info):
                logging.warning(f"{username} não autorizado - fora do grupo {self.tech_group_name}")
                return None

            user_info["is_admin"] = True
            user_info["is_authorized"] = True
            
            logging.info(f"=== Autenticação bem-sucedida para {username} ===")
            return user_info

        except Exception as e:
            logging.error(f"Erro authenticate_and_authorize: {type(e).__name__}: {e}")
            return None
        finally:
            self.disconnect()

    # ------------------------------------------------------------------ #
    # Diagnóstico                                                        #
    # ------------------------------------------------------------------ #
    def test_connection(self) -> bool:
        """Realiza bind com credenciais de teste com debug."""
        test_user = Config.AD_TEST_USER
        test_pass = Config.AD_TEST_PASS
        
        logging.info(f"=== Testando conexão com credenciais de teste ===")
        logging.info(f"Usuário de teste: {test_user}")
        
        if not (test_user and test_pass):
            logging.warning("AD_TEST_USER/AD_TEST_PASS não configurados")
            return False

        ok = self.connect(test_user, test_pass)
        self.disconnect()
        
        logging.info(f"Resultado do teste de conexão: {ok}")
        return ok


# ---------------------------------------------------------------------- #
# Helpers de alto nível                                                 #
# ---------------------------------------------------------------------- #
ad_auth_debug = ActiveDirectoryAuthDebug()


def authenticate_ad_user_debug(username: str, password: str) -> dict | None:
    """Interface externa para autenticação/autorizar AD com debug."""
    return ad_auth_debug.authenticate_and_authorize(username, password)


def is_ad_available_debug() -> bool:
    """Checa disponibilidade do AD com as credenciais de teste com debug."""
    return ad_auth_debug.test_connection()

