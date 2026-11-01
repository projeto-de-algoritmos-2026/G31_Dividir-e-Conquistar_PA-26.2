
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass
from typing import Sequence

from src.geometria import distancia_km


def _ordenar_e_contar(valores: Sequence[float]) -> tuple[list[float], int]:
    n = len(valores)
    if n <= 1:
        return list(valores), 0

    meio = n // 2
    esquerda, inv_esq = _ordenar_e_contar(valores[:meio])
    direita, inv_dir = _ordenar_e_contar(valores[meio:])

    # Junção: enquanto intercala, todo elemento que sai da direita antes de
    # elementos que ainda restam na esquerda forma uma inversão com cada um
    # deles. Na igualdade sai o da esquerda, então empate nunca conta.
    intercalado: list[float] = []
    cruzadas = 0
    i = j = 0
    while i < len(esquerda) and j < len(direita):
        if esquerda[i] <= direita[j]:
            intercalado.append(esquerda[i])
            i += 1
        else:
            intercalado.append(direita[j])
            j += 1
            cruzadas += len(esquerda) - i
    intercalado.extend(esquerda[i:])
    intercalado.extend(direita[j:])

    return intercalado, inv_esq + inv_dir + cruzadas


def contar_inversoes(valores: Sequence[float]) -> int:
    """Pares (i, j) com i < j e valores[i] > valores[j]. Empates não contam."""
    return _ordenar_e_contar(valores)[1]


@dataclass(frozen=True)
class Concordancia:
    """
    Resultado da comparação entre dois rankings, par a par.

    Um par é **discordante** quando o setor mais populoso tem a unidade mais
    longe. Zero discordantes é "quem tem mais gente tem a saúde mais perto";
    perto de metade dos pares é "os dois rankings são independentes"; mais que
    isso é o contrário da hipótese. Pares empatados em população ou em distância
    não dizem nada sobre a ordem e ficam fora da conta de `comparaveis`.
    """
    n: int
    pares: int
    empatados: int
    discordantes: int

    @property
    def comparaveis(self) -> int:
        return self.pares - self.empatados

    @property
    def concordantes(self) -> int:
        return self.comparaveis - self.discordantes

    @property
    def fracao_discordante(self) -> float:
        """Discordantes entre os pares comparáveis; 0,5 é o caso independente."""
        return self.discordantes / self.comparaveis if self.comparaveis else 0.0

    @property
    def fracao_sobre_pares(self) -> float:
        """Discordantes sobre todos os n(n-1)/2 pares, empatados incluídos."""
        return self.discordantes / self.pares if self.pares else 0.0


def _pares_iguais(chaves) -> int:
    return sum(c * (c - 1) // 2 for c in Counter(chaves).values())


def comparar_rankings(populacoes: Sequence[float],
                      distancias: Sequence[float]) -> Concordancia:
    """
    Distância de Kendall entre "mais população primeiro" e "mais perto primeiro".

    Ordena os índices por (-população, distância) e conta as inversões na
    sequência de distâncias: um par com população estritamente maior e
    distância estritamente maior é uma inversão. Dentro de um grupo de mesma
    população a ordem por distância já é crescente, então empate não conta.
    """
    if len(populacoes) != len(distancias):
        raise ValueError("populacoes e distancias precisam ter o mesmo tamanho")

    n = len(populacoes)
    ordem = sorted(range(n), key=lambda i: (-populacoes[i], distancias[i]))
    discordantes = contar_inversoes([distancias[i] for i in ordem])

    pares = n * (n - 1) // 2
    empatados = (_pares_iguais(populacoes) + _pares_iguais(distancias)
                 - _pares_iguais(zip(populacoes, distancias)))
    return Concordancia(n=n, pares=pares, empatados=empatados,
                        discordantes=discordantes)


def distancia_ate_a_mais_proxima(pontos: Sequence[tuple[float, float]],
                                 unidades: Sequence[tuple[float, float]]) -> list[float]:
    """Para cada (lat, lon) de `pontos`, a haversine até a unidade mais próxima."""
    if not unidades:
        raise ValueError("preciso de pelo menos uma unidade")
    return [min(distancia_km(lat, lon, ulat, ulon) for ulat, ulon in unidades)
            for lat, lon in pontos]


def _main() -> int:
    from src.dados import carregar
    from src.setores import UF_DF, carregar_setores

    try:
        setores = carregar_setores()
        estabelecimentos = [e for e in carregar() if e.uf == UF_DF]
    except FileNotFoundError as erro:
        print(f"não encontrei {erro} — veja o README", file=sys.stderr)
        return 1
    except ImportError as erro:
        print(erro, file=sys.stderr)
        return 1

    unidades = [(e.lat, e.lon) for e in estabelecimentos]
    distancias = distancia_ate_a_mais_proxima([(s.lat, s.lon) for s in setores], unidades)
    r = comparar_rankings([s.populacao for s in setores], distancias)

    milhar = lambda n: f"{n:,}".replace(",", ".")
    print(f"{milhar(len(setores))} setores · {milhar(len(unidades))} unidades (UF {UF_DF})")
    print(f"pares: {milhar(r.pares)} · empatados: {milhar(r.empatados)} · "
          f"comparáveis: {milhar(r.comparaveis)}")
    print(f"discordantes: {milhar(r.discordantes)} "
          f"({r.fracao_discordante:.1%} dos comparáveis, "
          f"{r.fracao_sobre_pares:.1%} de todos os pares)")
    print("0,5 = rankings independentes; abaixo disso, mais gente tende a ter "
          "a unidade mais perto")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())