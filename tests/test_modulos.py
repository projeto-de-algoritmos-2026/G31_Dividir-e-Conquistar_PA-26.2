import importlib
import pkgutil
import unittest
from pathlib import Path

import src

RAIZ = Path(__file__).resolve().parent.parent

MODULOS = sorted(m.name for m in pkgutil.iter_modules(src.__path__))


class TestTodoModuloImporta(unittest.TestCase):
    """
    O bug que este arquivo existe para impedir.

    Em 29/10 o repositório ficou com `src/inversoes.py` importando um
    `src/setores.py` que não existia, e `src/validacao.py` e `app.py`
    importando um `src/ufs.py` que também não existia. A suíte passava
    assim, porque nenhum teste importava aqueles módulos.
    """

    def test_a_lista_de_modulos_nao_esta_vazia(self):
        self.assertGreater(len(MODULOS), 4, MODULOS)

    def test_todo_modulo_de_src_importa(self):
        for nome in MODULOS:
            with self.subTest(modulo=nome):
                importlib.import_module(f"src.{nome}")

    def test_todo_arquivo_py_da_raiz_compila(self):
        for arquivo in sorted(RAIZ.glob("*.py")):
            with self.subTest(arquivo=arquivo.name):
                compile(arquivo.read_text(encoding="utf-8"), str(arquivo), "exec")

    def test_todo_import_de_src_aponta_para_modulo_existente(self):
        import ast

        alvos = [p for p in RAIZ.glob("*.py")]
        alvos += [p for p in (RAIZ / "src").glob("*.py")]
        alvos += [p for p in (RAIZ / "tests").glob("*.py")]

        existentes = set(MODULOS)
        for arquivo in sorted(alvos):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"), str(arquivo))
            for no in ast.walk(arvore):
                if isinstance(no, ast.ImportFrom) and (no.module or "").startswith("src"):
                    partes = no.module.split(".")
                    if len(partes) == 2:
                        with self.subTest(arquivo=arquivo.name, modulo=no.module):
                            self.assertIn(partes[1], existentes)
                    elif len(partes) == 1:
                        for alias in no.names:
                            with self.subTest(arquivo=arquivo.name, nome=alias.name):
                                self.assertIn(alias.name, existentes)


if __name__ == "__main__":
    unittest.main()
