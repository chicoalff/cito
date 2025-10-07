import sqlite3
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("poc/v01-a33/data")

DB_FILE = "cito.db"
TABLE_NAME = "stf_index"
JSON_FILE_PATH = Path("poc/v01-a33/data/json/jurisprudencia.json")

def create_database():
    """
    Cria o banco de dados SQLite e a tabela stf_index, se não existirem.
    A tabela é criada com uma restrição UNIQUE em 'id_decisao_stf' para evitar duplicatas.
    """
    print(f"1/3 | Configuração | Iniciado | Criando banco de dados '{DB_FILE}' e tabela '{TABLE_NAME}'...")
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # A coluna 'id_decisao_stf' será a chave para evitar duplicatas
        cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id_unico INTEGER,
            id_decisao_stf TEXT PRIMARY KEY,
            decisao TEXT,
            url TEXT,
            orgao_colegiado TEXT,
            relator TEXT,
            julgamento TEXT,
            publicacao TEXT
        )
        """)
        
        conn.commit()
        print(f"1/3 | Configuração | Concluído | Banco de dados e tabela prontos.")
    except sqlite3.Error as e:
        print(f"1/3 | Configuração | Erro | Erro ao criar banco de dados: {e}")
    finally:
        if conn:
            conn.close()

def insert_data_from_json():
    """
    Lê os dados do arquivo jurisprudencia.json e os insere no banco de dados SQLite.
    Utiliza 'INSERT OR IGNORE' para não inserir registros duplicados.
    """
    # 2. Ler o arquivo JSON
    print(f"2/3 | Leitura     | Iniciado | Lendo dados de '{JSON_FILE_PATH}'...")
    try:
        with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
            data_to_insert = json.load(f)
        print(f"2/3 | Leitura     | Concluído | {len(data_to_insert)} registros lidos do JSON.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"2/3 | Leitura     | Erro      | Falha ao ler o arquivo JSON: {e}")
        return

    if not data_to_insert:
        print("JSON vazio. Nenhuma inserção necessária.")
        return

    # 3. Inserir no banco de dados
    print(f"3/3 | Gravação    | Iniciado | Inserindo dados na tabela '{TABLE_NAME}'...")
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        for item in data_to_insert:
            cursor.execute(f"""
            INSERT OR IGNORE INTO {TABLE_NAME} (id_unico, id_decisao_stf, decisao, url, orgao_colegiado, relator, julgamento, publicacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, tuple(item.values()))

        conn.commit()
        print(f"3/3 | Gravação    | Concluído | {cursor.rowcount} novos registros inseridos. Total na tabela: {cursor.lastrowid}")
    except sqlite3.Error as e:
        print(f"3/3 | Gravação    | Erro      | Erro ao inserir dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
    insert_data_from_json()
    print("\nProcesso finalizado.")

