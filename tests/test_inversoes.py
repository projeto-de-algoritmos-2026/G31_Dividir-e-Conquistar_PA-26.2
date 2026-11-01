import itertools
import random
import unittest

from src.inversoes import (comparar_rankings, contar_inversoes,
                           distancia_ate_a_mais_proxima)


def inversoes_na_marra(valores):
    return sum(1 for i, j in itertools.combinations(range(len(valores)), 2)
               if valores[i] > valores[j])


class TestContarInversoes(unittest.TestCase):

    def test_lista_vazia_ou_de_um_nao_tem_inversao(self):
        self.assertEqual(contar_inversoes([]), 0)
        self.assertEqual(contar_inversoes([7]), 0)

    def test_ordenada_nao_tem_inversao(self):
        self.assertEqual(contar_inversoes([1, 2, 3, 4, 5]), 0)

    def test_invertida_tem_todas(self):
        self.assertEqual(contar_inversoes([5, 4, 3, 2, 1]), 10)

    def test_empates_nao_contam(self):
        self.assertEqual(contar_inversoes([2, 2, 2, 2]), 0)
        self.assertEqual(contar_inversoes([1, 1, 0]), 2)

    def test_o_exemplo_do_slide(self):
        self.assertEqual(contar_inversoes([1, 3, 4, 2, 5]), 2)

    def test_bate_com_a_contagem_na_marra(self):
        for semente in range(20):
            r = random.Random(semente)
            v = [r.randrange(12) for _ in range(r.randrange(2, 40))]
            with self.subTest(semente=semente):
                self.assertEqual(contar_inversoes(v), inversoes_na_marra(v))

    def test_nao_estoura_a_pilha_com_lista_grande(self):
        r = random.Random(1)
        v = [r.random() for _ in range(20_000)]
        self.assertGreater(contar_inversoes(v), 0)


class TestCompararRankings(unittest.TestCase):

    def test_tamanhos_diferentes_sao_erro(self):
        with self.assertRaises(ValueError):
            comparar_rankings([1, 2, 3], [1, 2])

    def test_concordancia_total_nao_tem_discordante(self):
        # mais população, menos distância
        r = comparar_rankings([100, 50, 10], [1.0, 2.0, 3.0])
        self.assertEqual(r.discordantes, 0)
        self.assertEqual(r.fracao_discordante, 0.0)

    def test_discordancia_total(self):
        # mais população, mais distância
        r = comparar_rankings([100, 50, 10], [3.0, 2.0, 1.0])
        self.assertEqual(r.discordantes, r.comparaveis)
        self.assertEqual(r.fracao_discordante, 1.0)

    def test_conta_os_pares(self):
        r = comparar_rankings([1, 2, 3, 4], [1.0, 2.0, 3.0, 4.0])
        self.assertEqual(r.n, 4)
        self.assertEqual(r.pares, 6)

    def test_empate_de_populacao_sai_da_conta(self):
        r = comparar_rankings([10, 10, 10], [1.0, 2.0, 3.0])
        self.assertEqual(r.empatados, 3)
        self.assertEqual(r.comparaveis, 0)
        self.assertEqual(r.fracao_discordante, 0.0)

    def test_concordantes_mais_discordantes_fecham_os_comparaveis(self):
        for semente in range(20):
            r = random.Random(semente)
            n = r.randrange(2, 30)
            pop = [r.randrange(5) for _ in range(n)]
            dist = [float(r.randrange(5)) for _ in range(n)]
            c = comparar_rankings(pop, dist)
            with self.subTest(semente=semente):
                self.assertEqual(c.concordantes + c.discordantes, c.comparaveis)
                self.assertLessEqual(c.comparaveis, c.pares)
                self.assertGreaterEqual(c.concordantes, 0)

    def test_lista_de_um_elemento_nao_divide_por_zero(self):
        c = comparar_rankings([5], [1.0])
        self.assertEqual(c.pares, 0)
        self.assertEqual(c.fracao_discordante, 0.0)
        self.assertEqual(c.fracao_sobre_pares, 0.0)


class TestDistanciaAteAMaisProxima(unittest.TestCase):

    def test_sem_unidade_e_erro(self):
        with self.assertRaises(ValueError):
            distancia_ate_a_mais_proxima([(-15.8, -47.9)], [])

    def test_ponto_em_cima_da_unidade_da_zero(self):
        d = distancia_ate_a_mais_proxima([(-15.8, -47.9)], [(-15.8, -47.9)])
        self.assertAlmostEqual(d[0], 0.0)

    def test_pega_a_mais_perto_e_nao_a_primeira(self):
        d = distancia_ate_a_mais_proxima(
            [(-15.80, -47.90)],
            [(-20.00, -50.00), (-15.81, -47.90), (-25.00, -45.00)])
        self.assertLess(d[0], 2.0)

    def test_devolve_um_valor_por_ponto_na_mesma_ordem(self):
        pontos = [(-15.8, -47.9), (-16.5, -47.9), (-10.0, -40.0)]
        d = distancia_ate_a_mais_proxima(pontos, [(-15.8, -47.9)])
        self.assertEqual(len(d), 3)
        self.assertAlmostEqual(d[0], 0.0)
        self.assertLess(d[1], d[2])


if __name__ == "__main__":
    unittest.main()
