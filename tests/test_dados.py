import tempfile
import unittest
from pathlib import Path

from src.dados import (ARQUIVO_CNES, Estabelecimento, _milhar, _no_brasil,
                       _numero, carregar, coordenadas)

TEM_DADOS = ARQUIVO_CNES.exists()

CABECALHO = "CNES;UF;IBGE;NOME;LOGRADOURO;BAIRRO;LATITUDE;LONGITUDE"


def arquivo_com(linhas):
    pasta = tempfile.mkdtemp()
    caminho = Path(pasta) / "cnes.csv"
    caminho.write_text("\n".join([CABECALHO] + linhas), encoding="utf-8")
    return caminho


class TestNumero(unittest.TestCase):

    def test_ponto_decimal(self):
        self.assertAlmostEqual(_numero("-15.8"), -15.8)

    def test_virgula_decimal(self):
        self.assertAlmostEqual(_numero("-47,9"), -47.9)

    def test_vazio_e_nulo(self):
        self.assertIsNone(_numero(""))
        self.assertIsNone(_numero("   "))
        self.assertIsNone(_numero(None))

    def test_texto_que_nao_e_numero_e_nulo(self):
        self.assertIsNone(_numero("sem informacao"))


class TestNoBrasil(unittest.TestCase):

    def test_brasilia_esta_dentro(self):
        self.assertTrue(_no_brasil(-15.8, -47.9))

    def test_lisboa_esta_fora(self):
        self.assertFalse(_no_brasil(38.7, -9.1))

    def test_zero_zero_esta_fora(self):
        self.assertFalse(_no_brasil(0.0, 0.0))


class TestCarregar(unittest.TestCase):

    def test_le_a_virgula_da_longitude(self):
        caminho = arquivo_com(["1;53;530010;UBS A;rua;centro;-15.8;-47,9"])
        e = carregar(caminho)[0]
        self.assertAlmostEqual(e.lat, -15.8)
        self.assertAlmostEqual(e.lon, -47.9)

    def test_descarta_sem_coordenada(self):
        caminho = arquivo_com([
            "1;53;530010;COM;rua;centro;-15.8;-47,9",
            "2;53;530010;SEM;rua;centro;;",
        ])
        nomes = [e.nome for e in carregar(caminho)]
        self.assertEqual(nomes, ["COM"])

    def test_descarta_coordenada_fora_do_brasil(self):
        caminho = arquivo_com([
            "1;53;530010;AQUI;rua;centro;-15.8;-47,9",
            "2;53;530010;LISBOA;rua;centro;38.7;-9,1",
        ])
        self.assertEqual([e.nome for e in carregar(caminho)], ["AQUI"])

    def test_guarda_os_codigos_como_texto(self):
        caminho = arquivo_com(["7;53;530010;UBS A;rua;centro;-15.8;-47,9"])
        e = carregar(caminho)[0]
        self.assertEqual(e.uf, "53")
        self.assertEqual(e.ibge, "530010")
        self.assertEqual(e.cnes, "7")

    def test_arquivo_ausente_e_erro(self):
        with self.assertRaises(FileNotFoundError):
            carregar(Path("nao/existe.csv"))


class TestMilhar(unittest.TestCase):

    def test_separa_milhar_com_ponto(self):
        self.assertEqual(_milhar(46059), "46.059")
        self.assertEqual(_milhar(1254), "1.254")

    def test_numero_pequeno_nao_ganha_separador(self):
        self.assertEqual(_milhar(27), "27")


class TestCoordenadas(unittest.TestCase):

    def test_devolve_pares_na_mesma_ordem(self):
        lista = [Estabelecimento("1", "A", "", "53", "530010", -15.8, -47.9),
                 Estabelecimento("2", "B", "", "53", "530010", -16.0, -48.0)]
        self.assertEqual(coordenadas(lista), [(-15.8, -47.9), (-16.0, -48.0)])


@unittest.skipUnless(TEM_DADOS, "base bruta ausente")
class TestComDadosReais(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.estabelecimentos = carregar()

    def test_a_quantidade_esperada(self):
        self.assertEqual(len(self.estabelecimentos), 46059)

    def test_todas_as_unidades_da_federacao(self):
        self.assertEqual(len({e.uf for e in self.estabelecimentos}), 27)

    def test_toda_coordenada_cai_dentro_do_brasil(self):
        for e in self.estabelecimentos:
            self.assertTrue(_no_brasil(e.lat, e.lon), e.nome)


if __name__ == "__main__":
    unittest.main()
