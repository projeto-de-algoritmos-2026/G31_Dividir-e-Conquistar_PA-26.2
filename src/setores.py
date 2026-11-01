from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

from src.geometria import centroide
from src.ufs import UF_DF  # noqa: F401

ARQUIVO_SETORES = Path("data/raw/DF_setores_CD2022")


@dataclass(frozen=True)
class Setor:
    codigo: str
    regiao: str
    populacao: int
    lat: float
    lon: float
    urbano: bool


def carregar_setores(caminho: Path = ARQUIVO_SETORES) -> list[Setor]:
    try:
        import shapefile
    except ImportError as erro:
        raise ImportError(
            "o pyshp é necessário para ler o shapefile do IBGE: "
            "pip install -r requirements.txt"
        ) from erro

    if not caminho.with_suffix(".shp").exists():
        raise FileNotFoundError(caminho.with_suffix(".shp"))

    leitor = shapefile.Reader(str(caminho))
    campos = [c[0] for c in leitor.fields[1:]]

    setores = []
    for registro, forma in zip(leitor.records(), leitor.shapes()):
        dados = dict(zip(campos, registro))
        lon, lat = centroide(forma.points, list(forma.parts))
        setores.append(Setor(
            codigo=dados["CD_SETOR"],
            regiao=dados["NM_SUBDIST"] or "(sem nome)",
            populacao=int(dados["v0001"] or 0),
            lat=lat, lon=lon,
            urbano=dados["SITUACAO"] == "Urbana",
        ))
    return setores


def _instrucoes() -> str:
    return (
        "Descompacte o shapefile do IBGE em data/raw/, deixando os cinco\n"
        "arquivos (.shp, .dbf, .shx, .prj, .cpg) soltos ali:\n\n"
        "  https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/"
        "Agregados_por_Setores_Censitarios/malha_com_atributos/setores/shp/UF/DF/"
        "DF_setores_CD2022.zip"
    )


def _main() -> int:
    try:
        setores = carregar_setores()
    except FileNotFoundError as erro:
        print(f"não encontrei {erro}\n\n{_instrucoes()}", file=sys.stderr)
        return 1
    except ImportError as erro:
        print(erro, file=sys.stderr)
        return 1

    populacao = sum(s.populacao for s in setores)
    rurais = sum(1 for s in setores if not s.urbano)
    print(f"{len(setores):,} setores censitários no DF".replace(",", "."))
    print(f"{populacao:,} habitantes".replace(",", "."))
    print(f"{len(setores) - rurais} urbanos · {rurais} rurais")
    print(f"{len({s.regiao for s in setores})} regiões administrativas")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
