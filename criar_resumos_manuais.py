"""
Resumos escritos manualmente a partir da leitura dos PDFs.
Substitui os resumos gerados automaticamente por versões de qualidade.
"""
import json
from pathlib import Path

RESUMOS_JSON = Path(__file__).parent / "output" / "resumos.json"
CARTAS_JSON = Path(__file__).parent / "output" / "cartas_processadas.json"

# Carrega resumos existentes para preservar campos de performance
with open(CARTAS_JSON, encoding="utf-8") as f:
    cartas = json.load(f)
cartas_map = {c["fundo"]: c for c in cartas}


def perf_texto(fundo_nome):
    carta = cartas_map.get(fundo_nome, {})
    perf = carta.get("performance", {})
    mes = perf.get("mes", "N/D")
    bench = perf.get("benchmark_mes", "N/D")
    ano = perf.get("ano", "N/D")
    if mes != "N/D" and bench != "N/D":
        try:
            diff = float(mes) - float(bench)
            comp = f"+{diff:.2f}pp" if diff > 0 else f"{diff:.2f}pp"
            txt = f"Rentabilidade no mês: {mes}% (CDI: {bench}%, {comp} vs CDI)"
        except ValueError:
            txt = f"Rentabilidade no mês: {mes}% (CDI: {bench}%)"
    elif mes != "N/D":
        txt = f"Rentabilidade no mês: {mes}%"
    else:
        txt = "Rentabilidade do mês não disponível na carta"
    if ano != "N/D":
        try:
            if float(ano) <= 50:
                txt += f". Acumulado no ano: {ano}%"
        except ValueError:
            pass
    return txt


def wpp(fundo, periodo_leg, perf, pontos):
    linhas = [f"*{fundo}* - Carta {periodo_leg}", perf]
    for p in pontos[:3]:
        linhas.append(f"• {p}")
    return "\n".join(linhas[:7])


MESES = {"01":"Jan","02":"Fev","03":"Mar","04":"Abr","05":"Mai","06":"Jun",
         "07":"Jul","08":"Ago","09":"Set","10":"Out","11":"Nov","12":"Dez"}

def periodo_leg(p):
    if "/" in p:
        m, a = p.split("/")
        return f"{MESES.get(m,m)}/{a}"
    return p


resumos = {}

# ===================== ARMOR AXE FIC FIM =====================
nome = "ARMOR AXE FIC FIM"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Fundo rendeu 1,64% no mês, com destaques positivos em renda fixa local (+0,44%), caixa (+0,77%) e renda variável (+0,57%). Custos e taxas detraíram -0,21%.",
    "Conflito no Oriente Médio seguiu sem resolução em maio, com negociações entre EUA e Irã marcadas por constantes mudanças de tom e ataques pontuais elevando a tensão.",
    "Sinalização de cessar-fogo de 60 dias e reabertura temporária do Estreito de Ormuz no final do mês, mas mercado mantém postura cautelosa.",
    "Bolsa americana resiliente sustentada por resultados de empresas de tecnologia; dados de China e Zona do Euro vieram mais fracos que o esperado.",
    "Fed em transição: Kevin Warsh assume em julho com inflação pressionada por petróleo; retirada do easing bias esperada na próxima comunicação.",
    "No Brasil, Ibovespa caiu mais de 7% pressionado por ruído político (PEC 6x1 e recuo na revisão do BPC), alta concentração em bancos/commodities e sem exposição ao rali de tech global.",
    "Fundo aumentou posições aplicadas em juros reais domésticos de médio prazo com hedge tático, e mantém alocação aplicada em Treasuries e comprada em bolsa global.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "O tema central de maio foi a negociação entre EUA e Irã para resolução do conflito no Oriente Médio. O fluxo marítimo no Estreito de Ormuz permaneceu bastante restrito, mantendo elevado o prêmio de risco sobre o petróleo. No final do mês, houve sinalização de cessar-fogo de 60 dias, mas o mercado segue cauteloso. Dados econômicos de China e Zona do Euro vieram fracos, enquanto a economia americana segue dinâmica com mercado de trabalho estável.",
    "posicionamento": "Aumento de posições aplicadas em juros reais domésticos de médio prazo com hedge em operações táticas tomadas na curva nominal. No exterior, mantém alocação aplicada em Treasuries e comprada em bolsa global. Ibovespa pressionado por ruído político e falta de exposição ao rali de tecnologia.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== GENOA CAPITAL SAGRES FIC FIM ACCESS =====================
nome = "GENOA CAPITAL SAGRES FIC FIM ACCESS"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Economia americana sólida com dinâmicas heterogêneas: famílias de menor renda afetadas pela gasolina, investimento puxado por data centers e IA.",
    "Inflação nos EUA enfrenta choques sucessivos (tarifas, petróleo, componentes de IA); Fed em posição delicada. Kevin Warsh deve retirar viés baixista na próxima reunião.",
    "Cenário mais provável: juros estáveis nos EUA até eleições de novembro, com discussão migrando gradualmente para alta de juros.",
    "Brasil sem hiato relevante: desemprego em mínimas históricas, demissões voluntárias em máximas, pressão salarial acima da produtividade.",
    "Inflação brasileira com balanço de riscos assimétrico para cima: núcleos de serviços entre 5,5% e 6,0% anualizados, PEC 6x1 com impacto estimado de 30 a 80 pontos-base.",
    "Projetam inflação de 5,5% em 2026 e 5,0% em 2027. Selic terminal estimada entre 15,75% e 16,25%.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "A economia americana segue expandindo a ritmo sólido, com investimento puxado por data centers e IA. A inflação enfrenta choques sucessivos e o Fed se encontra em posição delicada. Kevin Warsh assume o comitê e deve retirar o viés baixista. No Brasil, a economia segue aquecida sem abrir hiato relevante, com desemprego em mínimas e inflação com riscos assimétricos para cima.",
    "posicionamento": "Posições aplicadas em juros no Brasil (aposta em alta da Selic). Posições vendidas em real. Cautela com ativos de risco globais dado cenário de inflação persistente.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== IBIUNA HEDGE STH FIC FIM ACCESS =====================
nome = "IBIUNA HEDGE STH FIC FIM ACCESS"
per = "01/2025"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Livro de juros global foi destaque positivo, com posições aplicadas em curvas de juros de países emergentes.",
    "Posição comprada em Dólar vs. Real foi o principal detrator do mês.",
    "Início do governo Trump menos turbulento que o esperado, foco inicial em migração e desregulamentação, adiando tarifas em pelo menos dois meses.",
    "Avaliação de que o alívio nos mercados se provará temporário: agenda protecionista de Trump demanda posições defensivas.",
    "EUA com dólar apreciado, economia crescendo acima do potencial, desemprego abaixo do equilíbrio e inflação acima da meta.",
    "Tarifas devem adicionar pressões inflacionárias; impacto adverso sobre crescimento será relevante a médio prazo mas afetará EUA menos que parceiros comerciais.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "O início do governo Trump foi menos turbulento que o antecipado, com foco em migração e desregulamentação. Entretanto, a avaliação é que esse alívio será temporário: a implementação da agenda protecionista demanda posições defensivas em um ambiente potencialmente volátil. A economia americana cresce acima do potencial com inflação acima da meta.",
    "posicionamento": "Destaque para posições aplicadas em juros de emergentes. Comprado em Dólar vs Real (detrator). Livro sistemático com contribuição positiva. Postura defensiva para cenário de tarifas.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== IBIUNA TOTAL CREDIT FIC FIM CP =====================
nome = "IBIUNA TOTAL CREDIT FIC FIM CP"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Setores de utilidade pública e indústria/construção foram os principais destaques positivos; bancos e papel/celulose foram destaques negativos.",
    "Dissociação crescente entre mercados de commodities e ativos de risco globais: petróleo pressionado pelo conflito, mas S&P 500 perto da máxima histórica em 7.580 pontos.",
    "Risco assimétrico caso o conflito se prorrogue: petróleo pode ir bem acima de US$150/barril.",
    "Curva de juros americana pressionada pela inflação do petróleo e mudança no comando do Fed com Kevin Warsh. Não esperam corte de juros do Fed em 2026.",
    "Reduziram risco da carteira offshore, realizando lucro em parte da carteira de bonds após forte performance acumulada.",
    "CEMBI com retorno positivo de ~0,5% no mês; treasury de 10 anos fechou a 4,44% (chegou a 4,66% intra-mês).",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Maio foi marcado por dissociação entre commodities e ativos de risco. Conflito no Oriente Médio mantém pressão sobre petróleo, mas o S&P 500 encerrou perto de máxima histórica. Curva de juros americana subiu com inflação e troca no Fed. Não esperam corte de juros do Fed em 2026, com risco de aumento em 2027.",
    "posicionamento": "Reduziram risco da carteira offshore e realizaram lucro em bonds. Setores de utilidade pública e indústria/construção como destaques positivos. Postura mais conservadora diante do cenário de juros e conflito.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== ITAU ACTION DEB INC FIC INFRA RF CP LP =====================
nome = "ITAU ACTION DEB INC FIC INFRA RF CP LP"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Fundo de gestão ativa em juros local (pós, pré e real) e crédito privado, focado em debêntures de infraestrutura (Lei 12.431).",
    "Retorno de -0,51% no mês (benchmark IMA-B5: +0,97%), acumulado de 1,80% no ano vs 6,25% do benchmark.",
    "Target de volatilidade entre 8% e 10% a.a., com retorno líquido objetivo de 2,0% a 2,5% ao ano acima das NTN-Bs.",
    "Volatilidade realizada de 7,33% nos últimos 12 meses.",
    "Desde o início (jan/2022), retorno acumulado de 54,08%. Esteve acima do benchmark em 59% dos meses.",
    "Sem incidência de IR para investidores pessoa física por ser fundo de infraestrutura.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Mês negativo para o fundo em um ambiente de abertura de juros reais e pressão sobre ativos de renda fixa. O benchmark IMA-B5 rendeu apenas 0,97%, refletindo o momento desafiador para posições em juros reais.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== Itau Janeiro Multimercado Dist FICFI RL =====================
nome = "Itau Janeiro Multimercado Dist FICFI RL"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Fundo macro que busca retorno absoluto em qualquer cenário, com foco em identificar temas de investimento no início do ciclo.",
    "Rentabilidade de 1,52% no mês (142,1% do CDI), CDI +0,45% no mês.",
    "Acumulado no ano: 2,19% (38,6% do CDI), impactado pela perda de -4,03% em março.",
    "Desde o início (set/2023): retorno acumulado de 44,37% (117,6% do CDI, CDI +2,03% a.a.).",
    "Meses acima do benchmark: 63%. Meses de retorno positivo: 88%.",
    "Volatilidade desde o início de 3,94%, com índice Sharpe de 0,51.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo multimercado macro com retorno positivo no mês, superando o CDI. Recuperação parcial após mês de março negativo. Desde o início mantém retorno acumulado consistente acima do CDI.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== JGP CORPORATE PLUS FIC FIM CP =====================
nome = "JGP CORPORATE PLUS FIC FIM CP"
per = "04/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "JGP Corporate Plus rendeu 1,02% em abril. 95% alocado com 322 ativos de 196 emissores. Carrego: DI +2,60%, prazo médio de 3,0 anos.",
    "Mercado de crédito local positivo em abril: Idex-CDI rendeu +1,68% (MTM +0,39%, carrego +1,29%). Mercado offshore positivo com CEMBI Latam +2,32%.",
    "Abril marcado por aversão a risco: conflito no Oriente Médio elevou petróleo a US$110/barril; Ibovespa caiu mais de 6%.",
    "Destaques positivos: debêntures de CSN (CSNAA1) e Braskem (BRKMA8). Mercado primário desaqueceu com apenas 10 emissões (R$8,2 bi).",
    "Spreads de crédito em patamares justos mas com tendência de abertura diante do cenário de incerteza.",
    "Postura mais conservadora em novas alocações, privilegiando liquidez e emissores de alta qualidade.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Abril foi marcado por aversão a risco com conflito no Oriente Médio elevando petróleo a US$110/barril. Mercado de crédito local teve desempenho positivo (Idex-CDI +1,68%), enquanto offshore também rendeu bem (CEMBI Latam +2,32%). Mercado primário desaqueceu significativamente.",
    "posicionamento": "95% alocado com carrego de DI +2,60%. Destaques em Braskem e CSN. Postura mais conservadora em novas alocações, privilegiando liquidez.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== Kapitalo K10 =====================
nome = "Kapitalo K10"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Retorno de 0,85% vs 1,07% do benchmark. Livros de moedas e bolsa com resultado positivo.",
    "Negociações para reabrir o Estreito de Ormuz avançam, mas sem acordo definitivo. Estoques globais de petróleo em níveis criticamente baixos.",
    "Equilíbrio frágil no petróleo: sem normalização do Estreito, preço deve voltar a subir nas próximas semanas.",
    "Fed mais neutro: Waller sinalizou que mercado de trabalho está estabilizando, mas risco de inflação persistente pela alta de energia.",
    "Diferencial de crescimento a favor dos EUA e Fed preocupado com inflação favorecem dólar forte. Adicionaram posição comprada em dólar contra euro e libra.",
    "No Brasil, condições para continuidade do ciclo de corte de juros estão se exaurindo: emprego acelerando, estímulo fiscal contínuo, inflação piorando. Reduziram posições aplicadas em juros Brasil.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Negociações de paz no Oriente Médio avançam, mas estoques de petróleo estão criticamente baixos e o equilíbrio é frágil. O impacto da guerra é perceptível na inflação global, mas tímido na atividade. Nos EUA, crescimento forte puxado por IA e impulso fiscal. Fed em transição para postura mais neutra. No Brasil, condições para corte de juros se exaurem com aceleração do emprego e piora inflacionária.",
    "posicionamento": "Comprados em dólar contra euro e libra. Reduziram posições aplicadas em juros Brasil. Mantêm posições compradas em peso chileno. Vendidos em café, trigo e zinco. Tese de investimento em Colômbia: eleição pode trazer mudança de regime com candidato de direita.",
    "observar": "Evolução das negociações EUA-Irã para reabertura do Estreito de Ormuz. Eleições colombianas de 2026 com alta probabilidade de mudança de regime político.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== LEGACY CAPITAL FIC FIM ACCESS =====================
nome = "LEGACY CAPITAL FIC FIM ACCESS"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Rendimento de 1,48% no mês e 3,71% no ano. Resultado positivo concentrado em bolsa global, moedas e commodities.",
    "Mercado de maio dominado pela expectativa de acordo de paz entre EUA e Irã. Preços de ativos de risco voláteis com oscilações conforme as manchetes.",
    "Produção de petróleo no Golfo segue 15MBD abaixo do pré-guerra (~15% do consumo mundial). Barril entre US$90-100, 65% acima do pré-guerra.",
    "Se Estreito continuar fechado e estoques se esgotarem, petróleo pode ir a US$200/barril. Em cenário de acordo e reabertura, pode cair a US$80 até fim de 2026.",
    "No Brasil, atividade segue forte com PIB acima do potencial, inflação acima de 5% e Selic em patamar elevado.",
    "Cenário benigno de acordo e reabertura do Estreito vem se tornando mais provável nas últimas semanas.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Dinâmica de mercado em maio marcada pela expectativa em torno do acordo EUA-Irã. Produção de petróleo no Golfo segue 15MBD abaixo do pré-guerra. Sem acordo, petróleo pode ir a US$200; com acordo e reabertura, pode cair a US$80 até fim de 2026. Cenário benigno vem se tornando mais provável.",
    "posicionamento": "Resultado positivo concentrado em posições otimistas em bolsa global, moedas e commodities. Posicionamento reflete expectativa de resolução gradual do conflito.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== M8 Credit Advanced FICFIDC =====================
nome = "M8 Credit Advanced FICFIDC"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Retorno de 1,22% no mês (114% do CDI). Acumulado no ano: 6,40% (113% do CDI).",
    "Desde o início (jun/2023): retorno acumulado de 52,85% (122% do CDI, CDI +1,89% a.a.).",
    "Fundo investe preponderantemente em cotas seniores e mezaninos de FIDCs.",
    "Consistência: nunca rendeu abaixo de 0,94% em um mês desde o início.",
    "Menor rentabilidade mensal: 0,94%. Maior: 1,46%.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo de crédito estruturado com retorno consistente acima do CDI. Investe em cotas seniores e mezaninos de FIDCs com gestão ativa.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== M8 CREDIT STRATEGY PLUS FIC FIM CP =====================
nome = "M8 CREDIT STRATEGY PLUS FIC FIM CP"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Retorno de 1,04% no mês (97% do CDI). Acumulado no ano: 6,56%.",
    "Desde o início (mar/2019): retorno acumulado de 161,16%.",
    "Fundo para investidores profissionais com exposição a cotas seniores, mezanino e subordinada júnior de FIDCs.",
    "Histórico de rendimentos consistentes com média acima de 120% do CDI desde 2021.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo de crédito estruturado para investidores profissionais com exposição diversificada a FIDCs, incluindo cotas subordinadas. Histórico longo de rendimentos acima do CDI.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== SPX NIMITZ FIC FIM ACCESS =====================
nome = "SPX NIMITZ FIC FIM ACCESS"
per = "04/2025"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Crescimento brasileiro em 2025 sustentado por agropecuária, reajuste do salário-mínimo e calendário fiscal concentrado no 1º semestre.",
    "Consignado do setor privado deve adicionar 0,4% ao PIB entre 2º semestre de 2025 e 1º semestre de 2026.",
    "Cenário inflacionário desafiador com serviços pressionados pelo aquecimento da economia; BCB deve elevar Selic a 15% e manter durante todo 2026.",
    "Trump implementou tarifas maiores e mais abrangentes que o esperado; economia americana deve desacelerar nos próximos meses.",
    "Surpresas de inflação e piora das expectativas dos consumidores levam à expectativa de Fed parado em 2025.",
    "Posições de curva em juros desenvolvidos, sem direcional em Brasil, posições relativas em moedas (desenvolvidos vs emergentes), taticamente vendidos em bolsas globais.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "No Brasil, crescimento sustentado pelo fiscal com cenário inflacionário desafiador. Selic deve ir a 15% e permanecer durante todo 2026. Nos EUA, tarifas de Trump maiores que o esperado devem desacelerar a economia, mas Fed deve manter juros parados em 2025 diante da piora inflacionária.",
    "posicionamento": "Posições concentradas em curva de juros de países desenvolvidos, sem direcional em Brasil. Posições relativas em moedas (desenvolvidos vs emergentes). Taticamente vendidos em bolsas globais. Postura conservadora em crédito emergente soberano.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== SPX SEAHAWK GLOBAL FIC FIM CP =====================
nome = "SPX SEAHAWK GLOBAL FIC FIM CP"
per = "03/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Fundo de renda fixa crédito privado com objetivo de ganhos de capital no longo prazo.",
    "Carteira diversificada e líquida: debêntures, FIDCs, notas promissórias, letras financeiras, CDBs. Rating mínimo BBB para dívida local.",
    "Patrimônio líquido do Master: R$3,98 bilhões. PL do FIC: R$1,36 bilhão.",
    "Volatilidade desde o início: 1,28%. Taxa de administração: 0,6% a.a. Performance: 20% sobre CDI.",
    "Gestão baseada em abordagem macro e microeconômica com rigorosa avaliação de riscos.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo de renda fixa crédito privado da SPX com gestão ativa. Carteira diversificada em debêntures, FIDCs e outros instrumentos com rating mínimo BBB. Volatilidade baixa (1,28%) e patrimônio expressivo.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}


# ===================== SOLANA LS FIC FIM =====================
nome = "SOLANA LS FIC FIM"
per = "04/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Retorno de 2,32% no mês (213% do CDI). Acumulado no ano: 9,06% (200% do CDI).",
    "Desde o início (out/2013): retorno acumulado de 296,35% (132% do CDI). Sharpe de 4,91.",
    "Destaques positivos no mês: imobiliário (+0,59%), tecnologia (+0,47%), petróleo (+0,38%), consumo não cíclico (+0,35%) e siderurgia/mineração (+0,18%).",
    "Destaques negativos: consumo cíclico (-0,27%), índice EUA (-0,15%) e índice small-cap (-0,12%).",
    "Exposição gross: 66,46% intrasetorial, 15,89% intersetorial, 1,43% intracompany, 0,80% hedge.",
    "123 meses de retorno positivo vs 28 negativos. 88 meses acima do CDI. PL: R$ 127 milhões (master: R$ 238 mi).",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo long and short direcional com histórico longo e consistente desde 2013. Estratégia primordialmente intrasetorial (66% da exposição), buscando retorno acima do CDI com volatilidade controlada (3,31% a.a.).",
    "posicionamento": "Maior contribuição no ano vem de siderurgia/mineração (+2,92%), consumo não cíclico (+0,95%), petróleo (+0,89%) e imobiliário (+0,99%). Custos operacionais representaram 2,64% no ano.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== SOLIS CAPITAL ANTARES LIGHT FIC FIM CP =====================
nome = "SOLIS CAPITAL ANTARES LIGHT FIC FIM CP"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Retorno de 1,16% no mês (108,40% do CDI). Acumulado no ano: 6,21% (109,63% do CDI).",
    "Desde o início (set/2019): retorno acumulado de 108,95% (128,44% do CDI). 81 meses positivos, zero negativos.",
    "Fundo investe em carteira diversificada de cotas sênior de FIDCs, selecionadas com análise robusta de originadores e monitoramento contínuo.",
    "Carteira composta por 41% caixa, 14% multicedente/multisacado, 10% consignado estadual/municipal/federal e diversas outras classes de crédito.",
    "72,8% da carteira com rating AAA, 95,3% AA ou superior. Concentração: Top 5 = 20% do PL, Top 20 = 45,3%.",
    "PL atual: R$ 1,02 bilhão. PL da estratégia: R$ 12,7 bilhões. Resgate D+44, investidor qualificado.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo de FIDC com histórico excepcional: nunca teve mês negativo em quase 7 anos de operação. Carteira conservadora com 72,8% em rating AAA e alta diversificação por setores e lastros. Volatilidade de apenas 0,03% (12 meses).",
    "posicionamento": "Alocação diversificada em cotas sênior de FIDCs com lastro em consignado, crédito pessoal, agro e outros setores. Alta proporção de caixa (41%) demonstra postura conservadora e liquidez.",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# ===================== ABSOLUTE HIDRA CDI FIC FI INFRA RF =====================
nome = "ABSOLUTE HIDRA CDI FIC FI INFRA RF"
per = "05/2026"
pleg = periodo_leg(per)
perf = perf_texto(nome)
pontos = [
    "Retorno de 1,13% no mês. Acumulado no ano: 3,10% (55% do CDI), impactado por meses negativos em março (-0,19%) e abril (-0,47%).",
    "Desde o início (out/2022): retorno acumulado de 62,68% (115% do CDI).",
    "Fundo de infraestrutura (Lei 12.431) com isenção de IR para pessoas físicas. Benchmark CDI.",
    "Carteira concentrada em energia elétrica (59%), petróleo e gás (9,89%), saneamento (7,62%) e transporte (6,71%).",
    "71% em debêntures, 22% soberano, 4% bancários, 4% FIDC/Bonds. Rating: 72,8% AAA, 95,3% AA ou superior.",
    "PL: R$ 2,67 bilhões. Gestão ativa fundamentalista combinada com análise técnica e cenário macro da Absolute.",
]
resumos[nome] = {
    "periodo": per, "periodo_legivel": pleg, "performance": perf,
    "pontos_chave": pontos,
    "tese_macro": "Fundo de crédito de infraestrutura com isenção fiscal para PF. Carteira concentrada em energia elétrica e utilities. Ano de 2026 desafiador com dois meses negativos (março e abril), mas recuperação em maio.",
    "posicionamento": "Gestão ativa em debêntures de infraestrutura com foco em energia elétrica e utilities. Estratégia fundamentalista combinada com visão macro. Alta qualidade de crédito (maioria AAA/AA).",
    "whatsapp": wpp(nome, pleg, perf, pontos),
}

# Salva
with open(RESUMOS_JSON, "w", encoding="utf-8") as f:
    json.dump(resumos, f, ensure_ascii=False, indent=2)

print(f"{len(resumos)} resumos salvos em {RESUMOS_JSON}")
for nome, r in resumos.items():
    n = len(r.get("pontos_chave", []))
    print(f"  [OK] {nome} - {r['periodo_legivel']} ({n} pontos-chave)")
