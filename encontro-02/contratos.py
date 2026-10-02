"""Os contratos das ferramentas: o que o modelo lê.      (COMPLETE OS TODOs 1, 2 e 3)

O TODO 4 (a sexta ferramenta, construída do zero) fica em nova_ferramenta.py.

Cada contrato tem três partes:

    "descricao"   o que a ferramenta faz, QUANDO usar e QUANDO NÃO usar
    "parametros"  o schema da entrada (JSON Schema): tipos, enums, obrigatórios, limites
    "saida"       os campos do registro que voltam ao modelo. Tudo o que volta entra
                  no contexto, a cada passo seguinte do loop

O NOME de cada ferramenta já vem definido (o placar depende dele), assim como
os nomes dos parâmetros, que são os da implementação em ferramentas.py.

Duas ferramentas já vêm com contrato pronto, como exemplo: buscar_base_ti e
consultar_regra_beneficio. Leiam as duas antes de escrever as suas.

Para testar:  python encontro-02/rodar.py --casos c01 c11 c14 --detalhe
"""

CONTRATOS = {

    # ------------------------------------------------------------ PRONTO (exemplo)
    "buscar_base_ti": {
        "descricao": (
            "Busca na base de conhecimento de TI da Aurora: notebook e equipamentos, senha e "
            "bloqueio de conta, VPN e acesso remoto, instalação de programas. Devolve até 2 páginas, "
            "com o id da página (para citar como fonte) e o trecho relevante. "
            "Use antes de responder qualquer dúvida de TI e antes de decidir abrir um chamado. "
            "Não use para políticas de RH nem para benefícios, mesmo quando a pergunta menciona "
            "seguro, trabalho remoto ou ponto: essas palavras aparecem em páginas de TI também."
        ),
        "parametros": {
            "type": "object",
            "properties": {
                "pergunta": {"type": "string", "maxLength": 300,
                             "description": "A dúvida do colaborador, em português, com as palavras-chave do problema."},
            },
            "required": ["pergunta"],
            "additionalProperties": False,
        },
        "saida": ["id", "titulo", "atualizado_em", "trecho"],
    },

    # ------------------------------------------------------------ PRONTO (exemplo)
    "consultar_regra_beneficio": {
        "descricao": (
            "Consulta a regra vigente de um benefício da Aurora: valor, prazos, documentos e como pedir. "
            "Use para dúvidas gerais sobre um benefício. Devolve a página do benefício com o id para citar. "
            "Não use para saber se um colaborador específico tem direito ao benefício: isso é "
            "verificar_elegibilidade_beneficio."
        ),
        "parametros": {
            "type": "object",
            "properties": {
                "beneficio": {"type": "string", "enum": ["vale_refeicao", "plano_de_saude", "auxilio_creche"],
                              "description": "O benefício consultado."},
                "pergunta": {"type": "string", "maxLength": 300,
                             "description": "A dúvida do colaborador, para destacar o trecho relevante."},
            },
            "required": ["beneficio"],
            "additionalProperties": False,
        },
        "saida": ["id", "titulo", "atualizado_em", "trecho"],
    },

    # ==================================================================
    # TODO 1 — consultar_politica_rh
    #
    # Busca nas políticas de RH da wiki. Parâmetros da implementação:
    #   pergunta  (texto, obrigatório)
    #   tema      (opcional). Valores que o sistema aceita:
    #             "ferias", "trabalho_remoto", "licencas", "jornada", "integracao", "geral"
    #             ("integracao" é o guia de boas-vindas; "geral" busca em todas as políticas)
    # Campos disponíveis na saída (por página encontrada):
    #   id, titulo, tema, dono, atualizado_em, trecho, texto_completo, caminho,
    #   permissoes, tags, revisoes
    # Perguntas para decidir: quando o modelo NÃO deve usar esta ferramenta?
    # Sem o id na saída, o agente consegue citar a fonte?
    # ==================================================================
    "consultar_politica_rh": {
            "descricao": (
                "Busca nas políticas de RH da Aurora (férias, trabalho remoto, licenças, jornada, "
                "integração). Use 'tema' se souber do que se trata, ou 'geral' para buscar em todas. "
                "Devolve a página com o id para citar como fonte. "
                "Não use para TI nem para regras/valores de benefícios (use consultar_regra_beneficio) "
                "nem para elegibilidade individual (use verificar_elegibilidade_beneficio)."
            ),
            "parametros": {
                        "type": "object",
                        "properties": {
                            "tema": {"type": "string", "enum": ["ferias", "trabalho_remoto", "licencas", "jornada", "integracao", "geral"],
                                          "description": "O tema da política de RH consultada."},
                            "pergunta": {"type": "string", "maxLength": 300,
                                         "description": "A dúvida do colaborador, para destacar o trecho relevante."},
                        },
                        "required": ["pergunta"],
                        "additionalProperties": False,
                    },
            "saida": ["id", "titulo", "tema", "atualizado_em", "trecho"],
        },

    # ==================================================================
    # TODO 2 — abrir_chamado_ti
    #
    # ESCRITA: cria um chamado no service desk. Parâmetros da implementação:
    #   categoria  (obrigatório). Valores aceitos: "equipamento", "acesso", "software", "vpn", "outro"
    #   descricao  (obrigatório). Pelo menos 15 caracteres
    #   urgencia   (opcional). Valores aceitos: "baixa", "media", "alta"
    # Campos disponíveis na saída:
    #   id, status, categoria, urgencia, descricao, prazo_atendimento, grupo_resolvedor,
    #   fila_interna, sla_interno_min, historico, chave_idempotencia
    # Perguntas para decidir: em que situações o agente deve abrir chamado, e em quais
    # NÃO deve (a base de TI já resolve? o colaborador pediu?). O que o colaborador
    # precisa saber do chamado aberto?
    # ==================================================================
    "abrir_chamado_ti": {
        "descricao": (
            "Cria um chamado no service desk de TI. AÇÃO DE ESCRITA: cada chamada cria um novo "
            "chamado, mesmo repetindo os mesmos dados. Use só depois de buscar em buscar_base_ti e "
            "confirmar que a base não resolve o problema, e quando o colaborador pediu (ou aceitou) "
            "abrir o chamado. Não abra chamado para dúvidas que a base de conhecimento já responde "
            "(ex.: instalar programa disponível na Central de Software). Use urgencia 'alta' quando "
            "o colaborador ficou sem acesso a sistemas essenciais (ex.: perdeu o segundo fator, conta "
            "bloqueada); 'media' é o padrão."
        ),
        "parametros": {
                    "type": "object",
                    "properties": {
                        "categoria": {"type": "string", "enum": ["equipamento", "acesso", "software", "vpn", "outro"],
                                        "description": "A categoria do chamado."},
                        "descricao": {"type": "string", "minLength": 15, "maxLength": 300,
                                        "description": "A descrição do problema relatado, com pelo menos 15 caracteres."},
                        "urgencia": {"type": "string", "enum": ["baixa", "media", "alta"],
                                        "description": "A urgência do chamado. Padrão: 'media'."},
                    },
                    "required": ["categoria", "descricao"],
                    "additionalProperties": False,
                },
        "saida": ["id", "status", "categoria", "urgencia", "descricao", "prazo_atendimento", "grupo_resolvedor", "historico"],
    },

    # ==================================================================
    # TODO 3 — verificar_elegibilidade_beneficio
    #
    # Lê o cadastro do colaborador no sistema de RH e faz uma PRÉ-ANÁLISE automática.
    # Só o RH confirma elegibilidade. Parâmetros da implementação:
    #   colaborador_id  (obrigatório). Ex.: "1043"
    #   beneficio       (obrigatório). Valores aceitos: "vale_refeicao", "plano_de_saude", "auxilio_creche"
    # Campos disponíveis na saída:
    #   colaborador_id, nome, cpf, salario_base, regime, admissao, dependentes,
    #   beneficios_ativos, beneficio, pre_analise, criterios_verificados, aviso
    # Perguntas para decidir: quais desses campos o modelo precisa ver, e quais nunca
    # deveriam entrar no contexto? O que o agente faz com a pré-análise?
    # Em que se diferencia de consultar_regra_beneficio?
    # ==================================================================
    "verificar_elegibilidade_beneficio": {
        "descricao": (
            "Lê o cadastro do colaborador no sistema de RH e faz uma PRÉ-ANÁLISE automática dos "
            "critérios de um benefício. NÃO é uma confirmação de elegibilidade: só o RH confirma, "
            "depois de analisar a documentação. Use quando o colaborador perguntar se TEM DIREITO a "
            "um benefício específico (não para saber as regras gerais: isso é "
            "consultar_regra_beneficio). Sempre que usar esta ferramenta, informe o resultado da "
            "pré-análise como indicativo e escale/oriente o colaborador a confirmar com o RH — nunca "
            "afirme elegibilidade definitiva com base só nela."
        ),
        "parametros": {
                    "type": "object",
                    "properties": {
                        "colaborador_id": {"type": "string", "maxLength": 10,
                                            "description": "O ID do colaborador no sistema de RH."},
                        "beneficio": {"type": "string", "enum": ["vale_refeicao", "plano_de_saude", "auxilio_creche"],
                                        "description": "O benefício para o qual verificar a elegibilidade."},
                    },
                    "required": ["colaborador_id", "beneficio"],
                    "additionalProperties": False,
                },
        "saida": ["colaborador_id", "beneficio", "dependentes", "beneficios_ativos", "pre_analise", "criterios_verificados", "aviso"],
    },
}


# ======================================================================
# TODO 4 — a sexta ferramenta é construída do zero em nova_ferramenta.py
# (contrato E implementação). Quando o contrato de lá estiver preenchido,
# ela entra neste catálogo sozinha. Não precisa mexer aqui.
# ======================================================================
import nova_ferramenta as _nova   # noqa: E402

if _nova.CONTRATO.get("parametros") is not None:
    CONTRATOS[_nova.NOME] = _nova.CONTRATO
