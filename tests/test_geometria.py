import math
import unittest

from src.geometria import (KM_POR_GRAU, distancia_km, distancia_plana,
                           latitude_de_referencia, projetar, projetar_todos)


class TestDistanciaKm(unittest.TestCase):

    def test_ponto_consigo_mesmo_e_zero(self):
        self.assertAlmostEqual(distancia_km(-15.8, -47.9, -15.8, -47.9), 0.0)

    def test_um_grau_de_latitude_sao_cento_e_onze_km(self):
        d = distancia_km(0.0, 0.0, 1.0, 0.0)
        self.assertAlmostEqual(d, 111.19, delta=0.1)

    def test_um_grau_de_longitude_encolhe_longe_do_equador(self):
        no_equador = distancia_km(0.0, 0.0, 0.0, 1.0)
        no_df = distancia_km(-15.8, -47.9, -15.8, -46.9)
        self.assertGreater(no_equador, no_df)
        self.assertAlmostEqual(no_df, 107.0, delta=0.5)

    def test_a_distancia_e_simetrica(self):
        a = distancia_km(-15.8, -47.9, -23.5, -46.6)
        b = distancia_km(-23.5, -46.6, -15.8, -47.9)
        self.assertAlmostEqual(a, b)


class TestProjecao(unittest.TestCase):

    def test_latitude_vira_km_direto(self):
        _, y = projetar(10.0, 0.0, lat_referencia=0.0)
        self.assertAlmostEqual(y, 10.0 * KM_POR_GRAU)

    def test_longitude_encolhe_pelo_cosseno_da_referencia(self):
        x_equador, _ = projetar(0.0, 1.0, lat_referencia=0.0)
        x_sul, _ = projetar(0.0, 1.0, lat_referencia=-30.0)
        self.assertAlmostEqual(x_equador, KM_POR_GRAU)
        self.assertAlmostEqual(x_sul, KM_POR_GRAU * math.cos(math.radians(30)))

    def test_a_latitude_nao_desloca_o_ponto_no_eixo_x(self):
        x1, _ = projetar(-15.0, -47.9, lat_referencia=-15.8)
        x2, _ = projetar(-16.0, -47.9, lat_referencia=-15.8)
        self.assertAlmostEqual(x1, x2)

    def test_a_referencia_e_a_latitude_media(self):
        self.assertAlmostEqual(
            latitude_de_referencia([(-10.0, 0.0), (-20.0, 0.0)]), -15.0)

    def test_projeta_a_lista_inteira(self):
        pts = [(0.0, 0.0), (1.0, 1.0)]
        self.assertEqual(len(projetar_todos(pts)), 2)

    def test_em_distancias_curtas_a_projecao_concorda_com_haversine(self):
        a, b = (-15.8000, -47.9000), (-15.8050, -47.9040)
        ref = latitude_de_referencia([a, b])
        plana = distancia_plana(projetar(*a, ref), projetar(*b, ref))
        esfera = distancia_km(*a, *b)
        self.assertLess(abs(plana - esfera) / esfera, 0.01)


class TestDistanciaPlana(unittest.TestCase):

    def test_triangulo_de_lados_tres_e_quatro(self):
        self.assertAlmostEqual(distancia_plana((0, 0), (3, 4)), 5.0)

    def test_ponto_consigo_mesmo_e_zero(self):
        self.assertAlmostEqual(distancia_plana((2, 7), (2, 7)), 0.0)


if __name__ == "__main__":
    unittest.main()
