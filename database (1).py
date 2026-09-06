
import sqlite3
from datetime import datetime

DB_NAME = "frota.db"


def conectar():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def criar_tabelas():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            placa TEXT UNIQUE,
            tipo TEXT,
            responsavel TEXT,
            status TEXT DEFAULT 'Ativo'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS localizacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            velocidade REAL DEFAULT 0,
            bateria REAL DEFAULT 100,
            data_hora TEXT NOT NULL,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos(id)
        )
    """)

    conn.commit()
    conn.close()


def cadastrar_veiculo(nome, placa, tipo, responsavel):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO veiculos
        (nome, placa, tipo, responsavel)
        VALUES (?, ?, ?, ?)
    """, (nome, placa.upper().strip(), tipo, responsavel))

    conn.commit()
    conn.close()


def listar_veiculos():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nome, placa, tipo, responsavel, status
        FROM veiculos
        ORDER BY nome
    """)

    dados = cursor.fetchall()

    conn.close()

    return dados


def salvar_localizacao(
    veiculo_id,
    latitude,
    longitude,
    velocidade=0,
    bateria=100
):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO localizacoes
        (
            veiculo_id,
            latitude,
            longitude,
            velocidade,
            bateria,
            data_hora
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        veiculo_id,
        latitude,
        longitude,
        velocidade,
        bateria,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def ultima_localizacao(veiculo_id):

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            latitude,
            longitude,
            velocidade,
            bateria,
            data_hora
        FROM localizacoes
        WHERE veiculo_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (veiculo_id,))

    dado = cursor.fetchone()

    conn.close()

    return dado
