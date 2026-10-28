from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

ARQUIVO_CNES = Path("data/raw/Unidades_Basicas_Saude-UBS.csv")

LAT_BRASIL = (-34.0, 6.0)
LON_BRASIL = (-74.0, -33.0)


@dataclass(frozen=True)
class Estabelecimento:
    cnes: str
    nome: str
    bairro: str
    uf: str
    ibge: str
    lat: float
    lon: float


def _numero(texto: str | None) -> float | None:
    if texto is None:
        return None
    texto = texto.strip().replace(",", ".")
    try:
        return float(texto)
    except ValueError:
        return None


def _no_brasil(lat: float, lon: float) -> bool:
    return (LAT_BRASIL[0] <= lat <= LAT_BRASIL[1]
            and LON_BRASIL[0] <= lon <= LON_BRASIL[1])


def carregar(caminho: Path = ARQUIVO_CNES) -> list[Estabelecimento]:
    if not caminho.exists():
        raise FileNotFoundError(caminho)

    estabelecimentos = []
    with open(caminho, encoding="utf-8", errors="replace") as arquivo:
        for linha in csv.DictReader(arquivo, delimiter=";"):
            lat, lon = _numero(linha["LATITUDE"]), _numero(linha["LONGITUDE"])
            if lat is None or lon is None or not _no_brasil(lat, lon):
                continue
            estabelecimentos.append(Estabelecimento(
                cnes=linha["CNES"].strip(),
                nome=linha["NOME"].strip(),
                bairro=linha["BAIRRO"].strip(),
                uf=linha["UF"].strip(),
                ibge=linha["IBGE"].strip(),
                lat=lat, lon=lon,
            ))
    return estabelecimentos


def coordenadas(estabelecimentos: list[Estabelecimento]) -> list[tuple[float, float]]:
    return [(e.lat, e.lon) for e in estabelecimentos]


def _instrucoes() -> str:
    return (
        "Baixe o CSV e salve como data/raw/Unidades_Basicas_Saude-UBS.csv\n\n"
        "  https://dadosabertos.saude.gov.br/dataset/"
        "unidades-basicas-de-saude-ubs"
    )


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _main() -> int:
    try:
        estabelecimentos = carregar()
    except FileNotFoundError as erro:
        print(f"não encontrei {erro}\n\n{_instrucoes()}", file=sys.stderr)
        return 1

    from collections import Counter

    ufs = {e.uf for e in estabelecimentos}
    posicoes = Counter((e.lat, e.lon) for e in estabelecimentos)
    repetidas = {p: c for p, c in posicoes.items() if c > 1}
    envolvidos = sum(repetidas.values())
    maior = max(repetidas.values()) if repetidas else 0

    print(f"{_milhar(len(estabelecimentos))} estabelecimentos com coordenada válida")
    print(f"{len(ufs)} unidades da federação")
    print(f"{_milhar(len(repetidas))} coordenadas repetidas, "
          f"{_milhar(envolvidos)} registros envolvidos")
    print(f"maior empilhamento: {maior} estabelecimentos no mesmo ponto")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
