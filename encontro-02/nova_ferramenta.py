"""TODO 4 — Construir do zero: consultar_rede_credenciada.     (CONTRATO E IMPLEMENTAÇÃO)

Nas ferramentas 1 a 5, a implementação veio pronta e vocês escreveram o contrato.
Aqui não tem nada pronto: vocês escrevem as duas coisas.

O pedido do time de Benefícios
------------------------------
"Todo dia alguém pergunta se tal hospital ou laboratório atende pelo plano. A resposta
está na nossa planilha da rede credenciada, no Google Sheets. Queremos que o assistente
consulte a planilha."

O sistema: a planilha
---------------------
    SHEETS.ler("planilha-rede-credenciada", "prestadores")

devolve o mesmo formato da API do Google Sheets (spreadsheets.values.get):

    {"spreadsheetId": "planilha-rede-credenciada",
     "range": "prestadores!A1:L31",
     "majorDimension": "ROWS",
     "values": [
        ["prestador", "tipo", "especialidades", "cidade", "uf", "bairro", "telefone",
         "atende_24h", "situacao", "codigo_operadora", "valor_negociado_consulta",
         "observacao_interna"],                                            <- cabeçalho
        ["Hospital Jacarandá Paulista", "Hospital", "clínica geral; ...", "São Paulo", ...],
        ...
     ]}

Tudo vem como texto, e a planilha é mantida à mão desde 2021. Olhem os dados antes
de escrever qualquer linha:

    python encontro-02/nova_ferramenta.py          (a partir da raiz: imprime a planilha inteira)

Passo a passo
-------------
  4a. IMPLEMENTAÇÃO: escrevam consultar_rede_credenciada(). Decidam os parâmetros.
      Devolvam um dicionário com a lista de prestadores em "resultados" (um dicionário
      por prestador). Chaves fora de "resultados" também podem voltar ao modelo,
      se o contrato declarar (ex.: a fonte).
  4b. CONTRATO: preencham CONTRATO (descrição, schema, saída), como nos TODOs 1 a 3.
      Os parâmetros do schema precisam bater com os da função.
  4c. TESTE: assim que CONTRATO["parametros"] deixar de ser None, a ferramenta entra
      no catálogo do agente sozinha. Os casos c16 e c17 dependem dela:

          python encontro-02/rodar.py --casos c16 c17 --detalhe

Perguntas para decidir
----------------------
  - Que parâmetros o modelo precisa para chegar ao prestador certo? Quais valores aceitar?
  - "Campinas", "campinas" e "CAMPINAS " são a mesma cidade. Quem resolve isso: o modelo
    ou o código?
  - A planilha tem prestadores descredenciados e em negociação. O modelo deveria vê-los?
  - São Paulo tem mais de dez prestadores. Quantos voltam para o contexto?
  - Quais colunas nunca deveriam entrar no contexto? (O placar tem uma coluna para isso.)
  - Como o agente cita a planilha como fonte?
  - E erros: cidade sem prestador? Tipo que não existe?
"""
import unicodedata

from ferramentas import ErroDeFerramenta   # para devolver erros legíveis ao modelo (veja ferramentas.py)
from sistemas import PlanilhaGoogle

SHEETS = PlanilhaGoogle()
PLANILHA_ID = "planilha-rede-credenciada"
ABA = "prestadores"


def normalizar(texto: str) -> str:
    """'  São Paulo ' -> 'sao paulo'. Minúsculas, sem acento, sem espaço nas pontas."""
    sem_acento = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.lower().split())


# ======================================================================
# TODO 4a — a implementação
#
# Troquem a assinatura pelos parâmetros que vocês decidirem (com tipos e valores
# padrão) e escrevam o corpo. Esqueleto sugerido:
#   1. ler a planilha com SHEETS.ler(PLANILHA_ID, ABA)
#   2. transformar cada linha num dicionário (cabeçalho -> valor)
#   3. filtrar (normalizar() ajuda)
#   4. devolver {"resultados": [...], ...}
# ======================================================================
def consultar_rede_credenciada(cidade: str, especialidade: str = "", somente_24h: bool = False) -> dict:
    """Busca prestadores ativos da rede credenciada numa cidade.

    'especialidade' (opcional) filtra por tipo/especialidade (ex.: "laboratório",
    "pronto-socorro", "exames de sangue"), comparando texto normalizado. 'somente_24h'
    filtra só quem atende 24 horas. Prestadores descredenciados ou em negociação nunca
    voltam. Colunas comerciais/internas (código da operadora, valor negociado,
    observação interna) nunca voltam ao modelo.
    """
    cidade_norm = normalizar(cidade)
    especialidade_norm = normalizar(especialidade)

    bruto = SHEETS.ler(PLANILHA_ID, ABA)
    cabecalho = bruto["values"][0]
    linhas = [dict(zip(cabecalho, linha)) for linha in bruto["values"][1:]]

    encontrados = []
    for linha in linhas:
        if normalizar(linha.get("cidade", "")) != cidade_norm:
            continue
        if normalizar(linha.get("situacao", "")) != "ativo":
            continue
        if especialidade_norm:
            alvo = normalizar(linha.get("tipo", "")) + " " + normalizar(linha.get("especialidades", ""))
            if especialidade_norm not in alvo:
                continue
        if somente_24h and normalizar(linha.get("atende_24h", "")) not in ("sim",):
            continue
        encontrados.append({
            "prestador": linha["prestador"],
            "tipo": linha["tipo"],
            "especialidades": linha["especialidades"],
            "cidade": linha["cidade"],
            "uf": linha["uf"],
            "bairro": linha["bairro"],
            "telefone": linha["telefone"],
            "atende_24h": normalizar(linha.get("atende_24h", "")) == "sim",
        })

    if not encontrados:
        raise ErroDeFerramenta(
            "prestador_nao_encontrado",
            "Nenhum prestador ativo encontrado com esses critérios.",
            recebido={"cidade": cidade, "especialidade": especialidade, "somente_24h": somente_24h},
            como_corrigir="tentar sem 'especialidade', ou confirmar o nome da cidade com o colaborador",
            recuperavel=True,
        )

    return {"resultados": encontrados[:10], "fonte": PLANILHA_ID}


# ======================================================================
# TODO 4b — o contrato (mesmo formato de contratos.py)
# ======================================================================
CONTRATO = {
    "descricao": (
        "Busca prestadores (hospitais, clínicas, laboratórios, pronto-socorros) que atendem pelo "
        "plano de saúde numa cidade, na planilha da rede credenciada. Devolve só prestadores ativos "
        "(nunca descredenciados nem em negociação). Use 'especialidade' para filtrar por tipo de "
        "atendimento (ex.: 'laboratório', 'pronto-socorro', 'exames de sangue', 'pediatria') e "
        "'somente_24h' quando o colaborador precisar de atendimento 24 horas. "
        "Use antes de responder qualquer dúvida sobre onde atender pelo plano. "
        "Não use para saber o valor ou as regras do plano de saúde em si: isso é "
        "consultar_regra_beneficio."
    ),
    "parametros": {
        "type": "object",
        "properties": {
            "cidade": {"type": "string", "maxLength": 100,
                       "description": "A cidade onde o colaborador quer ser atendido."},
            "especialidade": {"type": "string", "maxLength": 100,
                               "description": "Tipo de prestador ou especialidade buscada (opcional)."},
            "somente_24h": {"type": "boolean",
                             "description": "Se true, devolve só quem atende 24 horas. Padrão: false."},
        },
        "required": ["cidade"],
        "additionalProperties": False,
    },
    "saida": ["prestador", "tipo", "especialidades", "cidade", "uf", "bairro", "telefone", "atende_24h", "fonte"],
}


NOME = "consultar_rede_credenciada"


if __name__ == "__main__":   # olhar os dados antes de escrever a ferramenta
    for linha in SHEETS.ler(PLANILHA_ID, ABA)["values"]:
        print(linha)
