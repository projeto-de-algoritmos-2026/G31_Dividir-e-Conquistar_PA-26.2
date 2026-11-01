from __future__ import annotations

import math
import random

import pandas as pd
import pydeck as pdk
import streamlit as st

from src import forca_bruta, par_proximo
from src.dados import carregar, coordenadas
from src.ufs import nome_da_uf
from validacao import cronometrar

st.set_page_config(page_title="Par mais próximo — CNES", page_icon="📍", layout="wide")

LIMITE_FORCA_BRUTA = 3_000


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _metros(distancia_km: float) -> str:
    return f"{distancia_km * 1000:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


@st.cache_data(show_spinner="Carregando a base do CNES…")
def carregar_base():
    return carregar()


@st.cache_data(show_spinner="Procurando o par mais próximo…")
def achar_par(minimo_m: float):
    pontos = coordenadas(carregar_base())
    segundos, (distancia_km, par) = cronometrar(par_proximo.par_mais_proximo,
                                                pontos, minimo_m / 1000)
    return distancia_km, par, segundos


def _zoom(distancia_km: float) -> float:
    return max(3.0, min(17.0, 16 - math.log2(max(distancia_km, 0.01) / 0.1)))


def mostrar_instrucoes_de_dados() -> None:
    st.error("Base do CNES não encontrada em `data/raw/`.")
    st.markdown(
        "Baixe o CSV e salve como `data/raw/Unidades_Basicas_Saude-UBS.csv`:\n\n"
        "<https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs>"
    )


def mostrar_estabelecimento(titulo: str, e) -> None:
    st.markdown(f"**{titulo}**")
    st.write(e.nome)
    st.caption(f"{e.bairro or '(sem bairro)'} · {nome_da_uf(e.uf)} · "
               f"município IBGE {e.ibge} · CNES {e.cnes}")


def mostrar_mapa(a, b, distancia_km: float) -> None:
    pontos = pd.DataFrame([
        {"nome": a.nome, "lat": a.lat, "lon": a.lon, "cor": [193, 84, 63, 230]},
        {"nome": b.nome, "lat": b.lat, "lon": b.lon, "cor": [30, 110, 90, 230]},
    ])
    ligacao = pd.DataFrame([{"lat0": a.lat, "lon0": a.lon, "lat1": b.lat, "lon1": b.lon}])

    camadas = [
        pdk.Layer("LineLayer", data=ligacao, get_source_position="[lon0, lat0]",
                  get_target_position="[lon1, lat1]", get_color=[20, 25, 23, 200],
                  get_width=3),
        pdk.Layer("ScatterplotLayer", data=pontos, get_position="[lon, lat]",
                  get_fill_color="cor", get_radius=6, radius_min_pixels=7,
                  pickable=True),
    ]
    st.pydeck_chart(pdk.Deck(
        layers=camadas,
        initial_view_state=pdk.ViewState(latitude=(a.lat + b.lat) / 2,
                                         longitude=(a.lon + b.lon) / 2,
                                         zoom=_zoom(distancia_km)),
        tooltip={"text": "{nome}"},
    ))


def mostrar_resultado(estabelecimentos, minimo_m: float) -> None:
    distancia_km, par, segundos = achar_par(minimo_m)

    if par is None:
        st.info("Nenhum par acima desse mínimo.")
        return

    a, b = estabelecimentos[par[0]], estabelecimentos[par[1]]
    col1, col2, col3 = st.columns(3)
    col1.metric("Menor distância", f"{_metros(distancia_km)} m")
    col2.metric("Estabelecimentos", _milhar(len(estabelecimentos)))
    col3.metric("Tempo (dividir e conquistar)", f"{segundos:.2f} s")

    if minimo_m <= 0:
        st.warning(
            "Sem limiar, a resposta é quase sempre **zero metros**: há cadastros "
            "empilhados na mesma coordenada (o centro da cidade usado como "
            "preenchimento). Para achar isso basta uma tabela hash — o algoritmo "
            "só faz diferença com um limiar."
        )

    esq, dir_ = st.columns(2)
    with esq:
        mostrar_estabelecimento("Serviço A", a)
    with dir_:
        mostrar_estabelecimento("Serviço B", b)
    mostrar_mapa(a, b, distancia_km)


def mostrar_comparacao_com_forca_bruta(estabelecimentos, minimo_m: float) -> None:
    st.subheader("Comparar com a força bruta")
    st.caption(
        f"A força bruta compara todos os pares, O(n²) — na base inteira são mais de "
        f"um bilhão de comparações e vários minutos. Aqui ela só roda num recorte "
        f"sorteado de **até {_milhar(LIMITE_FORCA_BRUTA)} pontos**."
    )

    n = st.slider("Pontos no recorte", min_value=500, max_value=LIMITE_FORCA_BRUTA,
                  value=2_000, step=500)
    semente = st.number_input("Semente do sorteio", value=0, step=1)

    if not st.button("Rodar as duas"):
        return

    pontos = coordenadas(estabelecimentos)
    recorte = random.Random(int(semente)).sample(pontos, min(n, len(pontos)))

    t_dc, (d_dc, _) = cronometrar(par_proximo.par_mais_proximo, recorte, minimo_m / 1000)
    t_fb, (d_fb, _) = cronometrar(forca_bruta.par_mais_proximo, recorte, minimo_m / 1000)

    col1, col2, col3 = st.columns(3)
    col1.metric("Dividir e conquistar", f"{t_dc:.3f} s")
    col2.metric("Força bruta", f"{t_fb:.3f} s")
    col3.metric("Ganho", f"{t_fb / t_dc:.0f}×" if t_dc > 0 else "—")

    if math.isclose(d_dc, d_fb, rel_tol=1e-9, abs_tol=1e-12):
        st.success(f"Mesma resposta: {_metros(d_dc)} m nos dois algoritmos.")
    else:
        st.error(f"Respostas diferentes: {_metros(d_dc)} m contra {_metros(d_fb)} m.")


def main() -> None:
    st.title("📍 Quais dois serviços de saúde estão mais perto?")
    st.caption(
        "Par de pontos mais próximos na base do CNES, por dividir e conquistar "
        "(O(n log n)). Pares abaixo do limiar escolhido são ignorados."
    )

    try:
        estabelecimentos = carregar_base()
    except FileNotFoundError:
        mostrar_instrucoes_de_dados()
        return

    with st.sidebar:
        st.header("Parâmetros")
        minimo_m = st.number_input("Ignorar pares a até (metros)", min_value=0.0,
                                   value=1.0, step=1.0,
                                   help="0 mostra as duplicatas; 1, 10 e 100 são os "
                                        "limiares medidos no relatório.")
        comparar = st.checkbox("Comparar com a força bruta (recorte pequeno)")

    mostrar_resultado(estabelecimentos, minimo_m)

    if comparar:
        mostrar_comparacao_com_forca_bruta(estabelecimentos, minimo_m)


if __name__ == "__main__":
    main()