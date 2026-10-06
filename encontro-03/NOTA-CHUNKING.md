# Nota de chunking · Equipe: VanAntonietti

Caso: (x) Aurora  ( ) domínio próprio: ____________

Modelo de embeddings: `intfloat/multilingual-e5-small` (local, prefixos `query:`/`passage:`). Placar: `casos.json`, 16 casos medidos + 3 sem resposta. Todas as rodadas estão no `02-hands-on-chunking.ipynb` executado.

## 1. O que adotamos

- **Estratégia de chunking:** por estrutura (`MarkdownHeaderTextSplitter` nos `##`), com prefixo "Título > Seção" em cada chunk. 90 chunks, mediana de 194 caracteres.
- **Busca:** híbrida (vetor + BM25, fundidos por Reciprocal Rank Fusion), buscando `k × 3` candidatos antes dos filtros.
- **Tratamento de versões e de autoridade:** filtro `autoridade = oficial` no índice e, nos candidatos, `so_a_versao_vigente` (para cada `politica`, só a página com a `vigencia` mais recente).
- **k:** 3 trechos para o agente (ver o teste de k na seção 2).

## 2. Por quê

Tabela gerada pelo passo 4 do notebook (formato: achou/casos, contaminados entre parênteses):

| configuração | normal | excecao | conflito | termo-exato | autoridade | total |
|---|---|---|---|---|---|---|
| base: tamanho 400 · vetor | 7/7 (0) | 2/2 (1) | 2/3 (3) | 3/3 (1) | 1/1 (0) | 15/16 (5) |
| tamanho 800/100 · vetor | 7/7 (0) | 2/2 (0) | 3/3 (2) | 3/3 (0) | 1/1 (0) | 16/16 (2) |
| estrutura · vetor | 6/7 (0) | 2/2 (0) | 2/3 (3) | 3/3 (0) | 1/1 (0) | 14/16 (3) |
| estrutura sem prefixo · vetor | 5/7 (0) | 2/2 (0) | 2/3 (3) | 2/3 (1) | 1/1 (0) | 12/16 (4) |
| estrutura · bm25 | 5/7 (0) | 2/2 (0) | 1/3 (3) | 3/3 (0) | 1/1 (0) | 12/16 (3) |
| estrutura · híbrida | 6/7 (0) | 2/2 (0) | 1/3 (3) | 3/3 (0) | 1/1 (0) | 13/16 (3) |
| estrutura · híbrida · vigente | 6/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | 15/16 (0) |
| **estrutura · híbrida · vigente · oficial** | 6/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | **15/16 (0)** |
| estrutura · vetor · vigente · oficial | 6/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | 15/16 (0) |

O que os números dizem:

- **"Achou" engana; "contaminou" é o que custa.** A linha de base acha 15/16, mas contamina 5: em E2 a regra dos R$ 110 vem antes da exceção dos R$ 160; em C1, C2 e C3 a política de 2024 (2 dias, R$ 80) vem antes da vigente; em T1 o chunk do erro 720 vem antes do 809. Um agente que recebe esses três trechos responde errado com fonte citada. Tamanho 800/100 acha 16/16, mas ainda contamina 2 (C1, C3): chunk maior resolve a exceção cortada ao meio, não resolve versão velha.
- **Estrutura zera a contaminação de exceção e de termo exato** (E e T passam a 0), porque a cláusula 5.3 fica inteira na seção "5. Alimentação" e o chunk "Erro 809" começa com o próprio código. O prefixo "Título > Seção" vale 2 casos: sem ele a busca cai de 14/16 para 12/16 e T1 volta a contaminar, porque o chunk "Ative o Modo TCP 443..." não diz de que erro é.
- **Nenhum corte e nenhuma busca resolve conflito de versão.** Estrutura, BM25 e híbrida ficam em 3 contaminados em "conflito". A página de 2024 fala "home office" em toda frase e a vigente fala "trabalho remoto": por similaridade, a velha é a melhor resposta. Isso é dado (metadado `vigencia`), não modelo: ao ligar `so_vigente`, conflito vai de 1/3 (3) para 3/3 (0) e o total de 13/16 (3) para 15/16 (0).
- **`so_oficial` não mudou o placar aqui**, porque o guia de integração (`autoridade: resumo`) já perdia por posição para a página de Benefícios em A1. Mantemos o filtro mesmo assim: é o que impede o R$ 42 de voltar quando a página oficial for reescrita ou quando o guia ganhar mais texto. É proteção, não ganho de recall.
- **Híbrida vs. vetor:** nesta wiki, com o prefixo de título, o vetor sozinho empata (15/16, 0). Escolhemos a híbrida pelo caso de uso, não pelo placar: códigos de erro, categorias de plano (AUR-S2) e números de cláusula são exatamente o que o embedding de 384 dimensões não distingue (a Etapa 3 do notebook 01 mostra "Erro 809" e "Erro 812" com similaridade alta entre si). O BM25 sozinho é o pior (12/16): perde N4 e N5 porque a pergunta não repete as palavras da política.
- **k:** com k=1 a melhor configuração cai para 13/16 (2): só um trecho não cobre pergunta que precisa de duas cláusulas. Com k=5 vai a 16/16 (0) e o N5 entra. Ficamos em k=3 porque k=5 passa 5 trechos de até 650 caracteres a cada busca do agente, e o ganho é um único caso que preferimos resolver na ingestão (seção 3).

| configuração | normal | excecao | conflito | termo-exato | autoridade | total |
|---|---|---|---|---|---|---|
| melhor · k=1 | 6/7 (0) | 2/2 (0) | 1/3 (2) | 3/3 (0) | 1/1 (0) | 13/16 (2) |
| melhor · k=3 | 6/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | 15/16 (0) |
| melhor · k=5 | 7/7 (0) | 2/2 (0) | 3/3 (0) | 3/3 (0) | 1/1 (0) | 16/16 (0) |

Para ir além: o reranker `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` sobre 10 candidatos da melhor configuração deu o mesmo 15/16 (0) e a mesma falha. Ele reordena o que a busca trouxe; não corrige chunk que perdeu contexto nem decide versão.

## 3. O que ela não resolve

**Caso N5 ("Roubaram meu notebook do trabalho. O que eu faço?")**, esperado "anexe o boletim de ocorrência" em `ti-equipamentos`. Na configuração adotada o chunk certo (`ti-equipamentos#1`, seção "1. Defeito, quebra, perda ou roubo") fica em 5º lugar. O que vem antes: a devolução de equipamentos no desligamento, a introdução da página de equipamentos, o erro 720 da VPN ("certificado do notebook") e a seção de seguro.

**Causa: chunking.** O corte por seção deixou a cláusula 1.1 sem a palavra "notebook": ela só aparece na introdução da página (chunk #0) e na seção de seguro. A pergunta tem três termos úteis ("roubaram", "notebook", "trabalho") e o chunk certo não casa com nenhum: "roubaram" não bate com "roubo" porque o tokenizador do BM25 não faz stemming, e "notebook" bate com cinco outras páginas. Na linha de base por tamanho o caso passa, porque o corte juntou a introdução com a seção 1 no mesmo bloco. É a mesma moeda do ganho da estrutura: a cláusula fica inteira, mas perde o contexto que o autor deixou fora da seção.

**Onde tratar:** na ingestão, não na busca. Duas opções, em ordem de preferência: (1) incluir a introdução da página (o texto antes do primeiro `##`) no prefixo de cada chunk, junto com "Título > Seção", para que o assunto da página acompanhe a cláusula; (2) adicionar stemming leve (ou lematização) ao `tokenizar` do BM25, para que "roubaram" case "roubo". Subir k para 5 também resolve, mas pagando tokens em todas as perguntas por um caso.

**O que o placar não mede: S1, S2 e S3 (sem resposta).** A busca sempre devolve 3 chunks. Para "previdência privada" voltam licenças, seguro de vida e plano odontológico; para "pós-graduação" volta o auxílio home office. A nota do melhor chunk no vetor (0,829 a 0,867) se sobrepõe à de casos normais (N5 em 0,874, N7 em 0,875), então um corte por similaridade erraria casos normais antes de pegar os sem resposta. O "não sei" tem de ser decidido pelo agente, com os trechos na mão e as regras de resposta do Encontro 1 (responder só com fonte que sustente), e não por um limiar no retriever.

## 4. O que a ingestão precisa garantir

| Metadado | Quem preenche | Quando é atualizado | Se estiver errado |
|---|---|---|---|
| `politica` (chave que liga versões da mesma regra) | Dono da página (RH, TI, Benefícios, Financeiro), ao criar a página | A cada nova versão da política, que **precisa** reusar o mesmo valor | Duas versões com valores diferentes nunca disputam: `so_vigente` não as vê como a mesma política e a de 2024 volta a ser citada (C1, C2, C3 voltam a contaminar: 15/16 (0) → 13/16 (3)) |
| `vigencia` (data em que a página passou a valer) | Dono da página, com validação do formato AAAA-MM-DD na publicação | Quando a política é publicada ou substituída | Vazia ou com data futura/errada: a versão errada "vence" e o agente responde com a regra revogada, citando fonte oficial. Formato errado quebra o `max` por string silenciosamente |
| `autoridade` (`oficial` / `resumo` / `comunidade`) | Dono da página; o padrão de quem não preenche deveria ser `resumo`, não `oficial` (hoje o código assume `oficial`) | Quando um guia passa a resumir outras páginas, ou quando uma página resumida vira a fonte primária | Guia marcado como oficial volta a disputar com Benefícios: o c07 do Encontro 1 reaparece (R$ 42 contra R$ 45), e o agente precisa voltar a dizer "não sei" |
| `titulo` e seções `##` (viram o prefixo do chunk) | Autor da página, no template da wiki; a publicação deveria recusar página sem `#` e sem `##` | A cada edição | Sem seção, a página inteira vira um chunk de até 650+ caracteres; sem título no prefixo, o chunk "Ative o Modo TCP 443" não diz a que erro pertence (T1 contamina; placar 14/16 → 12/16) |
| `espaco` (filtro opcional da ferramenta `buscar_politicas`) | Automático pela pasta/espaço de origem na migração | Na migração e em moves de página | Página do Confluence antigo (`confluence-rh`) marcada como `wiki-rh` passa a entrar no filtro de espaço; hoje é inofensivo porque `vigencia` a elimina, mas é a segunda linha de defesa |

A ingestão também precisa de um teste de regressão: rodar este placar a cada reindexação. Uma página nova mal preenchida não dá erro; só muda um número na tabela.
