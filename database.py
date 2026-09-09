import streamlit as st
from supabase import create_client


def _get_secret(name: str):
    return st.secrets[name]


@st.cache_resource
def get_supabase():
    return create_client(
        _get_secret("SUPABASE_URL"),
        _get_secret("SUPABASE_KEY")
    )


def criar_tabelas():
    """As tabelas são gerenciadas no Supabase."""
    return True


def cadastrar_veiculo(nome, placa, tipo, responsavel):
    supabase = get_supabase()

    dados = {
        "nome": nome.strip(),
        "placa": placa.upper().strip(),
        "tipo": tipo,
        "responsavel": responsavel.strip() if responsavel else None
    }

    return (
        supabase
        .table("veiculos")
        .insert(dados)
        .execute()
    )


def listar_veiculos():
    supabase = get_supabase()

    resposta = (
        supabase
        .table("veiculos")
        .select("id, nome, placa, tipo, responsavel")
        .order("nome")
        .execute()
    )

    dados = resposta.data or []

    return [
        (
            item["id"],
            item.get("nome"),
            item.get("placa"),
            item.get("tipo"),
            item.get("responsavel"),
            item.get("status", "Ativo")
        )
        for item in dados
    ]


def salvar_localizacao(
    veiculo_id,
    latitude,
    longitude,
    velocidade=0,
    bateria=100
):
    supabase = get_supabase()

    dados = {
        "veiculo_id": int(veiculo_id),
        "latitude": float(latitude),
        "longitude": float(longitude),
        "velocidade": float(velocidade or 0),
        "bateria": float(bateria) if bateria is not None else None
    }

    return (
        supabase
        .table("localizacoes")
        .insert(dados)
        .execute()
    )


def salvar_localizacao_gps(veiculo_id, latitude, longitude, velocidade=0, bateria=None):
    """Salva uma posição obtida diretamente pelo GPS do aparelho."""
    return salvar_localizacao(
        veiculo_id=veiculo_id,
        latitude=latitude,
        longitude=longitude,
        velocidade=velocidade,
        bateria=bateria
    )


def ultima_localizacao(veiculo_id):
    supabase = get_supabase()

    resposta = (
        supabase
        .table("localizacoes")
        .select(
            "latitude, longitude, velocidade, bateria, created_at"
        )
        .eq("veiculo_id", int(veiculo_id))
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    dados = resposta.data or []

    if not dados:
        return None

    item = dados[0]

    return (
        item.get("latitude"),
        item.get("longitude"),
        item.get("velocidade", 0),
        item.get("bateria"),
        item.get("created_at")
    )
