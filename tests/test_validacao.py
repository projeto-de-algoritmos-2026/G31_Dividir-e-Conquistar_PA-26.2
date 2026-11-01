import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from src.validacao import (COR_DIVIDIR, COR_FORCA_BRUTA, _decimal, _milhar,
                           comparar_com_hash, cronometrar, curva_de_tempo,
                           gerar_sintetico, repetidas_por_hash, salvar_csv,
                           svg_da_curva, tabela_de_limiares,
                           tamanhos_da_curva)


class TestCronometrar(unittest.TestCase):

    def test_devolve_o_tempo_e_o_resultado(self):
        t, r = cronometrar(sum, [1, 2, 3])
        self.assertEqual(r, 6)
        self.assertGreaterEqual(t, 0.0)


class TestTamanhosDaCurva(unittest.TestCase):

    def test_o_ultimo_e_o_total(self):
        self.assertEqual(tamanhos_da_curva(46059, 10)[-1], 46059)

    def test_sao_crescentes(self):
        t = tamanhos_da_curva(46059, 10)
        self.assertEqual(t, sorted(t))
        self.assertEqual(len(t), len(set(t)))

    def test_nenhum_passa_do_total(self):
        for n in (50, 1000, 46059):
            for passos in (2, 5, 10):
                with self.subTest(n=n, passos=passos):
                    self.assertLessEqual(max(tamanhos_da_curva(n, passos)), n)

    def test_total_menor_que_o_menor_nao_estoura(self):
        self.assertTrue(tamanhos_da_curva(10, 5))


class TestRepetidasPorHash(unittest.TestCase):

    def test_sem_repetidas(self):
        pos, regs, maior = repetidas_por_hash([(0.0, 0.0), (1.0, 1.0)])
        self.assertEqual((pos, regs), (0, 0))
        self.assertLessEqual(maior, 1)

    def test_conta_posicoes_registros_e_o_maior_empilhamento(self):
        pontos = [(0.0, 0.0)] * 3 + [(1.0, 1.0)] * 2 + [(2.0, 2.0)]
        pos, regs, maior = repetidas_por_hash(pontos)
        self.assertEqual(pos, 2)
        self.assertEqual(regs, 5)
        self.assertEqual(maior, 3)

    def test_o_hash_e_o_dividir_concordam_em_haver_duplicata(self):
        """
        O argumento central do trabalho: para achar duplicata o hash basta, e
        quando ele acha alguma o dividir-e-conquistar tem de dar zero metros.
        """
        r = comparar_com_hash([(0.0, 0.0), (0.0, 0.0), (5.0, 5.0)])
        self.assertEqual(r["coordenadas_repetidas"], 1)
        self.assertEqual(r["registros"], 2)
        self.assertEqual(r["maior_empilhamento"], 2)
        self.assertAlmostEqual(r["distancia_dc_m"], 0.0)

    def test_sem_duplicata_o_hash_nao_acha_nada_e_a_distancia_e_positiva(self):
        r = comparar_com_hash([(0.0, 0.0), (1.0, 1.0), (5.0, 5.0)])
        self.assertEqual(r["coordenadas_repetidas"], 0)
        self.assertEqual(r["registros"], 0)
        self.assertGreater(r["distancia_dc_m"], 0.0)


class TestTabelaDeLimiares(unittest.TestCase):

    def test_um_registro_por_limiar(self):
        pontos = gerar_sintetico(300, semente=1)
        linhas = tabela_de_limiares(pontos, limiares_m=(1.0, 10.0))
        self.assertEqual(len(linhas), 2)

    def test_limiar_maior_nunca_da_distancia_menor(self):
        pontos = gerar_sintetico(400, semente=2)
        pontos += [pontos[0], pontos[1], pontos[2]]
        linhas = tabela_de_limiares(pontos, limiares_m=(1.0, 10.0, 100.0))
        distancias = [l["distancia_m"] for l in linhas if l["distancia_m"] is not None]
        self.assertEqual(len(distancias), 3)
        self.assertEqual(distancias, sorted(distancias))

    def test_cada_linha_traz_limiar_distancia_par_e_tempo(self):
        linhas = tabela_de_limiares(gerar_sintetico(200, semente=8),
                                    limiares_m=(1.0,))
        self.assertEqual(set(linhas[0]), {"limiar_m", "distancia_m", "par", "segundos"})


class TestGerarSintetico(unittest.TestCase):

    def test_devolve_a_quantidade_pedida(self):
        self.assertEqual(len(gerar_sintetico(250, semente=3)), 250)

    def test_a_semente_torna_reproduzivel(self):
        self.assertEqual(gerar_sintetico(50, semente=7),
                         gerar_sintetico(50, semente=7))

    def test_sementes_diferentes_dao_conjuntos_diferentes(self):
        self.assertNotEqual(gerar_sintetico(50, semente=1),
                            gerar_sintetico(50, semente=2))


class TestCurvaDeTempo(unittest.TestCase):

    def setUp(self):
        self.pontos = gerar_sintetico(600, semente=5)
        self.linhas = curva_de_tempo(self.pontos, [200, 400, 600],
                                     forca_bruta_ate=400)

    def test_uma_linha_por_tamanho(self):
        self.assertEqual(len(self.linhas), 3)

    def test_acima_do_limite_a_forca_bruta_nao_roda(self):
        acima = [l for l in self.linhas if l["n"] > 400]
        self.assertTrue(acima)
        for l in acima:
            self.assertIsNone(l.get("t_forca_bruta"))

    def test_abaixo_do_limite_as_duas_dao_a_mesma_distancia(self):
        for l in self.linhas:
            if l.get("t_forca_bruta") is None:
                continue
            with self.subTest(n=l["n"]):
                self.assertTrue(l.get("iguais", True), l)


class TestSvg(unittest.TestCase):

    def setUp(self):
        self.linhas = curva_de_tempo(gerar_sintetico(400, semente=4),
                                     [100, 250, 400], forca_bruta_ate=250)

    def test_e_xml_bem_formado(self):
        ET.fromstring(svg_da_curva(self.linhas, titulo="teste"))

    def test_a_versao_log_tambem(self):
        ET.fromstring(svg_da_curva(self.linhas, log=True, titulo="teste"))

    def test_as_duas_cores_aparecem(self):
        svg = svg_da_curva(self.linhas, titulo="teste")
        self.assertIn(COR_DIVIDIR, svg)
        self.assertIn(COR_FORCA_BRUTA, svg)


class TestFormatacao(unittest.TestCase):

    def test_milhar_usa_ponto(self):
        self.assertEqual(_milhar(46059), "46.059")
        self.assertEqual(_milhar(27), "27")

    def test_decimal_usa_virgula(self):
        self.assertIn(",", _decimal(1.02))
        self.assertNotIn(".", _decimal(1.02))


class TestSalvarCsv(unittest.TestCase):

    def test_grava_um_arquivo_legivel(self):
        linhas = curva_de_tempo(gerar_sintetico(200, semente=6), [100, 200],
                                forca_bruta_ate=200)
        with tempfile.TemporaryDirectory() as pasta:
            destino = Path(pasta) / "curva.csv"
            salvar_csv(linhas, destino)
            texto = destino.read_text(encoding="utf-8")
        self.assertIn("n", texto.splitlines()[0])
        self.assertEqual(len(texto.strip().splitlines()), len(linhas) + 1)


if __name__ == "__main__":
    unittest.main()
