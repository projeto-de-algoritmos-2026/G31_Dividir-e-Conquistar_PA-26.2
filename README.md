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

**A base só traz códigos.** `UF` e `IBGE` são códigos numéricos, não nomes.

Os **27 códigos de unidade da federação** estão em `src/dados.py`, e não vieram
de memória: conferimos cada um contra as coordenadas da própria base. Roraima e
Amapá são os dois únicos com latitude média positiva, o Acre é o mais a oeste, o
Rio Grande do Sul o mais ao sul, e o Distrito Federal tem exatamente 200
estabelecimentos — o mesmo número do nosso trabalho anterior. Tem teste próprio.

Os **nomes de município** não cabem no código: são 5.570. Se o arquivo
`data/municipios_ibge.csv` existir, com as colunas `codigo;nome` separadas por
ponto e vírgula, os nomes aparecem nas saídas; sem ele, sai o código. A tabela
está em <https://servicodados.ibge.gov.br/api/v1/localidades/municipios>.

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

A força bruta compara todos os pares: com 46.059 pontos são **1.060.692.711**
comparações. O dividir e conquistar resolve o mesmo problema em três passos.

**1. Dividir.** Ordena os pontos pela coordenada horizontal e corta no meio, com
uma linha vertical deixando metade dos pontos de cada lado.

**2. Conquistar.** Resolve cada metade recursivamente e guarda a menor das duas
distâncias encontradas. Chame ela de **d**.

**3. Combinar.** O par mais próximo ainda pode ter um ponto de cada lado — mas
só se os dois estiverem a menos de **d** da linha de corte. Basta olhar uma
faixa de largura `2d` em volta dela.

### Por que a faixa não custa caro

O passo 3 parece ser onde o algoritmo se perde: a faixa pode conter todos os
pontos. O que salva é a ordem.

Percorrendo a faixa **ordenada pela coordenada vertical**, cada ponto só precisa
ser comparado com os seguintes enquanto a diferença vertical for menor que
**d** — passou disso, nenhum ponto adiante pode formar par melhor, e a varredura
para.

E esse pedaço é curto. Considere o retângulo de `2d` por `d` à frente de um
ponto da faixa: como as duas metades já foram resolvidas, **não há dois pontos
do mesmo lado a menos de d um do outro**. Dividindo o retângulo em quadrados de
lado `d/2`, cada quadrado cabe no máximo um ponto, e são oito quadrados. Logo, no
máximo **sete vizinhos** a examinar por ponto. Sete é constante, a combinação
fica linear, e o total é **O(n log n)**.

### O limiar derruba esse argumento

Quando se pede o par mais próximo **acima de um limiar**, o `minimo_km`, aquele
raciocínio deixa de valer. Ele depende de não existirem dois pontos a menos de
**d** do mesmo lado — e é exatamente isso que o limiar permite: pares colados
são descartados da resposta, mas os pontos continuam lá, ocupando a faixa e
empurrando os vizinhos de verdade para fora da janela de sete.

Alargar a janela não conserta, porque o número de pontos que cabem no retângulo
deixa de ter limite fixo: depende de quão coladas as duplicatas estão. A solução
correta é **não ter janela**: a varredura para apenas pela diferença vertical,
que é o que de fato garante a corretude. Com dados sem duplicatas o efeito é o
mesmo, porque a parada acontece no sétimo vizinho de qualquer jeito.

O custo disso é que, numa base com muitos pontos empilhados, a faixa pode ficar
cara. Na base do CNES isso não acontece — as 46 mil comparações levam menos de
um segundo —, mas é uma limitação real e fica registrada aqui.

### Onde isso está

`src/par_proximo.py`. A função pública é

```
par_mais_proximo(pontos, minimo_km=0.0) -> (distancia_km, (i, j))
```

Ela recebe latitudes e longitudes, projeta, roda a recursão no plano e devolve
os índices do par junto com a distância **de haversine** entre eles — a
distância de verdade sobre a esfera, não a do plano.

O caso base da recursão é a própria força bruta, para três pontos ou menos. É a
mesma ideia que `src/forca_bruta.py` aplica à base inteira, e é o que permite
afirmar que os dois concordam.

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
