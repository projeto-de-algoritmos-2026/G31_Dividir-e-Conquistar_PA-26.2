from __future__ import annotations

import math

RAIO_DA_TERRA_KM = 6371.0
KM_POR_GRAU = 111.0


def centroide(pontos: list[tuple[float, float]],
              inicios: list[int] | None = None) -> tuple[float, float]:
    if not pontos:
        raise ValueError("polígono sem pontos")

    limites = list(inicios or [0]) + [len(pontos)]
    area_dobrada = soma_x = soma_y = 0.0

    for i in range(len(limites) - 1):
        anel = pontos[limites[i]:limites[i + 1]]
        for j in range(len(anel) - 1):
            x0, y0 = anel[j]
            x1, y1 = anel[j + 1]
            cruzado = x0 * y1 - x1 * y0
            area_dobrada += cruzado
            soma_x += (x0 + x1) * cruzado
            soma_y += (y0 + y1) * cruzado

    if abs(area_dobrada) < 1e-12:
        return (sum(p[0] for p in pontos) / len(pontos),
                sum(p[1] for p in pontos) / len(pontos))

    return soma_x / (3 * area_dobrada), soma_y / (3 * area_dobrada)


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    fi1, fi2 = math.radians(lat1), math.radians(lat2)
    dfi = fi2 - fi1
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dfi / 2) ** 2 + math.cos(fi1) * math.cos(fi2) * math.sin(dlambda / 2) ** 2
    return 2 * RAIO_DA_TERRA_KM * math.asin(math.sqrt(a))


def projetar(lat: float, lon: float, lat_referencia: float) -> tuple[float, float]:
    x = lon * math.cos(math.radians(lat_referencia)) * KM_POR_GRAU
    y = lat * KM_POR_GRAU
    return x, y


def latitude_de_referencia(pontos: list[tuple[float, float]]) -> float:
    if not pontos:
        return 0.0
    return sum(lat for lat, _ in pontos) / len(pontos)


def projetar_todos(pontos: list[tuple[float, float]],
                   lat_referencia: float | None = None
                   ) -> list[tuple[float, float]]:
    if lat_referencia is None:
        lat_referencia = latitude_de_referencia(pontos)
    return [projetar(lat, lon, lat_referencia) for lat, lon in pontos]


def distancia_plana(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])
