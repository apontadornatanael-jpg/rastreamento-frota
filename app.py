import streamlit as st
import pandas as pd
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
    salvar_localizacao_gps,
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

    st.subheader("📊 Visão geral da frota")

    veiculos = listar_veiculos()

    total = len(veiculos)

    localizados = sum(
        1 for veiculo in veiculos
        if ultima_localizacao(veiculo[0])
    )

    col1, col2, col3 = st.columns(3)

    col1.metric("🚗 Total de veículos", total)
    col2.metric("📍 Com localização", localizados)
    col3.metric("📡 Sem localização", total - localizados)

    if veiculos:

        mapa = folium.Map(
            location=[-15.7801, -47.9292],
            zoom_start=4
        )

        encontrou_localizacao = False

        for veiculo in veiculos:

            localizacao = ultima_localizacao(veiculo[0])

            if localizacao:

                encontrou_localizacao = True

                latitude, longitude, velocidade, bateria, data_hora = localizacao

                bateria_texto = (
                    f"{bateria}%" if bateria is not None else "Não informada"
                )

                popup = f"""
                <b>{veiculo[1]}</b><br>
                Placa: {veiculo[2]}<br>
                Velocidade: {velocidade} km/h<br>
                Bateria: {bateria_texto}<br>
                Atualização: {data_hora}
                """

                folium.Marker(
                    location=[latitude, longitude],
                    popup=popup,
                    tooltip=veiculo[1]
                ).add_to(mapa)

        if encontrou_localizacao:

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
# LOCALIZAÇÃO
# =========================================================

elif pagina == "📍 Atualizar Localização":

    st.subheader("📍 Localização automática do aparelho")
    st.caption(
        "O sistema solicita a localização GPS do celular/tablet. "
        "Permita o acesso à localização quando o navegador solicitar."
    )

    veiculos = listar_veiculos()

    if not veiculos:
        st.warning("Cadastre um veículo primeiro.")
    else:
        opcoes = {f"{v[1]} - {v[2]}": v[0] for v in veiculos}

        veiculo_nome = st.selectbox(
            "Selecione o veículo",
            list(opcoes.keys())
        )
        veiculo_id = opcoes[veiculo_nome]

        if streamlit_geolocation is None:
            st.error(
                "O componente de GPS não está instalado. "
                "Adicione streamlit-geolocation ao requirements.txt e faça novo deploy."
            )
        else:
            st.markdown("### 📡 GPS do dispositivo")
            localizacao = streamlit_geolocation(
                key="gps_rastreamento_frota"
            )

            if isinstance(localizacao, dict) and localizacao.get("error"):
                erro = localizacao.get("error") or {}
                mensagem = (
                    erro.get("message", "Não foi possível obter a localização.")
                    if isinstance(erro, dict)
                    else str(erro)
                )
                st.warning(f"⚠️ GPS: {mensagem}")

            elif isinstance(localizacao, dict):
                lat = localizacao.get("latitude")
                lon = localizacao.get("longitude")
                accuracy = localizacao.get("accuracy")

                if lat is not None and lon is not None:
                    lat = float(lat)
                    lon = float(lon)
                    accuracy = float(accuracy) if accuracy is not None else None

                    st.success("📍 Localização GPS capturada automaticamente!")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("Latitude", f"{lat:.7f}")
                    c2.metric("Longitude", f"{lon:.7f}")
                    c3.metric(
                        "Precisão",
                        f"±{accuracy:.1f} m" if accuracy is not None else "Não informada"
                    )

                    if accuracy is not None and accuracy > 50:
                        st.warning(
                            f"⚠️ A precisão atual é de aproximadamente ±{accuracy:.1f} m. "
                            "Se possível, fique alguns segundos parado e tente novamente."
                        )

                    velocidade = st.number_input(
                        "Velocidade (km/h)",
                        min_value=0.0,
                        value=0.0,
                        step=1.0
                    )

                    bateria = st.number_input(
                        "Bateria (%) — opcional",
                        min_value=0.0,
                        max_value=100.0,
                        value=100.0,
                        step=1.0
                    )

                    if st.button("📍 Salvar minha localização", type="primary"):
                        try:
                            salvar_localizacao_gps(
                                veiculo_id,
                                lat,
                                lon,
                                velocidade,
                                bateria
                            )
                            st.session_state["ultima_posicao_salva"] = (
                                veiculo_id, lat, lon
                            )
                            st.success(
                                f"✅ Localização do veículo {veiculo_nome} salva no Supabase!"
                            )
                            st.rerun()
                        except Exception as erro:
                            st.error(f"Erro ao salvar localização: {erro}")

                    maps_url = f"https://www.google.com/maps?q={lat:.7f},{lon:.7f}"
                    st.link_button("🌎 Conferir posição no Google Maps", maps_url)
                else:
                    st.info(
                        "Aguardando o GPS do aparelho. Verifique se a localização está ativada."
                    )
            else:
                st.info(
                    "Aguardando a localização do aparelho. Permita o acesso ao GPS no navegador."
                )

