import itertools
import random
import unittest

from src.forca_bruta import par_mais_proximo as bruta
from src.geometria import distancia_km, distancia_plana, projetar_todos
from src.par_proximo import par_mais_proximo as dividir


def menor_no_plano(pontos, minimo_km=0.0):
    planos = projetar_todos(pontos)
    melhor = float("inf")
    for i, j in itertools.combinations(range(len(pontos)), 2):
        d = distancia_plana(planos[i], planos[j])
        if minimo_km > 0 and d <= minimo_km:
            continue
        melhor = min(melhor, d)
    return melhor


def sorteio(n, semente, repetidos=0):
    r = random.Random(semente)
    pts = [(r.uniform(-33.0, 5.0), r.uniform(-73.0, -34.0)) for _ in range(n)]
    pts += [pts[r.randrange(len(pts))] for _ in range(repetidos)]
    return pts


class TestCasosPequenos(unittest.TestCase):

    def test_menos_de_dois_pontos_nao_tem_par(self):
        self.assertEqual(bruta([]), (float("inf"), None))
        self.assertEqual(bruta([(0.0, 0.0)]), (float("inf"), None))

    def test_dois_pontos_sao_o_par(self):
        d, par = bruta([(-15.80, -47.90), (-15.81, -47.90)])
        self.assertEqual(set(par), {0, 1})
        self.assertAlmostEqual(d, distancia_km(-15.80, -47.90, -15.81, -47.90))

    def test_pontos_iguais_dao_distancia_zero(self):
        d, par = bruta([(-15.8, -47.9), (-20.0, -50.0), (-15.8, -47.9)])
        self.assertAlmostEqual(d, 0.0)
        self.assertEqual(set(par), {0, 2})

    def test_minimo_negativo_e_erro(self):
        with self.assertRaises(ValueError):
            bruta([(0.0, 0.0), (1.0, 1.0)], minimo_km=-1.0)

    def test_limiar_alto_demais_nao_deixa_par_nenhum(self):
        d, par = bruta([(-15.8, -47.9), (-15.9, -47.9)], minimo_km=10_000.0)
        self.assertEqual(d, float("inf"))
        self.assertIsNone(par)


class TestContraAReferencia(unittest.TestCase):

    def test_acha_a_menor_distancia_no_plano(self):
        for semente in range(8):
            pontos = sorteio(40, semente)
            _, par = bruta(pontos)
            planos = projetar_todos(pontos)
            self.assertAlmostEqual(distancia_plana(planos[par[0]], planos[par[1]]),
                                   menor_no_plano(pontos), places=9)

    def test_o_par_devolvido_tem_mesmo_a_distancia_informada(self):
        pontos = sorteio(60, 42)
        d, par = bruta(pontos)
        self.assertAlmostEqual(d, distancia_km(*pontos[par[0]], *pontos[par[1]]))


class TestConcordaComODividirEConquistar(unittest.TestCase):
    """
    É isto que justifica o trabalho: a força bruta é a régua, e o algoritmo
    rápido tem de dar a mesma resposta que ela.
    """

    def test_mesma_distancia_sem_limiar(self):
        for n in (10, 50, 200):
            for semente in range(5):
                pontos = sorteio(n, semente)
                with self.subTest(n=n, semente=semente):
                    self.assertAlmostEqual(bruta(pontos)[0], dividir(pontos)[0],
                                           places=9)

    def test_mesma_distancia_com_limiar(self):
        for minimo in (0.001, 1.0, 50.0):
            for semente in range(5):
                pontos = sorteio(120, semente)
                with self.subTest(minimo=minimo, semente=semente):
                    self.assertAlmostEqual(bruta(pontos, minimo)[0],
                                           dividir(pontos, minimo)[0], places=9)

    def test_mesma_distancia_com_muitas_duplicatas(self):
        for semente in range(5):
            pontos = sorteio(60, semente, repetidos=40)
            with self.subTest(semente=semente):
                self.assertAlmostEqual(bruta(pontos)[0], dividir(pontos)[0],
                                       places=9)
                self.assertAlmostEqual(bruta(pontos, 0.001)[0],
                                       dividir(pontos, 0.001)[0], places=9)

    def test_concordam_tambem_quando_nao_existe_par_valido(self):
        pontos = [(-15.8, -47.9), (-15.8, -47.9)]
        self.assertEqual(bruta(pontos, 1.0), (float("inf"), None))
        self.assertEqual(dividir(pontos, 1.0), (float("inf"), None))


if __name__ == "__main__":
    unittest.main()
