import streamlit as st
import pandas as pd
import time
import folium
from streamlit_folium import st_folium

try:
    from streamlit_geolocation import streamlit_geolocation
except ImportError:
    streamlit_geolocation = None

from database import (
    criar_tabelas,
    cadastrar_veiculo,
    listar_veiculos,
    salvar_localizacao,
    ultima_localizacao
)


st.set_page_config(
    page_title="Rastreamento de Frota",
    page_icon="🚛",
    layout="wide"
)


criar_tabelas()


st.title("🚛 Rastreamento de Frotas")


pagina = st.sidebar.radio(
    "Menu",
    [
        "📊 Dashboard",
        "🚗 Veículos",
        "📍 Atualizar Localização"
    ]
)


# =========================================================
# DASHBOARD
# =========================================================

if pagina == "📊 Dashboard":

    st.subheader("📊 Acompanhamento da Frota")

    veiculos = listar_veiculos()
    total = len(veiculos)

    dados_frota = []
    for veiculo in veiculos:
        loc = ultima_localizacao(veiculo[0])
        dados_frota.append((veiculo, loc))

    localizados = sum(1 for _, loc in dados_frota if loc)

    from datetime import datetime, timezone

    def esta_online(data_hora):
        if not data_hora:
            return False
        try:
            dt = datetime.fromisoformat(str(data_hora).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            agora = datetime.now(timezone.utc)
            return (agora - dt).total_seconds() <= 120
        except Exception:
            return False

    online = sum(
        1 for _, loc in dados_frota
        if loc and esta_online(loc[4])
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🚗 Veículos", total)
    col2.metric("🟢 Online", online)
    col3.metric("📍 Localizados", localizados)
    col4.metric("🔴 Sem sinal", total - online)

    if veiculos:

        st.markdown("### 🚛 Velocidade dos veículos")

        velocidades = [
            {
                "Veículo": veiculo[1],
                "Placa": veiculo[2],
                "Velocidade": float(loc[2] or 0),
                "Atualização": loc[4]
            }
            for veiculo, loc in dados_frota
            if loc
        ]

        if velocidades:
            cols = st.columns(min(4, len(velocidades)))

            for i, item in enumerate(velocidades):
                with cols[i % len(cols)]:
                    status = (
                        "🟢"
                        if esta_online(item["Atualização"])
                        else "🔴"
                    )
                    st.metric(
                        f"{status} {item['Veículo']}",
                        f"{item['Velocidade']:.1f} km/h",
                        item["Placa"]
                    )

        st.markdown("### 🗺️ Localização da frota")

        mapa = folium.Map(
            location=[-15.7801, -47.9292],
            zoom_start=5
        )

        encontrou_localizacao = False
        coordenadas = []

        for veiculo, localizacao in dados_frota:

            if localizacao:
                encontrou_localizacao = True

                latitude, longitude, velocidade, bateria, data_hora = localizacao

                latitude = float(latitude)
                longitude = float(longitude)
                velocidade = float(velocidade or 0)

                coordenadas.append([latitude, longitude])

                online_veiculo = esta_online(data_hora)
                status_texto = (
                    "🟢 ONLINE"
                    if online_veiculo
                    else "🔴 SEM SINAL"
                )

                bateria_texto = (
                    f"{bateria}%"
                    if bateria is not None
                    else "Não informada"
                )

                popup = (
                    f"<b>🚛 {veiculo[1]}</b><br>"
                    f"Placa: {veiculo[2]}<br>"
                    f"Status: <b>{status_texto}</b><br>"
                    f"🚗 Velocidade: <b>{velocidade:.1f} km/h</b><br>"
                    f"🔋 Bateria: {bateria_texto}<br>"
                    f"🕐 Atualização: {data_hora}"
                )

                folium.CircleMarker(
                    location=[latitude, longitude],
                    radius=10,
                    popup=folium.Popup(popup, max_width=300),
                    tooltip=f"{veiculo[1]} — {velocidade:.1f} km/h",
                    fill=True
                ).add_to(mapa)

                etiqueta = (
                    '<div style="'
                    'background:white;'
                    'border:2px solid #333;'
                    'border-radius:8px;'
                    'padding:3px 6px;'
                    'font-size:12px;'
                    'font-weight:bold;'
                    'white-space:nowrap;'
                    'box-shadow:0 1px 4px rgba(0,0,0,.35);'
                    '">'
                    f'🚛 {velocidade:.1f} km/h'
                    '</div>'
                )

                folium.Marker(
                    location=[latitude, longitude],
                    icon=folium.DivIcon(html=etiqueta)
                ).add_to(mapa)

        if encontrou_localizacao:

            if len(coordenadas) == 1:
                mapa.location = coordenadas[0]
                mapa.options["zoom"] = 14
            else:
                mapa.fit_bounds(coordenadas)

            st_folium(
                mapa,
                width=None,
                height=600,
                key="mapa_frota"
            )

        else:
            st.info("Nenhuma localização registrada ainda.")

    else:
        st.info("Nenhum veículo cadastrado ainda.")


# =========================================================
# VEÍCULOS
# =========================================================

elif pagina == "🚗 Veículos":

    st.subheader("🚗 Cadastro de veículos")

    with st.form("cadastro_veiculo"):

        nome = st.text_input("Nome do veículo")

        placa = st.text_input("Placa")

        tipo = st.selectbox(
            "Tipo",
            [
                "Caminhão",
                "Pickup",
                "Carro",
                "Máquina",
                "Sonda",
                "Outro"
            ]
        )

        responsavel = st.text_input("Motorista / Responsável")

        salvar = st.form_submit_button(
            "💾 Cadastrar veículo"
        )

        if salvar:

            if nome and placa:

                try:

                    cadastrar_veiculo(
                        nome,
                        placa,
                        tipo,
                        responsavel
                    )

                    st.success(
                        "Veículo cadastrado com sucesso!"
                    )

                except Exception as erro:

                    st.error(
                        f"Erro ao cadastrar: {erro}"
                    )

            else:

                st.warning(
                    "Preencha pelo menos nome e placa."
                )


    st.divider()

    st.subheader("Veículos cadastrados")

    veiculos = listar_veiculos()

    if veiculos:

        df = pd.DataFrame(
            veiculos,
            columns=[
                "ID",
                "Nome",
                "Placa",
                "Tipo",
                "Responsável",
                "Status"
            ]
        )

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Nenhum veículo cadastrado."
        )


# =========================================================
# RASTREAMENTO AUTOMÁTICO
# =========================================================

elif pagina == "📍 Atualizar Localização":

    st.subheader("📡 Rastreamento")

    veiculos = listar_veiculos()

    if not veiculos:
        st.warning("Cadastre um veículo primeiro.")
    else:
        # Mantém a seleção do veículo apenas na primeira utilização.
        opcoes = {f"{v[1]} - {v[2]}": v[0] for v in veiculos}

        if "veiculo_rastreamento_id" not in st.session_state:
            st.session_state["veiculo_rastreamento_id"] = veiculos[0][0]

        nomes_ids = list(opcoes.items())
        nome_atual = next(
            (
                nome
                for nome, vid in nomes_ids
                if vid == st.session_state["veiculo_rastreamento_id"]
            ),
            nomes_ids[0][0]
        )

        veiculo_nome = st.selectbox(
            "Veículo",
            list(opcoes.keys()),
            index=list(opcoes.keys()).index(nome_atual)
        )
        veiculo_id = opcoes[veiculo_nome]
        st.session_state["veiculo_rastreamento_id"] = veiculo_id

        # Um único botão para iniciar/parar.
        rastreando = st.session_state.get("rastreando", False)

        if not rastreando:
            st.markdown("### 🚛 Pronto para rastrear")
            st.caption(
                "Toque no botão abaixo e permita o acesso à localização "
                "quando o navegador solicitar."
            )

            if st.button(
                "📍 ATIVAR RASTREAMENTO",
                type="primary",
                use_container_width=True
            ):
                st.session_state["rastreando"] = True
                st.session_state["ultima_posicao_rastreamento"] = None
                st.rerun()

        else:
            st.success(f"🟢 Rastreamento ativo — {veiculo_nome}")

            if st.button(
                "⏹️ PARAR RASTREAMENTO",
                use_container_width=True
            ):
                st.session_state["rastreando"] = False
                st.rerun()

            if streamlit_geolocation is None:
                st.error(
                    "O componente de GPS não está instalado. "
                    "Adicione streamlit-geolocation ao requirements.txt."
                )
            else:
                localizacao = streamlit_geolocation()

                if isinstance(localizacao, dict) and localizacao.get("error"):
                    erro = localizacao.get("error") or {}
                    mensagem = (
                        erro.get(
                            "message",
                            "Não foi possível obter a localização."
                        )
                        if isinstance(erro, dict)
                        else str(erro)
                    )
                    st.warning(f"⚠️ GPS: {mensagem}")

                elif isinstance(localizacao, dict):
                    lat = localizacao.get("latitude")
                    lon = localizacao.get("longitude")
                    accuracy = localizacao.get("accuracy")

                    # O navegador/GPS pode fornecer a velocidade em m/s.
                    velocidade_ms = localizacao.get("speed")

                    if lat is not None and lon is not None:
                        lat = float(lat)
                        lon = float(lon)
                        accuracy = (
                            float(accuracy)
                            if accuracy is not None
                            else None
                        )

                        if velocidade_ms is not None:
                            try:
                                velocidade = max(
                                    0.0,
                                    float(velocidade_ms) * 3.6
                                )
                            except (TypeError, ValueError):
                                velocidade = 0.0
                        else:
                            velocidade = 0.0

                        c1, c2 = st.columns(2)
                        c1.metric("🚗 Velocidade", f"{velocidade:.1f} km/h")
                        c2.metric(
                            "🎯 Precisão",
                            (
                                f"±{accuracy:.1f} m"
                                if accuracy is not None
                                else "Não informada"
                            )
                        )

                        st.caption(
                            f"📍 {lat:.6f}, {lon:.6f}"
                        )

                        # Só envia novamente se a posição mudou.
                        posicao_atual = (
                            veiculo_id,
                            round(lat, 6),
                            round(lon, 6)
                        )

                        ultima_enviada = st.session_state.get(
                            "ultima_posicao_rastreamento"
                        )

                        if posicao_atual != ultima_enviada:
                            try:
                                salvar_localizacao(
                                    veiculo_id,
                                    lat,
                                    lon,
                                    velocidade,
                                    None
                                )

                                st.session_state[
                                    "ultima_posicao_rastreamento"
                                ] = posicao_atual

                                st.session_state[
                                    "ultima_atualizacao_rastreamento"
                                ] = time.strftime(
                                    "%d/%m/%Y %H:%M:%S"
                                )

                                st.toast(
                                    "📡 Localização atualizada!",
                                    icon="📍"
                                )

                            except Exception as erro:
                                st.error(
                                    f"Erro ao enviar localização: {erro}"
                                )

                        ultima_atualizacao = st.session_state.get(
                            "ultima_atualizacao_rastreamento"
                        )

                        if ultima_atualizacao:
                            st.caption(
                                f"Último envio: {ultima_atualizacao}"
                            )

                        if accuracy is not None and accuracy > 50:
                            st.warning(
                                f"⚠️ Precisão do GPS: aproximadamente "
                                f"±{accuracy:.1f} m."
                            )

                        # Atualização automática.
                        time.sleep(15)
                        st.rerun()

                    else:
                        st.info(
                            "📡 Aguardando sinal do GPS..."
                        )

                else:
                    st.info(
                        "📡 Aguardando sinal do GPS..."
                    )
