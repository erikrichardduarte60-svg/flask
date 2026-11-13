from flask import Blueprint, render_template, request

bp = Blueprint("calculos", __name__)

# ---------------------------------------------------------------------------
# Regras de negócio (funções puras: não usam request, banco nem template)
# ---------------------------------------------------------------------------

# (limite superior da faixa, alíquota, parcela a deduzir) - tabela mensal 2026
TABELA_IRPF = [
    (2428.80, 0.0, 0.0),
    (2826.65, 0.075, 182.16),
    (3751.05, 0.15, 394.16),
    (4664.68, 0.225, 675.49),
    (float("inf"), 0.275, 908.73),
]

LIMITE_ISENCAO = 5000.00
LIMITE_REDUCAO = 7350.00
REDUCAO_MAXIMA = 312.89
DESCONTO_SIMPLIFICADO = 607.20

def calcular_irpf(salario_bruto):
    """Calcula o IRPF mensal estimado (tabela 2026 com redução da Lei 15.270/2025).
    Simplificação: usa o desconto simplificado no lugar de INSS e dependentes."""

    # A tabela progressiva incide sobre a base após o desconto simplificado
    base_calculo = max(0.0, salario_bruto - DESCONTO_SIMPLIFICADO)

    aliquota, parcela = 0.0, 0.0

    for limite, aliq, deducao in TABELA_IRPF:
        if base_calculo <= limite:
            aliquota, parcela = aliq, deducao
            break

    imposto_tabela = max(0.0, base_calculo * aliquota - parcela)

    # A redução usa o rendimento tributável mensal (o salário bruto)
    if salario_bruto <= LIMITE_ISENCAO:
        reducao = REDUCAO_MAXIMA
    elif salario_bruto <= LIMITE_REDUCAO:
        reducao = max(0.0, 978.62 - 0.133145 * salario_bruto)
    else:
        reducao = 0.0

    reducao = min(reducao, imposto_tabela)  # a redução nunca passa do imposto
    imposto = imposto_tabela - reducao

    return {
        "salario_bruto": salario_bruto,
        "base_calculo": round(base_calculo, 2),
        "aliquota": aliquota * 100,
        "imposto_tabela": round(imposto_tabela, 2),
        "reducao": round(reducao, 2),
        "imposto": round(imposto, 2),
        "salario_liquido": round(salario_bruto - imposto, 2),
    }


def calcular_decimo_terceiro(salario_base, meses_trabalhados):
    """13º proporcional aproximado: salário / 12 x meses trabalhados no ano."""
    valor = salario_base / 12 * meses_trabalhados

    return {
        "salario_base": salario_base,
        "meses": meses_trabalhados,
        "valor_mensal": round(salario_base / 12, 2),
        "decimo_terceiro": round(valor, 2),
    }


def ler_numero(campo):
    """Converte o texto do formulário em float (aceita vírgula decimal).
    Levanta ValueError se for inválido."""
    texto = request.form.get(campo, "").strip().replace(",", ".")
    return float(texto)


# ---------------------------------------------------------------------------
# Controlador: Requisição -> Processamento -> Resposta (nada vai ao banco)
# ---------------------------------------------------------------------------

@bp.route("/painel", methods=("GET", "POST"))
def painel():
    resultado_irpf = None
    resultado_13 = None
    erro_irpf = None
    erro_13 = None

    if request.method == "POST":
        acao = request.form.get("acao")

        if acao == "irpf":
            try:
                salario = ler_numero("salario_bruto")

                if salario <= 0:
                    raise ValueError

                resultado_irpf = calcular_irpf(salario)

            except ValueError:
                erro_irpf = "Informe um salário bruto válido, maior que zero."

        elif acao == "rescisao":
            try:
                salario = ler_numero("salario_base")
                meses = int(request.form.get("meses", "").strip())

                if salario <= 0 or not 1 <= meses <= 12:
                    raise ValueError

                resultado_13 = calcular_decimo_terceiro(salario, meses)

            except ValueError:
                erro_13 = "Informe um salário válido e meses entre 1 e 12."

    return render_template(
        "calculos/index.html",
        irpf=resultado_irpf,
        decimo=resultado_13,
        erro_irpf=erro_irpf, erro_13=erro_13,
    )