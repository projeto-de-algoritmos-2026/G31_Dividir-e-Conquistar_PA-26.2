import unittest
from pathlib import Path

from src.geometria import centroide
from src.setores import ARQUIVO_SETORES, Setor, carregar_setores


def _tem_pyshp() -> bool:
    try:
        import shapefile  # noqa: F401
    except ImportError:
        return False
    return True


TEM_DADOS = ARQUIVO_SETORES.with_suffix(".shp").exists() and _tem_pyshp()


class TestCentroide(unittest.TestCase):

    def test_quadrado_tem_centro_no_meio(self):
        quadrado = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
        x, y = centroide(quadrado)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 1.0)

    def test_triangulo_tem_centro_na_media_dos_vertices(self):
        triangulo = [(0, 0), (3, 0), (0, 3), (0, 0)]
        x, y = centroide(triangulo)
        self.assertAlmostEqual(x, 1.0)
        self.assertAlmostEqual(y, 1.0)

    def test_a_ordem_dos_vertices_nao_muda_o_centro(self):
        horario = [(0, 0), (0, 2), (2, 2), (2, 0), (0, 0)]
        anti = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0)]
        self.assertEqual(centroide(horario), centroide(anti))

    def test_poligono_degenerado_cai_na_media_dos_pontos(self):
        linha = [(0, 0), (2, 0), (4, 0), (0, 0)]
        x, y = centroide(linha)
        self.assertAlmostEqual(y, 0.0)
        self.assertAlmostEqual(x, 1.5)

    def test_sem_pontos_e_erro(self):
        with self.assertRaises(ValueError):
            centroide([])

    def test_dois_aneis_sao_tratados_juntos(self):
        pontos = [(0, 0), (2, 0), (2, 2), (0, 2), (0, 0),
                  (10, 10), (12, 10), (12, 12), (10, 12), (10, 10)]
        x, y = centroide(pontos, inicios=[0, 5])
        self.assertGreater(x, 1.0)
        self.assertGreater(y, 1.0)


class TestArquivoAusente(unittest.TestCase):

    def test_shapefile_ausente_e_erro(self):
        with self.assertRaises((FileNotFoundError, ImportError)):
            carregar_setores(Path("nao/existe"))


@unittest.skipUnless(TEM_DADOS, "shapefile do IBGE ou pyshp ausentes")
class TestComDadosReais(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.setores = carregar_setores()

    def test_a_quantidade_esperada(self):
        self.assertEqual(len(self.setores), 5418)

    def test_a_populacao_do_censo(self):
        self.assertEqual(sum(s.populacao for s in self.setores), 2_817_381)

    def test_urbanos_e_rurais(self):
        rurais = sum(1 for s in self.setores if not s.urbano)
        self.assertEqual(rurais, 397)
        self.assertEqual(len(self.setores) - rurais, 5021)

    def test_as_regioes_administrativas(self):
        self.assertEqual(len({s.regiao for s in self.setores}), 33)

    def test_todo_centroide_cai_dentro_do_df(self):
        for s in self.setores:
            self.assertTrue(-16.10 <= s.lat <= -15.45, s.codigo)
            self.assertTrue(-48.35 <= s.lon <= -47.25, s.codigo)

    def test_nenhuma_populacao_negativa(self):
        for s in self.setores:
            self.assertGreaterEqual(s.populacao, 0, s.codigo)

    def test_sao_do_tipo_setor(self):
        self.assertIsInstance(self.setores[0], Setor)


if __name__ == "__main__":
    unittest.main()
