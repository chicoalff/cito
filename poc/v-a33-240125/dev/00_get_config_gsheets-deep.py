from __future__ import annotations

from pathlib import Path
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# CONFIGURAÇÕES
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1XvNJWRsAyoasc6IE9v6-uG_o8vi_7OkS2hvWaL281MA/edit?usp=sharing"
WORKSHEET_NAME = "config"
SERVICE_ACCOUNT_FILE = Path("poc/v.a33-240125/config/service_account.json")
OUTPUT_COLUMNS = ["id_config", "status", "config_name", "description", "value"]
STATUS_ALIASES = ["status", "stauts"]

def log(level: str, message: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")

def main() -> None:
    log("INFO", "Iniciando script de leitura de configurações")

    if not SERVICE_ACCOUNT_FILE.exists():
        log("ERROR", f"Arquivo não encontrado: {SERVICE_ACCOUNT_FILE.resolve()}")
        raise FileNotFoundError("Credenciais não localizadas")

    log("INFO", "Autenticando com Google Sheets API")
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    creds = Credentials.from_service_account_file(str(SERVICE_ACCOUNT_FILE), scopes=scopes)
    gc = gspread.authorize(creds)

    log("INFO", "Abrindo planilha")
    sh = gc.open_by_url(SPREADSHEET_URL)
    ws = sh.worksheet(WORKSHEET_NAME)

    log("INFO", "Lendo registros da planilha")
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    log("INFO", f"Total de registros lidos: {len(df)}")

    if df.empty:
        log("WARN", "Nenhum registro encontrado")
        return

    df.columns = [str(c).strip() for c in df.columns]
    status_col = next((c for c in STATUS_ALIASES if c in df.columns), None)
    
    if not status_col:
        log("ERROR", f"Nenhuma coluna de status encontrada")
        raise ValueError("Coluna de status inexistente")

    if status_col != "status":
        df = df.rename(columns={status_col: "status"})

    missing = [c for c in OUTPUT_COLUMNS if c not in df.columns]
    if missing:
        log("ERROR", f"Colunas ausentes: {missing}")
        raise ValueError("Estrutura incompatível")

    log("INFO", "Aplicando filtro: status = 'active' ou 'inactive'")
    df["status"] = df["status"].astype(str).str.strip()
    filtered_df = df[df["status"].str.lower().isin(["active", "inactive"])].copy()

    log("INFO", f"Registros filtrados: {len(filtered_df)}")

    if filtered_df.empty:
        log("WARN", "Nenhuma configuração encontrada")
        return

    print("\nCONFIGURAÇÕES FILTRADAS\n")
    print(filtered_df[["id_config", "config_name", "value"]].to_string(index=False))
    print()

    log("INFO", "Execução finalizada")

if __name__ == "__main__":
    main()