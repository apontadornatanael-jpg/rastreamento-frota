import streamlit as st
import pandas as pd
import folium

from streamlit_folium import st_folium

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

                popup = f"""
                <b>{veiculo[1]}</b><br>
                Placa: {veiculo[2]}<br>
                Velocidade: {velocidade} km/h<br>
                Bateria: {bateria}%<br>
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
                height=600
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

    st.subheader(
        "📍 Atualização de localização"
    )

    veiculos = listar_veiculos()

    if not veiculos:

        st.warning(
            "Cadastre um veículo primeiro."
        )

    else:

        opcoes = {
            f"{v[1]} - {v[2]}": v[0]
            for v in veiculos
        }

        veiculo_nome = st.selectbox(
            "Selecione o veículo",
            list(opcoes.keys())
        )

        veiculo_id = opcoes[
            veiculo_nome
        ]


        with st.form(
            "atualizar_localizacao"
        ):

            latitude = st.number_input(
                "Latitude",
                value=-15.7801,
                format="%.6f"
            )

            longitude = st.number_input(
                "Longitude",
                value=-47.9292,
                format="%.6f"
            )

            velocidade = st.number_input(
                "Velocidade (km/h)",
                min_value=0.0,
                value=0.0
            )

            bateria = st.number_input(
                "Bateria (%)",
                min_value=0.0,
                max_value=100.0,
                value=100.0
            )

            atualizar = st.form_submit_button(
                "📍 Salvar localização"
            )

            if atualizar:

                salvar_localizacao(
                    veiculo_id,
                    latitude,
                    longitude,
                    velocidade,
                    bateria
                )

                st.success(
                    "Localização atualizada!"
                )
