import tempfile
import unittest
from pathlib import Path

from src.dados import (ARQUIVO_CNES, UNIDADES_DA_FEDERACAO, Estabelecimento,
                       _milhar, _no_brasil, _numero, carregar,
                       carregar_municipios, coordenadas, local, nome_da_uf,
                       sigla_da_uf)

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


class TestUnidadesDaFederacao(unittest.TestCase):

    def test_sao_vinte_e_sete(self):
        self.assertEqual(len(UNIDADES_DA_FEDERACAO), 27)

    def test_traduz_codigo_em_sigla_e_nome(self):
        self.assertEqual(sigla_da_uf("53"), "DF")
        self.assertEqual(nome_da_uf("53"), "Distrito Federal")
        self.assertEqual(sigla_da_uf("22"), "PI")
        self.assertEqual(nome_da_uf("29"), "Bahia")

    def test_codigo_desconhecido_nao_estoura(self):
        self.assertEqual(sigla_da_uf("99"), "UF 99")
        self.assertEqual(nome_da_uf("99"), "UF 99")

    def test_nenhuma_sigla_se_repete(self):
        siglas = [s for s, _ in UNIDADES_DA_FEDERACAO.values()]
        self.assertEqual(len(siglas), len(set(siglas)))


class TestMunicipios(unittest.TestCase):

    def test_sem_a_tabela_devolve_vazio(self):
        self.assertEqual(carregar_municipios(Path("nao/existe.csv")), {})

    def test_le_a_tabela_quando_existe(self):
        pasta = tempfile.mkdtemp()
        caminho = Path(pasta) / "m.csv"
        caminho.write_text("codigo;nome\n221040;Picos\n530010;Brasília\n",
                           encoding="utf-8")
        tabela = carregar_municipios(caminho)
        self.assertEqual(tabela["221040"], "Picos")
        self.assertEqual(tabela["530010"], "Brasília")


class TestLocal(unittest.TestCase):

    def setUp(self):
        self.e = Estabelecimento("1", "UBS A", "", "22", "221040", -7.0, -41.4)

    def test_sem_tabela_mostra_o_codigo_mas_nomeia_o_estado(self):
        self.assertEqual(local(self.e), "município 221040, PI")

    def test_com_tabela_mostra_o_nome(self):
        self.assertEqual(local(self.e, {"221040": "Picos"}), "Picos, PI")

    def test_tabela_sem_aquele_codigo_cai_no_codigo(self):
        self.assertEqual(local(self.e, {"530010": "Brasília"}),
                         "município 221040, PI")


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

    def test_todo_codigo_de_uf_da_base_esta_na_tabela(self):
        for e in self.estabelecimentos:
            self.assertIn(e.uf, UNIDADES_DA_FEDERACAO, e.nome)

    def test_o_codigo_ibge_comeca_pelo_codigo_da_uf(self):
        for e in self.estabelecimentos:
            self.assertTrue(e.ibge.startswith(e.uf), f"{e.nome}: {e.ibge}/{e.uf}")

    def test_cada_uf_cai_onde_o_estado_fica(self):
        import collections
        pontos = collections.defaultdict(list)
        for e in self.estabelecimentos:
            pontos[e.uf].append((e.lat, e.lon))

        def media_lat(uf):
            return sum(p[0] for p in pontos[uf]) / len(pontos[uf])

        def media_lon(uf):
            return sum(p[1] for p in pontos[uf]) / len(pontos[uf])

        self.assertGreater(media_lat("14"), 0.0)
        self.assertGreater(media_lat("16"), 0.0)
        self.assertLess(media_lat("43"), media_lat("35"))
        self.assertLess(media_lat("35"), media_lat("29"))
        self.assertLess(media_lat("29"), media_lat("23"))
        self.assertLess(media_lon("12"), media_lon("53"))
        self.assertLess(media_lon("53"), media_lon("24"))
        self.assertAlmostEqual(media_lat("53"), -15.83, delta=0.2)
        self.assertEqual(len(pontos["53"]), 200)


if __name__ == "__main__":
    unittest.main()
