from __future__ import annotations

from pathlib import Path
import sys
import re
from typing import Any, Dict

# Garante acesso ao a_get_configs.py (pasta com hífen)
THIS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(THIS_DIR))

from a_get_configs import get_config_data, get_config_dict  # noqa: E402


def _sanitize_var_name(name: str) -> str:
    """
    Converte config_name em um nome de variável Python válido.
    Ex:
        "api-url"   -> API_URL
        "db.host"   -> DB_HOST
        "timeout"   -> TIMEOUT
    """
    name = name.strip()
    name = re.sub(r"[^\w]+", "_", name)
    if name and name[0].isdigit():
        name = f"CFG_{name}"
    return name.upper()


def load_configs_as_variables(
    *,
    service_account_file: Path,
    filter_statuses={"active"},
    target_globals: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """
    Carrega configs da planilha e cria variáveis globais dinamicamente.

    Returns:
        dict normalizado {VAR_NAME: value}
    """
    if target_globals is None:
        target_globals = globals()

    df = get_config_data(
        service_account_file=service_account_file,
        filter_statuses=filter_statuses,
    )

    if df is None or df.empty:
        raise RuntimeError("Nenhuma configuração carregada")

    config_dict = get_config_dict(df)

    exported: Dict[str, Any] = {}

    for raw_name, value in config_dict.items():
        var_name = _sanitize_var_name(raw_name)
        target_globals[var_name] = value
        exported[var_name] = value

    return exported


def main() -> None:
    service_account_file = THIS_DIR / "config" / "service_account.json"

    configs = load_configs_as_variables(
        service_account_file=service_account_file,
        filter_statuses={"active"},
    )

    print("\n= VARIÁVEIS CRIADAS =")
    for k, v in configs.items():
        print(f"{k} = {v!r}")


if __name__ == "__main__":
    main()
