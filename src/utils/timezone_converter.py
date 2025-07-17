from datetime import datetime
import pytz

def convert_to_brasilia_time(utc_dt: datetime) -> datetime:
    """Converte um objeto datetime UTC para o fuso horário de Brasília."""
    if utc_dt.tzinfo is None: # Assume UTC se não houver timezone info
        utc_dt = utc_dt.replace(tzinfo=pytz.utc)
    brasilia_tz = pytz.timezone("America/Sao_Paulo")
    return utc_dt.astimezone(brasilia_tz)

def format_datetime_to_brasilia(utc_dt_str: str) -> str:
    """Converte uma string de datetime UTC para o fuso horário de Brasília e formata."""
    if not utc_dt_str: return ""
    try:
        # Suporta formatos com e sem milissegundos
        if "." in utc_dt_str:
            utc_dt = datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S.%f")
        else:
            utc_dt = datetime.strptime(utc_dt_str, "%Y-%m-%d %H:%M:%S")
        brasilia_dt = convert_to_brasilia_time(utc_dt)
        return brasilia_dt.strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return utc_dt_str # Retorna original se falhar a conversão

