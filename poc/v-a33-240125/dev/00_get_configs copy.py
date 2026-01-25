# arquivo: poc/v-a33-240125/00_get_configs.py

from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Iterable, Set

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1XvNJWRsAyoasc6IE9v6-uG_o8vi_7OkS2hvWaL281MA/edit?usp=sharing"
)
WORKSHEET_NAME = "config"
SERVICE_ACCOUNT_FILE = Path("poc/v-a33-240125/config/service_account.json")

STATUS_ALIASES = ["status", "stauts"]
FILTER_STATUSES = {"active", "inactive"}

# Ordem solicitada (colunas de exibição)
PRINT_COLUMNS = ["id", "status", "config_name", "value"]


def log(level: str, message: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {message}")


def get_config_data(
    spreadsheet_url: str = SPREADSHEET_URL,
    worksheet_name: str = WORKSHEET_NAME,
    service_account_file: Path = SERVICE_ACCOUNT_FILE,
    filter_statuses: Iterable[str] = FILTER_STATUSES,
    required_columns: Optional[List[str]] = None,
) -> Optional[pd.DataFrame]:
    """
    Obtém dados de configuração do Google Sheets, normaliza 'status', filtra por status,
    reordena as colunas e ordena linhas por: id, status, config_name, value.

    Returns:
        DataFrame com dados filtrados (ordenado e com colunas reordenadas) ou None em caso de erro/sem dados.
    """
    if required_columns is None:
        # mantém as colunas que você já estava usando como "obrigatórias"
        required_columns = ["id", "status", "config_name", "value", "description"]

    try:
        if not service_account_file.exists():
            log("ERROR", f"Credenciais não encontradas: {service_account_file.resolve()}")
            return None

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file(str(service_account_file), scopes=scopes)
        gc = gspread.authorize(creds)

        sh = gc.open_by_url(spreadsheet_url)
        ws = sh.worksheet(worksheet_name)

        df = pd.DataFrame(ws.get_all_records())
        if df.empty:
            log("WARN", "Sem dados na planilha")
            return None

        # Normaliza cabeçalhos
        df.columns = [str(c).strip() for c in df.columns]

        # Resolve alias da coluna status
        status_col = next((c for c in STATUS_ALIASES if c in df.columns), None)
        if not status_col:
            log("ERROR", f"Coluna de status não encontrada (esperado: {STATUS_ALIASES})")
            return None

        if status_col != "status":
            df = df.rename(columns={status_col: "status"})
            log("INFO", f"Coluna '{status_col}' renomeada para 'status'")

        # Valida colunas obrigatórias
        missing = [c for c in required_columns if c not in df.columns]
        if missing:
            log("ERROR", f"Colunas ausentes: {missing}")
            return None

        # Normaliza status e filtro
        df["status"] = df["status"].astype(str).str.strip().str.lower()
        filter_statuses_norm: Set[str] = {str(s).strip().lower() for s in filter_statuses}

        # Reordena colunas: id, status, config_name, value (restante mantém depois)
        preferred_order = ["id", "status", "config_name", "value"]
        ordered_columns = [c for c in preferred_order if c in required_columns] + [
            c for c in required_columns if c not in preferred_order
        ]

        # Filtra + ordena linhas
        filtered_df = (
            df[df["status"].isin(filter_statuses_norm)][ordered_columns]
            .copy()
            .sort_values(by=["id", "status", "config_name", "value"], kind="stable")
            .reset_index(drop=True)
        )

        log("INFO", f"Dados obtidos: {len(filtered_df)} linhas filtradas")
        return filtered_df

    except Exception as e:
        log("ERROR", f"Erro ao obter dados: {e}")
        return None


def get_config_dict(df: Optional[pd.DataFrame]) -> Dict[str, Any]:
    """
    Converte DataFrame de configurações para dicionário: {config_name: value}.
    """
    if df is None or df.empty:
        return {}
    return df.set_index("config_name")["value"].to_dict()


def main() -> None:
    log("INFO", "Iniciando obtenção de configurações")

    config_df = get_config_data()
    if config_df is None or config_df.empty:
        log("WARN", "Nenhum dado obtido da planilha")
        return

    print("\n= CONFIGURAÇÕES (active/inactive) =")
    display_cols = [c for c in PRINT_COLUMNS if c in config_df.columns]
    print(config_df[display_cols].to_string(index=False))
    print("= FIM =\n")

    config_dict = get_config_dict(config_df)
    log("INFO", f"Configurações convertidas para dicionário: {len(config_dict)} itens")
    log("INFO", "Finalizado")


if __name__ == "__main__":
    main()
