from __future__ import annotations

import math

from src.geometria import distancia_km, projetar_todos


def par_mais_proximo(pontos: list[tuple[float, float]],
                     minimo_km: float = 0.0) -> tuple[float, tuple[int, int] | None]:

    if minimo_km < 0:
        raise ValueError(f"minimo_km não pode ser negativo, recebi {minimo_km}")
    n = len(pontos)
    if n < 2:
        return float("inf"), None

    planos = projetar_todos(pontos)
    xs = [p[0] for p in planos]
    ys = [p[1] for p in planos]
    hipot = math.hypot

    melhor, par = float("inf"), None
    for i in range(n - 1):
        xi, yi = xs[i], ys[i]
        for j in range(i + 1, n):
            d = hipot(xi - xs[j], yi - ys[j])
            if d < melhor and (minimo_km <= 0 or d > minimo_km):
                melhor, par = d, (i, j)

    if par is None:
        return float("inf"), None
    return distancia_km(*pontos[par[0]], *pontos[par[1]]), par