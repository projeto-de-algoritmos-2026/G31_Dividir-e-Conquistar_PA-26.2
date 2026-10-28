from __future__ import annotations

import sys

from src.geometria import distancia_km, distancia_plana, projetar_todos

def _valida(a, b, minimo_km: float) -> float:
    d = distancia_plana(a, b)
    if minimo_km <= 0:
        return d
    return d if d > minimo_km else float("inf")


def _bruta(pontos, minimo_km):
    melhor, par = float("inf"), None
    for i in range(len(pontos)):
        for j in range(i + 1, len(pontos)):
            d = _valida(pontos[i], pontos[j], minimo_km)
            if d < melhor:
                melhor, par = d, (pontos[i][2], pontos[j][2])
    return melhor, par


def _recursao(por_x, por_y, minimo_km):
    n = len(por_x)
    if n <= 3:
        return _bruta(por_x, minimo_km)

    meio = n // 2
    corte = por_x[meio][0]
    indices_esquerda = {p[2] for p in por_x[:meio]}

    y_esquerda = [p for p in por_y if p[2] in indices_esquerda]
    y_direita = [p for p in por_y if p[2] not in indices_esquerda]

    d_esq, par_esq = _recursao(por_x[:meio], y_esquerda, minimo_km)
    d_dir, par_dir = _recursao(por_x[meio:], y_direita, minimo_km)
    melhor, par = (d_esq, par_esq) if d_esq <= d_dir else (d_dir, par_dir)

    faixa = [p for p in por_y if abs(p[0] - corte) < melhor]
    for i in range(len(faixa)):
        for j in range(i + 1, len(faixa)):
            if faixa[j][1] - faixa[i][1] >= melhor:
                break
            d = _valida(faixa[i], faixa[j], minimo_km)
            if d < melhor:
                melhor, par = d, (faixa[i][2], faixa[j][2])
    return melhor, par


def par_mais_proximo(pontos: list[tuple[float, float]],
                     minimo_km: float = 0.0) -> tuple[float, tuple[int, int] | None]:
    if minimo_km < 0:
        raise ValueError(f"minimo_km não pode ser negativo, recebi {minimo_km}")
    if len(pontos) < 2:
        return float("inf"), None

    planos = [(x, y, i) for i, (x, y) in enumerate(projetar_todos(pontos))]
    por_x = sorted(planos, key=lambda p: (p[0], p[1]))
    por_y = sorted(planos, key=lambda p: (p[1], p[0]))

    _, par = _recursao(por_x, por_y, minimo_km)
    if par is None:
        return float("inf"), None

    i, j = par
    return distancia_km(*pontos[i], *pontos[j]), (i, j)


def _main(argv: list[str]) -> int:
    from src.dados import carregar, coordenadas

    minimo = float(argv[1]) if len(argv) > 1 else 0.0
    try:
        estabelecimentos = carregar()
    except FileNotFoundError as erro:
        print(f"não encontrei {erro} — veja o README", file=sys.stderr)
        return 1

    d, par = par_mais_proximo(coordenadas(estabelecimentos), minimo)
    if par is None:
        print("nenhum par acima desse mínimo")
        return 0

    a, b = estabelecimentos[par[0]], estabelecimentos[par[1]]
    print(f"{len(estabelecimentos):,} estabelecimentos · mínimo de {minimo:g} km"
          .replace(",", "."))
    print(f"menor distância: {d * 1000:.2f} metros\n")
    print(f"  {a.nome} · UF {a.uf} · IBGE {a.ibge}")
    print(f"  {b.nome} · UF {b.uf} · IBGE {b.ibge}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
