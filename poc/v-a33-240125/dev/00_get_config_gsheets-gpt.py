from __future__ import annotations

from pathlib import Path
from datetime import datetime

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1XvNJWRsAyoasc6IE9v6-uG_o8vi_7OkS2hvWaL281MA/edit?usp=sharing"
)
WORKSHEET_NAME = "config"
SERVICE_ACCOUNT_FILE = Path("poc/v.a33-240125/config/service_account.json")

STATUS_ALIASES = ["status", "stauts"]
FILTER_STATUSES = {"active", "inactive"}
PRINT_COLUMNS = ["id_config", "config_name", "value"]


def log(level: str, message: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {message}")


def main() -> None:
    log("INFO", "Iniciando")
    if not SERVICE_ACCOUNT_FILE.exists():
        log("ERROR", f"Credenciais não encontradas: {SERVICE_ACCOUNT_FILE.resolve()}")
        raise FileNotFoundError("Arquivo de credenciais não localizado")

    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(str(SERVICE_ACCOUNT_FILE), scopes=scopes)
    gc = gspread.authorize(creds)
    log("INFO", "Autenticado")

    sh = gc.open_by_url(SPREADSHEET_URL)
    ws = sh.worksheet(WORKSHEET_NAME)
    log("INFO", f"Abrindo aba: {WORKSHEET_NAME}")

    df = pd.DataFrame(ws.get_all_records())
    log("INFO", f"Registros lidos: {len(df)}")
    if df.empty:
        log("WARN", "Sem dados")
        return

    df.columns = [str(c).strip() for c in df.columns]
    log("INFO", f"Colunas: {list(df.columns)}")

    status_col = next((c for c in STATUS_ALIASES if c in df.columns), None)
    if not status_col:
        log("ERROR", f"Coluna de status ausente (esperado: {STATUS_ALIASES})")
        raise ValueError("Coluna de status inexistente")

    if status_col != "status":
        df = df.rename(columns={status_col: "status"})
        log("WARN", f"Renomeado '{status_col}' -> 'status'")

    required = set(PRINT_COLUMNS) | {"status"}
    missing = [c for c in required if c not in df.columns]
    if missing:
        log("ERROR", f"Colunas obrigatórias ausentes: {missing}")
        raise ValueError("Estrutura da planilha incompatível")

    df["status"] = df["status"].astype(str).str.strip().str.lower()
    out = df[df["status"].isin(FILTER_STATUSES)][PRINT_COLUMNS].copy()

    log("INFO", f"Linhas com status em {sorted(FILTER_STATUSES)}: {len(out)}")
    if out.empty:
        log("WARN", "Nenhuma linha encontrada para os status filtrados")
        return

    print("\n= Dados (active/inactive) =")
    print(out.to_string(index=False))
    print("= Fim =\n")

    log("INFO", "Finalizado")


if __name__ == "__main__":
    main()
