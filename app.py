
from __future__ import annotations

import math
import random

import pandas as pd
import pydeck as pdk
import streamlit as st

from src import forca_bruta, par_proximo
from src.dados import carregar, coordenadas
from src.ufs import nome_da_uf
from src.validacao import cronometrar


st.set_page_config(
    page_title="Saúde em Proximidade",
    page_icon="📍",
    layout="wide"
)

LIMITE_FORCA_BRUTA = 3_000




def milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def metros(distancia_km: float) -> str:
    return (
        f"{distancia_km * 1000:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def zoom(distancia_km: float) -> float:
    return max(
        3.0,
        min(
            17.0,
            16 - math.log2(max(distancia_km, 0.01) / 0.1)
        )
    )


@st.cache_data(show_spinner="Carregando a base do CNES...")
def carregar_base():
    return carregar()


@st.cache_data(show_spinner="Procurando o par mais próximo...")
def achar_par(minimo_m: float, uf: str, municipio: str):
    estabelecimentos = carregar_base()

    if uf != "Todos":
        estabelecimentos = [
            e for e in estabelecimentos
            if e.uf == uf
        ]

    if municipio != "Todos":
        estabelecimentos = [
            e for e in estabelecimentos
            if str(e.ibge) == municipio
        ]

    pontos = coordenadas(estabelecimentos)

    if len(pontos) < 2:
        return None, None, 0.0

    segundos, (distancia_km, par) = cronometrar(
        par_proximo.par_mais_proximo,
        pontos,
        minimo_m / 1000
    )

    return distancia_km, par, segundos




def mostrar_mapa(a, b, distancia_km: float):
    pontos = pd.DataFrame([
        {
            "nome": a.nome,
            "lat": a.lat,
            "lon": a.lon,
            "cor": [193, 84, 63, 230]
        },
        {
            "nome": b.nome,
            "lat": b.lat,
            "lon": b.lon,
            "cor": [30, 110, 90, 230]
        }
    ])

    ligacao = pd.DataFrame([
        {
            "lat0": a.lat,
            "lon0": a.lon,
            "lat1": b.lat,
            "lon1": b.lon
        }
    ])

    camadas = [
        pdk.Layer(
            "LineLayer",
            data=ligacao,
            get_source_position="[lon0, lat0]",
            get_target_position="[lon1, lat1]",
            get_color=[20, 25, 23, 200],
            get_width=3
        ),
        pdk.Layer(
            "ScatterplotLayer",
            data=pontos,
            get_position="[lon, lat]",
            get_fill_color="cor",
            get_radius=6,
            radius_min_pixels=7,
            pickable=True
        )
    ]

    st.pydeck_chart(
        pdk.Deck(
            layers=camadas,
            initial_view_state=pdk.ViewState(
                latitude=(a.lat + b.lat) / 2,
                longitude=(a.lon + b.lon) / 2,
                zoom=zoom(distancia_km)
            ),
            tooltip={"text": "{nome}"}
        )
    )


def mostrar_mapa_regiao(estabelecimentos):
    pontos = [
        {
            "nome": e.nome,
            "lat": e.lat,
            "lon": e.lon
        }
        for e in estabelecimentos
        if e.lat is not None and e.lon is not None
        and math.isfinite(e.lat) and math.isfinite(e.lon)
        and -90 <= e.lat <= 90
        and -180 <= e.lon <= 180
    ]

    if not pontos:
        st.info("Não existem coordenadas disponíveis para este filtro.")
        return

    df = pd.DataFrame(pontos)

    camada = pdk.Layer(
        "ScatterplotLayer",
        data=df,
        get_position="[lon, lat]",
        get_fill_color=[30, 110, 90, 180],
        get_radius=1000,
        radius_min_pixels=3,
        radius_max_pixels=10,
        pickable=True
    )

    st.pydeck_chart(
        pdk.Deck(
            layers=[camada],
            initial_view_state=pdk.ViewState(
                latitude=df["lat"].mean(),
                longitude=df["lon"].mean(),
                zoom=5 if len(df) > 100 else 9
            ),
            tooltip={"text": "{nome}"}
        )
    )



def mostrar_estabelecimento(titulo: str, estabelecimento):
    st.markdown(f"**{titulo}**")

    st.write(estabelecimento.nome)

    st.caption(
        f"{estabelecimento.bairro or '(sem bairro)'} · "
        f"{nome_da_uf(estabelecimento.uf)} · "
        f"Município IBGE {estabelecimento.ibge} · "
        f"CNES {estabelecimento.cnes}"
    )



def mostrar_resultado(estabelecimentos, minimo_m, uf, municipio):
    distancia_km, par, segundos = achar_par(
        minimo_m,
        uf,
        municipio
    )

    if par is None:
        st.warning(
            "Não foi possível encontrar um par. "
            "Selecione uma região com pelo menos dois estabelecimentos."
        )
        return

    a = estabelecimentos[par[0]]
    b = estabelecimentos[par[1]]

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Menor distância",
        f"{metros(distancia_km)} m"
    )

    col2.metric(
        "Estabelecimentos",
        milhar(len(estabelecimentos))
    )

    col3.metric(
        "Tempo de execução",
        f"{segundos:.4f} s"
    )

    if minimo_m <= 0:
        st.warning(
            "Sem limiar, podem aparecer distâncias próximas de zero. "
            "Isso acontece porque existem registros com coordenadas "
            "iguais ou preenchidas com uma localização aproximada."
        )

    st.divider()

    st.subheader("Estabelecimentos encontrados")

    col1, col2 = st.columns(2)

    with col1:
        mostrar_estabelecimento("📍 Serviço A", a)

    with col2:
        mostrar_estabelecimento("📍 Serviço B", b)

    st.subheader("Localização do par")

    mostrar_mapa(a, b, distancia_km)




def mostrar_exploracao(estabelecimentos):
    st.subheader("Distribuição dos serviços de saúde")

    st.write(
        "Explore a localização dos estabelecimentos presentes "
        "na região selecionada."
    )

    mostrar_mapa_regiao(estabelecimentos)



def mostrar_como_funciona():
    st.subheader("Como funciona o dividir e conquistar?")

    st.markdown(
        """
        O problema consiste em encontrar os dois pontos cuja
        distância entre si é a menor possível.

        Para resolver esse problema, utilizamos a estratégia
        **dividir e conquistar**, que reduz a quantidade de
        comparações necessárias.
        """
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 1. Dividir")

        st.write(
            """
            Os pontos são organizados pela coordenada X e
            separados em duas metades: esquerda e direita.
            """
        )

    with col2:
        st.markdown("### 2. Conquistar")

        st.write(
            """
            O algoritmo resolve recursivamente o problema
            em cada metade, encontrando o menor par de cada lado.
            """
        )

    st.divider()

    st.markdown("### 3. Combinar")

    st.write(
        """
        Comparamos as menores distâncias encontradas nas duas
        metades.

        Depois, verificamos uma faixa próxima à linha divisória,
        pois pode existir um par ainda mais próximo formado por
        pontos de lados diferentes.
        """
    )

    st.info(
        "O algoritmo consegue resolver o problema em O(n log n), "
        "enquanto a força bruta realiza O(n²) comparações."
    )

    st.divider()

    st.markdown("### Pseudocódigo")

    st.code(
        """
PAR_MAIS_PROXIMO(pontos):

    ordenar pontos pela coordenada X

    se houver poucos pontos:
        retornar força bruta

    dividir pontos em esquerda e direita

    par_esquerda = PAR_MAIS_PROXIMO(esquerda)
    par_direita = PAR_MAIS_PROXIMO(direita)

    menor_distancia = menor(
        distancia(par_esquerda),
        distancia(par_direita)
    )

    verificar pontos próximos à divisão

    retornar o menor par encontrado
        """,
        language="text"
    )

    st.divider()

    st.markdown("### Análise de complexidade")

    col1, col2 = st.columns(2)

    col1.metric(
        "Dividir e conquistar",
        "O(n log n)"
    )

    col2.metric(
        "Força bruta",
        "O(n²)"
    )

    st.markdown(
        """
        **Por que dividir e conquistar é mais eficiente?**

        A força bruta compara cada ponto com todos os outros.
        Já dividir e conquistar reduz o problema em partes menores,
        aproveitando os resultados encontrados em cada etapa.
        """
    )




def mostrar_comparacao_com_forca_bruta(estabelecimentos, minimo_m):
    st.subheader("Laboratório de desempenho")

    st.write(
        """
        Compare o algoritmo dividir e conquistar com a força bruta
        utilizando uma amostra aleatória dos estabelecimentos.
        """
    )

    st.caption(
        f"A força bruta compara todos os pares, O(n²). "
        f"Para evitar uma execução muito demorada, "
        f"o experimento utiliza até {milhar(LIMITE_FORCA_BRUTA)} pontos."
    )

    n = st.slider(
        "Quantidade de pontos",
        min_value=500,
        max_value=LIMITE_FORCA_BRUTA,
        value=2_000,
        step=500
    )

    semente = st.number_input(
        "Semente do sorteio",
        value=0,
        step=1
    )

    if st.button("🚀 Executar comparação"):
        pontos = coordenadas(estabelecimentos)

        recorte = random.Random(
            int(semente)
        ).sample(
            pontos,
            min(n, len(pontos))
        )

        if len(recorte) < 2:
            st.warning("São necessários pelo menos dois pontos.")
            return

        t_dc, (d_dc, _) = cronometrar(
            par_proximo.par_mais_proximo,
            recorte,
            minimo_m / 1000
        )

        t_fb, (d_fb, _) = cronometrar(
            forca_bruta.par_mais_proximo,
            recorte,
            minimo_m / 1000
        )

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Dividir e conquistar",
            f"{t_dc:.4f} s"
        )

        col2.metric(
            "Força bruta",
            f"{t_fb:.4f} s"
        )

        col3.metric(
            "Ganho de velocidade",
            f"{t_fb / t_dc:.2f}x" if t_dc > 0 else "—"
        )

        if math.isclose(
            d_dc,
            d_fb,
            rel_tol=1e-9,
            abs_tol=1e-12
        ):
            st.success(
                f"Os dois algoritmos encontraram a mesma distância: "
                f"{metros(d_dc)} m."
            )
        else:
            st.error(
                f"Resultados diferentes: {metros(d_dc)} m "
                f"contra {metros(d_fb)} m."
            )

        st.divider()

        st.markdown("### Comparação visual")

        grafico = pd.DataFrame({
            "Algoritmo": [
                "Dividir e conquistar",
                "Força bruta"
            ],
            "Tempo (segundos)": [
                t_dc,
                t_fb
            ]
        })

        st.bar_chart(
            grafico,
            x="Algoritmo",
            y="Tempo (segundos)"
        )




def mostrar_analise(estabelecimentos, minimo_m):
    st.subheader("Análise de desempenho")

    st.write(
        """
        Observe como o tempo de execução muda conforme
        a quantidade de pontos aumenta.
        """
    )

    pontos = coordenadas(estabelecimentos)

    if len(pontos) < 2:
        st.warning("Poucos pontos disponíveis para análise.")
        return

    tamanhos = sorted(set(
        min(t, len(pontos))
        for t in [100, 250, 500, 1000, 2000, 3000]
        if min(t, len(pontos)) >= 2
    ))

    if not tamanhos:
        st.warning("Não há pontos suficientes para o experimento.")
        return

    if st.button("📊 Gerar gráfico de escalabilidade"):
        resultados = []

        for tamanho in tamanhos:
            recorte = random.Random(42).sample(
                pontos,
                tamanho
            )

            tempo, _ = cronometrar(
                par_proximo.par_mais_proximo,
                recorte,
                minimo_m / 1000
            )

            resultados.append({
                "Quantidade de pontos": tamanho,
                "Tempo (segundos)": tempo
            })

        df = pd.DataFrame(resultados)

        st.line_chart(
            df,
            x="Quantidade de pontos",
            y="Tempo (segundos)"
        )

        st.dataframe(
            df,
            hide_index=True,
            use_container_width=True
        )

        st.caption(
            "Os tempos são medições reais da execução. "
            "Podem variar conforme o hardware e a carga do sistema."
        )




def main():

    st.title("📍 Saúde em Proximidade")

    st.caption(
        "Explorando a distribuição dos serviços de saúde do Brasil "
        "com algoritmos de proximidade geográfica."
    )

    try:
        estabelecimentos = carregar_base()

    except FileNotFoundError:
        st.error("Base do CNES não encontrada em data/raw/.")

        st.markdown(
            """
            Baixe o arquivo CSV no portal de dados abertos:

            [Unidades Básicas de Saúde - CNES](https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs)

            Salve como:

            `data/raw/Unidades_Basicas_Saude-UBS.csv`
            """
        )

        return


    with st.sidebar:

        st.header("🔎 Explorar dados")

        ufs = sorted({
            e.uf for e in estabelecimentos
            if e.uf
        })

        uf_selecionada = st.selectbox(
            "Estado",
            options=["Todos"] + ufs,
            format_func=lambda uf: (
                "Brasil inteiro"
                if uf == "Todos"
                else nome_da_uf(uf)
            )
        )

        base_estado = [
            e for e in estabelecimentos
            if uf_selecionada == "Todos"
            or e.uf == uf_selecionada
        ]

        municipios = sorted({
            str(e.ibge)
            for e in base_estado
            if e.ibge is not None
        })

        municipio_selecionado = st.selectbox(
            "Município",
            options=["Todos"] + municipios,
            format_func=lambda codigo: (
                "Todos os municípios"
                if codigo == "Todos"
                else codigo
            )
        )

        estabelecimentos_filtrados = [
            e for e in base_estado
            if municipio_selecionado == "Todos"
            or str(e.ibge) == municipio_selecionado
        ]

        st.caption(
            f"**{milhar(len(estabelecimentos_filtrados))}** "
            "estabelecimentos selecionados"
        )

        st.divider()

        st.header("⚙️ Parâmetros")

        minimo_m = st.number_input(
            "Ignorar pares a até (metros)",
            min_value=0.0,
            value=1.0,
            step=1.0,
            help="Distâncias menores ou iguais ao limiar são ignoradas."
        )

        st.divider()

        st.caption("Projeto de Algoritmos · CNES")


    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Estabelecimentos na base",
        milhar(len(estabelecimentos))
    )

    col2.metric(
        "Estados disponíveis",
        len(ufs)
    )

    col3.metric(
        "Estabelecimentos filtrados",
        milhar(len(estabelecimentos_filtrados))
    )

    st.divider()



    aba_explorar, aba_algoritmo, aba_desempenho = st.tabs([
        "📍 Explorar regiões",
        "🧠 Como funciona",
        "📊 Desempenho"
    ])

    with aba_explorar:

        st.header("Descubra os serviços mais próximos")

        st.write(
            "Selecione um estado ou município na barra lateral "
            "para encontrar os dois estabelecimentos geograficamente "
            "mais próximos."
        )

        mostrar_resultado(
            estabelecimentos_filtrados,
            minimo_m,
            uf_selecionada,
            municipio_selecionado
        )

        st.divider()

        with st.expander("🗺️ Ver distribuição dos estabelecimentos"):
            mostrar_exploracao(estabelecimentos_filtrados)

    with aba_algoritmo:

        mostrar_como_funciona()

    with aba_desempenho:

        mostrar_comparacao_com_forca_bruta(
            estabelecimentos_filtrados,
            minimo_m
        )

        st.divider()

        mostrar_analise(
            estabelecimentos_filtrados,
            minimo_m
        )


if __name__ == "__main__":
    main()
