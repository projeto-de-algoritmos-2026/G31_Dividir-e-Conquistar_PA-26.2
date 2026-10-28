import itertools
import random
import unittest

from src.geometria import distancia_km, distancia_plana, projetar_todos
from src.par_proximo import par_mais_proximo


def referencia(pontos, minimo_km=0.0):
    planos = projetar_todos(pontos)
    melhor, par = float("inf"), None
    for i, j in itertools.combinations(range(len(pontos)), 2):
        d = distancia_plana(planos[i], planos[j])
        if minimo_km > 0 and d <= minimo_km:
            continue
        if d < melhor:
            melhor, par = d, (i, j)
    if par is None:
        return float("inf"), None
    return distancia_km(*pontos[par[0]], *pontos[par[1]]), par


class TestCasosPequenos(unittest.TestCase):

    def test_menos_de_dois_pontos_nao_tem_par(self):
        self.assertEqual(par_mais_proximo([]), (float("inf"), None))
        self.assertEqual(par_mais_proximo([(0.0, 0.0)]), (float("inf"), None))

    def test_dois_pontos_sao_o_par(self):
        d, par = par_mais_proximo([(-15.80, -47.90), (-15.81, -47.90)])
        self.assertEqual(set(par), {0, 1})
        self.assertAlmostEqual(d, distancia_km(-15.80, -47.90, -15.81, -47.90))

    def test_pontos_iguais_dao_distancia_zero(self):
        d, par = par_mais_proximo([(-15.8, -47.9), (-20.0, -50.0), (-15.8, -47.9)])
        self.assertAlmostEqual(d, 0.0)
        self.assertEqual(set(par), {0, 2})

    def test_acha_o_par_escondido_no_meio(self):
        pontos = [(-15.0, -47.0), (-16.0, -47.0), (-17.0, -47.0),
                  (-17.0001, -47.0001), (-18.0, -47.0)]
        d, par = par_mais_proximo(pontos)
        self.assertEqual(set(par), {2, 3})
        self.assertLess(d, 0.1)

    def test_minimo_negativo_e_erro(self):
        with self.assertRaises(ValueError):
            par_mais_proximo([(0.0, 0.0), (1.0, 1.0)], minimo_km=-1.0)


class TestContraForcaBruta(unittest.TestCase):

    def _sorteio(self, n, semente):
        r = random.Random(semente)
        return [(r.uniform(-33.0, 5.0), r.uniform(-73.0, -34.0)) for _ in range(n)]

    def test_bate_com_a_referencia_em_instancias_sorteadas(self):
        for semente in range(12):
            pontos = self._sorteio(60, semente)
            esperado, _ = referencia(pontos)
            obtido, _ = par_mais_proximo(pontos)
            self.assertAlmostEqual(obtido, esperado, places=9, msg=f"semente {semente}")

    def test_bate_mesmo_com_muitos_pontos_repetidos(self):
        r = random.Random(3)
        base = [(r.uniform(-20, -10), r.uniform(-60, -40)) for _ in range(10)]
        pontos = [base[r.randrange(len(base))] for _ in range(50)]
        self.assertAlmostEqual(par_mais_proximo(pontos)[0], 0.0)

    def test_o_par_devolvido_tem_mesmo_a_distancia_informada(self):
        pontos = self._sorteio(80, 99)
        d, par = par_mais_proximo(pontos)
        self.assertAlmostEqual(d, distancia_km(*pontos[par[0]], *pontos[par[1]]))


class TestLimiar(unittest.TestCase):

    def test_o_limiar_pula_os_pontos_colados(self):
        pontos = [(-15.8, -47.9), (-15.8, -47.9), (-15.9, -47.9), (-16.1, -47.9)]
        sem, _ = par_mais_proximo(pontos)
        com, par = par_mais_proximo(pontos, minimo_km=0.001)
        self.assertAlmostEqual(sem, 0.0)
        self.assertGreater(com, 0.001)
        self.assertIn(set(par), ({0, 2}, {1, 2}))

    def test_bate_com_a_referencia_tambem_com_limiar(self):
        r = random.Random(5)
        base = [(r.uniform(-25, -15), r.uniform(-55, -45)) for _ in range(20)]
        pontos = base + [base[i] for i in range(10)]
        for minimo in (0.0, 0.5, 5.0, 50.0):
            esperado, _ = referencia(pontos, minimo)
            obtido, _ = par_mais_proximo(pontos, minimo)
            self.assertAlmostEqual(obtido, esperado, places=9,
                                   msg=f"mínimo de {minimo} km")

    def test_limiar_alto_demais_nao_deixa_par_nenhum(self):
        pontos = [(-15.8, -47.9), (-15.9, -47.9)]
        d, par = par_mais_proximo(pontos, minimo_km=10_000.0)
        self.assertEqual(d, float("inf"))
        self.assertIsNone(par)


class TestMetricaProjetada(unittest.TestCase):

    def _menor_haversine(self, pontos):
        return min(distancia_km(*pontos[i], *pontos[j])
                   for i, j in itertools.combinations(range(len(pontos)), 2))

    def test_na_escala_que_interessa_acha_o_par_certo(self):
        for semente in range(20):
            r = random.Random(semente)
            pontos = [(-15.8 + r.uniform(-0.05, 0.05),
                       -47.9 + r.uniform(-0.05, 0.05)) for _ in range(50)]
            obtido, _ = par_mais_proximo(pontos)
            self.assertAlmostEqual(obtido, self._menor_haversine(pontos),
                                   places=9, msg=f"semente {semente}")

    def test_espalhado_pelo_pais_a_projecao_cobra_um_preco(self):
        pior = 0.0
        for semente in range(50):
            r = random.Random(semente)
            pontos = [(r.uniform(-33.0, 5.0), r.uniform(-73.0, -34.0))
                      for _ in range(60)]
            obtido, _ = par_mais_proximo(pontos)
            verdade = self._menor_haversine(pontos)
            pior = max(pior, (obtido - verdade) / verdade)
        self.assertLess(pior, 0.06)
        self.assertGreater(pior, 0.0)


if __name__ == "__main__":
    unittest.main()
