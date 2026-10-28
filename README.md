# Par de Pontos mais Próximos na base do CNES

**Número do Grupo:** 31 &nbsp;·&nbsp; **Conteúdo da Disciplina:** Dividir e Conquistar

Entre os 46 mil estabelecimentos de saúde do Brasil, quais dois serviços
distintos estão mais perto um do outro?

## Alunos

| Matrícula | Aluno |
| --- | --- |
| 222006534 | Anna Clara Cardoso Evangelista Brandão |
| 231026699 | Eduarda Domingos Rodrigues |

## Sobre

A base do CNES tem **46.059 estabelecimentos de saúde com coordenada válida** no
Brasil. A pergunta ingênua — quais dois pontos estão mais perto — tem resposta
decepcionante: **zero metros**, porque há cadastros repetidos na mesma
coordenada. E para achar isso não é preciso algoritmo nenhum: uma tabela hash
resolve em centésimos de segundo.

A pergunta que exige o algoritmo é outra: **qual o par mais próximo acima de um
limiar**. Aí não basta saber se dois pontos são iguais, é preciso saber qual é o
mais próximo — e a força bruta levaria mais de mil milhões de comparações.

## Os dados

O arquivo bruto não é versionado. Baixe o CSV do CNES e salve como
`data/raw/Unidades_Basicas_Saude-UBS.csv`:

<https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs>

Conferência — `python -m src.dados` deve imprimir:

| | |
| --- | --- |
| Registros no Brasil | 47.983 |
| **Com coordenada válida** | **46.059** |
| Unidades da federação | 27 |
| Coordenadas repetidas | 486, envolvendo 1.254 registros |
| Maior empilhamento | 33 estabelecimentos no mesmo ponto |

**Armadilha do separador decimal.** A coluna `LATITUDE` usa ponto e a `LONGITUDE`
usa vírgula, no arquivo nacional inteiro. Sem trocar a vírgula por ponto, todo
`float()` de longitude estoura. Tem teste próprio.

**A base só traz códigos.** `UF` e `IBGE` são códigos numéricos, não nomes. Para
escrever o nome do estado ou do município é preciso cruzar com a tabela do IBGE.

## A geometria

O algoritmo clássico é **plano e euclidiano**; a Terra não é. Projetamos com

```
x = longitude × cos(latitude de referência) × 111
y = latitude × 111
```

onde a latitude de referência é a média do conjunto.

**O cosseno é da referência, não de cada ponto.** Essa distinção não é detalhe:
usando o cosseno da latitude de cada ponto, a coordenada `x` passa a depender da
latitude, e como a longitude no Brasil vale cerca de −48, andar um grau para o
sul desloca o ponto 25 km para o lado no mapa. Medimos o estrago: **11% de erro
na distância, em qualquer escala**. Com a latitude de referência o erro some.

**O que isso custa.** Numa nuvem de poucos quilômetros — a escala em que as
respostas deste trabalho acontecem — o par escolhido é exatamente o mesmo que a
distância de haversine escolheria: medimos erro **zero**. Espalhando pontos pelo
país inteiro, a projeção chega a errar **4,9%** e pode trocar o par vencedor. A
resposta final é sempre reportada em haversine, a distância de verdade sobre a
esfera.

## O algoritmo

*(seção a ser detalhada)*

## A extensão: Contagem de Inversões

*(seção da Eduarda)*

## A força bruta e a validação

*(seção da Eduarda)*

## Instalação

Requer **Python 3.10 ou mais novo**. Os comandos rodam da raiz do repositório.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Uso

```bash
python -m src.dados                 # confere o carregamento da base
python -m src.par_proximo           # o par mais próximo, sem limiar
python -m src.par_proximo 0.001     # o par mais próximo acima de 1 metro
```

## Testes

```bash
python -m unittest discover
```

Os que dependem do arquivo bruto são pulados quando ele não está em `data/raw/`,
então a suíte roda num clone recém-feito, sem download.

## Apresentação

`<link do vídeo>`

## Trabalho anterior do grupo

A distância de haversine e a leitura do CSV do CNES vêm do nosso trabalho de
Algoritmos Gulosos, em
[G31_Greedy_PA-26.2](https://github.com/projeto-de-algoritmos-2026/G31_Greedy_PA-26.2).
Aqui a base é usada inteira, e não só a parte do Distrito Federal.

## Referências

- KLEINBERG, J.; TARDOS, É. *Algorithm Design*, cap. 5 — Divide and Conquer.
- CORMEN, T. H. et al. *Introduction to Algorithms*, 3. ed., cap. 4 e 33.4.
- [Estabelecimentos de saúde — Portal de Dados Abertos do SUS](https://dadosabertos.saude.gov.br/dataset/unidades-basicas-de-saude-ubs)
