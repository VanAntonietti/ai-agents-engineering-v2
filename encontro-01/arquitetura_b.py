"""Arquitetura B — workflow determinístico.   (COMPLETE OS TODOs 1 e 2)

O fluxo está escrito no código. O modelo só faz duas tarefas pequenas:
classificar a pergunta e redigir a resposta.

    pergunta ──► classificar ──► tema?
                                   ├── "elegibilidade" ──► escalar (sem chamar o modelo)
                                   └── "rh" | "ti" | "beneficios"
                                          ──► buscar(tema, pergunta) ──► [ modelo + 3 documentos ] ──► resposta

Quem decide o próximo passo é o CÓDIGO, não o modelo.
"""
from comum import modelo
from comum.resultado import Resultado
from ferramentas import buscar, formatar
from politica_de_resposta import FORMATO_JSON, REGRAS

CATEGORIAS = ("rh", "ti", "beneficios", "elegibilidade")

PROMPT_CLASSIFICADOR = """Classifique a dúvida de um colaborador em UMA destas categorias:

- ti: notebook, senha, Windows, computador travado, VPN, e-mail, acesso a sistemas
- rh: salário, folha de pagamento, férias, ponto, demissão, promoção, contrato
- beneficios: vale transporte, vale refeição, plano de saúde, auxílio creche, gympass
- elegibilidade: quando a pessoa pergunta se ELA tem direito a algo
  ("eu tenho direito a...", "posso pedir...", "eu me encaixo em...")

Responda só com o nome da categoria, em minúsculas, sem pontuação e sem explicação.
"""


def classificar(pergunta: str) -> str:
    resposta = modelo.chamar([modelo.mensagem_do_usuario(pergunta)],
                             sistema=PROMPT_CLASSIFICADOR, max_tokens=10)
    categoria = resposta.texto.strip().lower()

    # O modelo pode responder algo fora das CATEGORIAS ("beneficios." ou uma frase).
    for valida in CATEGORIAS:
        if valida in categoria:
            return valida
    return "todos"  # padrão: não sabemos o tema, então buscamos no corpus inteiro


def resolver(pergunta: str) -> Resultado:
    categoria = classificar(pergunta)

    if categoria == "elegibilidade":
        return Resultado("escalar", [], "O RH vai analisar sua solicitação.")

    docs = buscar(categoria, pergunta)
    if not docs:
        return Resultado("nao_sei", [], "Não encontrei documentos sobre isso.")

    sistema = (f"{REGRAS}\n\n{FORMATO_JSON}\n\nDocumentos disponíveis:\n\n"
               + "\n\n".join(formatar(doc) for doc in docs))

    resposta = modelo.chamar([modelo.mensagem_do_usuario(pergunta)], sistema=sistema)
    return Resultado.de_json(resposta.texto)
