from __future__ import annotations

import argparse
import csv
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape

from src import forca_bruta, par_proximo
from src.ufs import nome_da_uf

PASSOS_PADRAO = 10
FORCA_BRUTA_ATE_PADRAO = 10_000
MINIMO_PADRAO_M = 1.0
LIMIARES_M = (1.0, 10.0, 100.0)

COR_FORCA_BRUTA = "#c1543f"
COR_DIVIDIR = "#1E6E5A"


def cronometrar(funcao, *args):
    inicio = time.perf_counter()
    resultado = funcao(*args)
    return time.perf_counter() - inicio, resultado


def tamanhos_da_curva(total: int, passos: int, menor: int = 1000) -> list[int]:

    if total < 2:
        return []
    menor = min(menor, total)
    if passos <= 1 or menor == total:
        return [total]
    saltos = [round(menor + (total - menor) * k / (passos - 1)) for k in range(passos)]
    return sorted(set(saltos))


def curva_de_tempo(pontos, tamanhos, semente: int = 0, forca_bruta_ate: int | None = None,
                   minimo_km: float = 0.0, progresso=None) -> list[dict]:
    ordem = list(pontos)
    random.Random(semente).shuffle(ordem)

    linhas = []
    for n in tamanhos:
        recorte = ordem[:n]
        t_dc, (d_dc, _) = cronometrar(par_proximo.par_mais_proximo, recorte, minimo_km)

        t_fb, mesma = None, None
        if forca_bruta_ate is not None and n <= forca_bruta_ate:
            t_fb, (d_fb, _) = cronometrar(forca_bruta.par_mais_proximo, recorte, minimo_km)
            mesma = math.isclose(d_dc, d_fb, rel_tol=1e-9, abs_tol=1e-12)

        linha = {"n": n, "segundos_dc": t_dc, "segundos_fb": t_fb,
                 "distancia_km": d_dc, "mesma_distancia": mesma}
        linhas.append(linha)
        if progresso:
            progresso(linha)
    return linhas


def repetidas_por_hash(pontos) -> tuple[int, int, int]:
    repetidas = [c for c in Counter(pontos).values() if c > 1]
    return len(repetidas), sum(repetidas), max(repetidas, default=0)

def comparar_com_hash(pontos) -> dict:
    t_hash, (coordenadas, registros, maior) = cronometrar(repetidas_por_hash, pontos)
    t_dc, (d, _) = cronometrar(par_proximo.par_mais_proximo, pontos, 0.0)
    return {"coordenadas_repetidas": coordenadas, "registros": registros,
            "maior_empilhamento": maior, "segundos_hash": t_hash,
            "segundos_dc": t_dc, "distancia_dc_m": d * 1000}


def tabela_de_limiares(pontos, limiares_m=LIMIARES_M) -> list[dict]:
    linhas = []
    for m in limiares_m:
        segundos, (d, par) = cronometrar(par_proximo.par_mais_proximo, pontos, m / 1000)
        linhas.append({"limiar_m": m, "distancia_m": d * 1000 if par else None,
                       "par": par, "segundos": segundos})
    return linhas


def gerar_sintetico(n: int, semente: int = 0) -> list[tuple[float, float]]:
    r = random.Random(semente)
    return [(r.uniform(-33.0, 5.0), r.uniform(-73.0, -34.0)) for _ in range(n)]


def _ticks_lineares(maximo: float, alvo: int = 5) -> list[float]:
    if maximo <= 0:
        return [0.0]
    bruto = maximo / alvo
    potencia = 10 ** math.floor(math.log10(bruto))
    passo = next(m * potencia for m in (1, 2, 5, 10) if m * potencia >= bruto)
    ticks, v = [], 0.0
    while v <= maximo * 1.0000001:
        ticks.append(round(v, 12))
        v += passo
    return ticks


def _rotulo(v: float) -> str:
    return f"{v:g}"


def svg_da_curva(linhas: list[dict], log: bool = False, titulo: str = "") -> str:
    largura, altura = 760, 460
    esq, dir_, topo, base = 78, 24, 52, 64
    area_l, area_a = largura - esq - dir_, altura - topo - base

    dc = [(l["n"], l["segundos_dc"]) for l in linhas]
    fb = [(l["n"], l["segundos_fb"]) for l in linhas if l["segundos_fb"] is not None]
    xs = [x for x, _ in dc]
    ys = [y for _, y in dc + fb if y > 0] or [1e-6]

    if log:
        x0 = 10 ** math.floor(math.log10(min(xs)))
        x1 = 10 ** math.ceil(math.log10(max(xs)))
        y0 = 10 ** math.floor(math.log10(min(ys)))
        y1 = 10 ** math.ceil(math.log10(max(ys)))
        if x0 == x1:
            x1 = x0 * 10
        if y0 == y1:
            y1 = y0 * 10
        xticks = [10.0 ** k for k in range(round(math.log10(x0)), round(math.log10(x1)) + 1)]
        yticks = [10.0 ** k for k in range(round(math.log10(y0)), round(math.log10(y1)) + 1)]
        fx = lambda x: (math.log10(max(x, x0)) - math.log10(x0)) / (math.log10(x1) - math.log10(x0))
        fy = lambda y: (math.log10(max(y, y0)) - math.log10(y0)) / (math.log10(y1) - math.log10(y0))
    else:
        x0, x1 = 0.0, max(xs)
        y0, y1 = 0.0, max(ys) * 1.05
        xticks, yticks = _ticks_lineares(x1), _ticks_lineares(y1)
        fx = lambda x: (x - x0) / (x1 - x0) if x1 > x0 else 0.5
        fy = lambda y: (y - y0) / (y1 - y0)

    px = lambda x: esq + fx(x) * area_l
    py = lambda y: topo + area_a - fy(y) * area_a

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" '
         f'width="{largura}" height="{altura}" font-family="Helvetica, Arial, sans-serif">',
         f'<rect width="{largura}" height="{altura}" fill="#ffffff"/>',
         f'<text x="{largura / 2}" y="28" text-anchor="middle" font-size="16" '
         f'font-weight="bold" fill="#141917">{escape(titulo)}</text>']

    for t in yticks:
        if y0 <= t <= y1 * 1.0000001:
            y = py(t)
            s.append(f'<line x1="{esq}" y1="{y:.1f}" x2="{largura - dir_}" y2="{y:.1f}" stroke="#e3e0d6"/>')
            s.append(f'<text x="{esq - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" '
                     f'fill="#5f6b65">{escape(_rotulo(t))}</text>')
    for t in xticks:
        if x0 <= t <= x1 * 1.0000001:
            x = px(t)
            s.append(f'<line x1="{x:.1f}" y1="{topo}" x2="{x:.1f}" y2="{topo + area_a}" stroke="#eef0ea"/>')
            s.append(f'<text x="{x:.1f}" y="{topo + area_a + 18}" text-anchor="middle" '
                     f'font-size="11" fill="#5f6b65">{escape(_rotulo(t))}</text>')

    s.append(f'<line x1="{esq}" y1="{topo + area_a}" x2="{largura - dir_}" y2="{topo + area_a}" stroke="#141917"/>')
    s.append(f'<line x1="{esq}" y1="{topo}" x2="{esq}" y2="{topo + area_a}" stroke="#141917"/>')
    s.append(f'<text x="{esq + area_l / 2}" y="{altura - 14}" text-anchor="middle" '
             f'font-size="12" fill="#141917">pontos (n){" — escala log" if log else ""}</text>')
    s.append(f'<text x="18" y="{topo + area_a / 2}" text-anchor="middle" font-size="12" '
             f'fill="#141917" transform="rotate(-90 18 {topo + area_a / 2})">'
             f'segundos{" — escala log" if log else ""}</text>')

    for serie, cor in ((fb, COR_FORCA_BRUTA), (dc, COR_DIVIDIR)):
        if not serie:
            continue
        pontos_svg = " ".join(f"{px(x):.1f},{py(y if y > 0 else y0):.1f}" for x, y in serie)
        s.append(f'<polyline points="{pontos_svg}" fill="none" stroke="{cor}" stroke-width="2.5"/>')
        for x, y in serie:
            s.append(f'<circle cx="{px(x):.1f}" cy="{py(y if y > 0 else y0):.1f}" r="3.5" fill="{cor}"/>')

    lx, ly = esq + 24, topo + 10
    s.append(f'<rect x="{lx - 10}" y="{ly - 6}" width="250" height="50" fill="#ffffff" stroke="#e3e0d6"/>')
    s.append(f'<line x1="{lx}" y1="{ly + 8}" x2="{lx + 24}" y2="{ly + 8}" stroke="{COR_FORCA_BRUTA}" stroke-width="2.5"/>')
    s.append(f'<text x="{lx + 32}" y="{ly + 12}" font-size="12" fill="#141917">força bruta, O(n²)</text>')
    s.append(f'<line x1="{lx}" y1="{ly + 30}" x2="{lx + 24}" y2="{ly + 30}" stroke="{COR_DIVIDIR}" stroke-width="2.5"/>')
    s.append(f'<text x="{lx + 32}" y="{ly + 34}" font-size="12" fill="#141917">dividir e conquistar, O(n log n)</text>')
    s.append("</svg>")
    return "\n".join(s)


def _milhar(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _decimal(v: float, casas: int = 2) -> str:
    return f"{v:.{casas}f}".replace(".", ",")


def _descrever(estabelecimentos, indice: int) -> str:
    if estabelecimentos is None:
        return f"ponto {indice}"
    e = estabelecimentos[indice]
    return f"{e.nome} — {nome_da_uf(e.uf)} (município IBGE {e.ibge})"


def relatorio_md(linhas, hash_, limiares, total: int, semente: int, minimo_m: float,
                 fonte: str, estabelecimentos=None) -> str:
    partes = []
    if fonte != "CNES":
        partes.append(f"> **DADOS SINTÉTICOS** ({fonte}) — pontos sorteados, "
                      "não são números do CNES.\n")
    partes.append(f"# Validação do dividir e conquistar — {_milhar(total)} pontos\n")

    partes.append("## 1. Curva de tempo\n")
    partes.append(f"Prefixos de uma mesma ordem embaralhada (semente {semente}), "
                  f"ignorando pares a {minimo_m:g} m ou menos.\n")
    partes.append("| pontos | dividir e conquistar | força bruta | ganho | mesma distância? |")
    partes.append("| --- | --- | --- | --- | --- |")
    for l in linhas:
        fb = f"{_decimal(l['segundos_fb'], 3)} s" if l["segundos_fb"] is not None else "—"
        ganho = (f"{_decimal(l['segundos_fb'] / l['segundos_dc'], 0)}×"
                 if l["segundos_fb"] is not None and l["segundos_dc"] > 0 else "—")
        mesma = {True: "sim", False: "**NÃO**", None: "—"}[l["mesma_distancia"]]
        partes.append(f"| {_milhar(l['n'])} | {_decimal(l['segundos_dc'], 3)} s | {fb} | {ganho} | {mesma} |")
    partes.append("\n![Curva de tempo](curva_tempo.svg)\n")
    partes.append("![Curva de tempo, escala log](curva_tempo_log.svg)\n")

    partes.append("## 2. A tabela hash acha as duplicatas\n")
    partes.append(f"{_milhar(hash_['coordenadas_repetidas'])} coordenadas repetidas, "
                  f"{_milhar(hash_['registros'])} registros envolvidos, maior "
                  f"empilhamento de {_milhar(hash_['maior_empilhamento'])}.\n")
    partes.append("| | tempo |")
    partes.append("| --- | --- |")
    partes.append(f"| tabela hash | {_decimal(hash_['segundos_hash'], 3)} s |")
    partes.append(f"| dividir e conquistar (sem limiar) | {_decimal(hash_['segundos_dc'], 3)} s |")

    partes.append("\n## 3. O par mais próximo acima de um limiar\n")
    partes.append("| acima de | distância | tempo | par |")
    partes.append("| --- | --- | --- | --- |")
    for l in limiares:
        if l["par"] is None:
            partes.append(f"| {l['limiar_m']:g} m | — | {_decimal(l['segundos'], 3)} s | nenhum par |")
            continue
        a, b = l["par"]
        partes.append(f"| {l['limiar_m']:g} m | {_decimal(l['distancia_m'], 2)} m | "
                      f"{_decimal(l['segundos'], 3)} s | {_descrever(estabelecimentos, a)} · "
                      f"{_descrever(estabelecimentos, b)} |")
    return "\n".join(partes) + "\n"


def salvar_csv(linhas, caminho: Path) -> None:
    with open(caminho, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["n", "segundos_dc", "segundos_fb", "distancia_km", "mesma_distancia"])
        for l in linhas:
            escritor.writerow([l["n"], f"{l['segundos_dc']:.6f}",
                               "" if l["segundos_fb"] is None else f"{l['segundos_fb']:.6f}",
                               f"{l['distancia_km']:.9f}",
                               "" if l["mesma_distancia"] is None else int(l["mesma_distancia"])])


def _argumentos(argv):
    p = argparse.ArgumentParser(description="Validação do dividir e conquistar.")
    p.add_argument("--passos", type=int, default=PASSOS_PADRAO, help="pontos na curva")
    p.add_argument("--forca-bruta-ate", type=int, default=FORCA_BRUTA_ATE_PADRAO,
                   help="maior n em que a força bruta roda (ela é O(n²))")
    p.add_argument("--minimo-m", type=float, default=MINIMO_PADRAO_M,
                   help="ignora pares a essa distância ou menos, em metros")
    p.add_argument("--semente", type=int, default=0)
    p.add_argument("--sintetico", type=int, metavar="N",
                   help="usa N pontos sorteados no lugar do CSV do CNES")
    p.add_argument("--saida", type=Path, default=None)
    return p.parse_args(argv)


def _main(argv=None) -> int:
    args = _argumentos(argv)

    estabelecimentos = None
    if args.sintetico:
        pontos = gerar_sintetico(args.sintetico, args.semente)
        fonte = f"{_milhar(args.sintetico)} pontos sorteados, semente {args.semente}"
        saida = args.saida or Path("resultados/sintetico")
    else:
        from src.dados import carregar, coordenadas
        try:
            estabelecimentos = carregar()
        except FileNotFoundError as erro:
            print(f"não encontrei {erro} — veja o README (ou use --sintetico N)", file=sys.stderr)
            return 1
        pontos = coordenadas(estabelecimentos)
        fonte = "CNES"
        saida = args.saida or Path("resultados")

    saida.mkdir(parents=True, exist_ok=True)
    tamanhos = tamanhos_da_curva(len(pontos), args.passos)
    print(f"{_milhar(len(pontos))} pontos · força bruta até {_milhar(args.forca_bruta_ate)}")

    def mostrar(l):
        fb = f"{l['segundos_fb']:.3f} s" if l["segundos_fb"] is not None else "—"
        print(f"  n = {_milhar(l['n']):>7} · dividir {l['segundos_dc']:.3f} s · força bruta {fb}")

    linhas = curva_de_tempo(pontos, tamanhos, args.semente, args.forca_bruta_ate,
                            args.minimo_m / 1000, progresso=mostrar)
    if any(l["mesma_distancia"] is False for l in linhas):
        print("ATENÇÃO: os dois algoritmos devolveram distâncias diferentes.", file=sys.stderr)

    hash_ = comparar_com_hash(pontos)
    limiares = tabela_de_limiares(pontos)

    titulo = "Tempo para achar o par mais próximo"
    salvar_csv(linhas, saida / "curva_tempo.csv")
    (saida / "curva_tempo.svg").write_text(svg_da_curva(linhas, False, titulo), encoding="utf-8")
    (saida / "curva_tempo_log.svg").write_text(svg_da_curva(linhas, True, titulo), encoding="utf-8")
    (saida / "validacao.md").write_text(
        relatorio_md(linhas, hash_, limiares, len(pontos), args.semente, args.minimo_m,
                     fonte, estabelecimentos), encoding="utf-8")
    print(f"salvo em {saida}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())