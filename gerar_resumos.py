"""
Gerador de Resumos Estruturados das Cartas dos Gestores.
Extrai seções do texto, limpa artefatos e gera resumo para o site + WhatsApp.
"""
import json
import re
from pathlib import Path

PASTA_OUTPUT = Path(__file__).parent / "output"
CARTAS_JSON = PASTA_OUTPUT / "cartas_processadas.json"
RESUMOS_JSON = PASTA_OUTPUT / "resumos.json"

MESES = {
    "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
    "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
    "09": "Set", "10": "Out", "11": "Nov", "12": "Dez",
}

# Padrões de lixo a remover
LIXO_PATTERNS = [
    r"https?://\S+",
    r"\S+@\S+\.\S+",
    r"CNPJ[:\s]*\d[\d./\-]+",
    r"CVM\s*n[ºo°]?\s*\d+",
    r"(?:Tel|Fax|Telefone)[:\s]*[\d\s()+\-]+",
    r"(?:Av\.|Rua|Alameda|R\.)\s+[^.]{5,60},\s*\d+[^.]{0,40}(?:andar|sala|conj)",
    r"(?:administrador|custodiante|auditor|gestor)[:\s]+\S+.*$",
    r"(?:taxa\s+(?:de\s+)?(?:adm|administração|performance))[:\s]+[\d,.\s%]+(?:a\.a\.)?",
    r"(?:público\s+alvo|política\s+de\s+investimento)\b.*$",
    r"(?:regulamento|prospecto|lâmina)\b.*$",
    r"SAC\s*[:.].*$",
    r"Ouvidoria\s*[:.].*$",
    r"\*+\s*(?:FIDC|fundo).*$",
    r"(?:rentabilidade\s+passada|resultados\s+passados).*$",
    r"(?:este\s+(?:material|documento)\s+(?:é|tem|foi|não)).*$",
    r"(?:as\s+informações\s+contidas\s+neste).*$",
    r"(?:as\s+opiniões\s+expressas).*$",
    r"(?:para\s+uso\s+exclusivo).*$",
]
LIXO_RE = [re.compile(p, re.I | re.MULTILINE) for p in LIXO_PATTERNS]


def periodo_legivel(periodo: str) -> str:
    if "/" in periodo:
        m, a = periodo.split("/")
        return f"{MESES.get(m, m)}/{a}"
    return periodo


def limpar_texto_profundo(texto: str) -> str:
    """Remove artefatos de PDF, texto grudado, disclaimers e lixo."""
    # Fix espaços faltando antes de maiúscula no meio de minúsculas (palavras grudadas)
    texto = re.sub(r'([a-záéíóúãõâêô]{2})([A-ZÁÉÍÓÚÃÕÂÊÔ][a-záéíóúãõâêô]{2})', r'\1 \2', texto)
    # Fix espaços faltando após pontuação
    texto = re.sub(r'([.!?])([A-ZÁÉÍÓÚÃÕÂÊÔ])', r'\1 \2', texto)
    # Fix vírgula/ponto-vírgula grudado
    texto = re.sub(r'([a-záéíóúãõâêô]),([a-záéíóúãõâêô])', r'\1, \2', texto)
    # Remove padrões de lixo
    for pat in LIXO_RE:
        texto = pat.sub('', texto)
    # Remove linhas que são majoritariamente números/tabelas
    linhas = []
    for linha in texto.split('\n'):
        stripped = linha.strip()
        if not stripped:
            continue
        # Pula linhas com mais de 40% de dígitos/símbolos
        chars_uteis = re.sub(r'[\d%,.+\-/()\s|]', '', stripped)
        if len(stripped) > 10 and len(chars_uteis) / max(len(stripped), 1) < 0.4:
            continue
        # Pula linhas muito curtas sem contexto
        if len(stripped) < 20 and not stripped.endswith(('.', ':', '!')):
            continue
        linhas.append(stripped)
    return '\n'.join(linhas)


def extrair_secoes(texto: str) -> dict:
    """Divide o texto em seções baseando-se nos headers."""
    paragrafos = texto.split("\n\n")
    secoes = {}
    secao_atual = "intro"
    conteudo_atual = []

    for p in paragrafos:
        p = p.strip()
        if not p:
            continue
        if len(p) < 80 and p[-1:] not in ".,:;)%" and not re.match(r"^\d", p):
            if conteudo_atual:
                secoes[secao_atual] = "\n".join(conteudo_atual)
            secao_atual = p.lower().strip()
            conteudo_atual = []
        else:
            conteudo_atual.append(p)

    if conteudo_atual:
        secoes[secao_atual] = "\n".join(conteudo_atual)
    return secoes


def encontrar_secao(secoes: dict, palavras_chave: list[str]) -> str:
    """Busca uma seção cujo título contenha uma das palavras-chave."""
    for titulo, conteudo in secoes.items():
        for kw in palavras_chave:
            if kw in titulo:
                texto_limpo = limpar_texto_profundo(conteudo)
                if len(texto_limpo.strip()) < 50:
                    continue
                return texto_limpo
    return ""


def frase_fragmentada(frase: str) -> bool:
    """Detecta frases cortadas/fragmentadas por extração de colunas de PDF."""
    f = frase.strip()
    if not f:
        return True
    # Começa com minúscula (fragmento de frase anterior)
    if f[0].islower() and len(f) < 120:
        return True
    # Qualquer quebra de linha interna (texto de coluna fragmentado)
    if '\n' in f:
        return True
    # Contém disclaimers típicos
    if re.search(r'VOLATILIDADE|RENTABILIDADE PASSADA|LÂMINA|NÃO É LÍQUIDA', f, re.I):
        return True
    # Frase muito longa com duas ideias misturadas (colunas lado a lado)
    palavras = f.split()
    if len(palavras) > 20:
        # Conta transições maiúscula→minúscula no meio (indica frases de colunas diferentes)
        maiusculas_meio = len(re.findall(r'(?<=[a-záéíóúãõâêô,]\s)[A-ZÁÉÍÓÚÃÕÂÊÔ][a-záéíóúãõâêô]{2,}', f))
        if maiusculas_meio >= 3:
            return True
    # Palavras cortadas no final de coluna (ex: "criticame", "resolu", "amb")
    # Detecta palavras que claramente não são completas em português
    tokens = re.findall(r'\b([a-záéíóúãõâêô]{3,})\b', f.lower())
    sinais_corte = 0
    for p in tokens:
        # Termina em consoante rara para fim de palavra em português
        if p[-1] in 'bcdfghjkpqtvwxyz' and p not in (
            'com', 'sem', 'mas', 'dos', 'das', 'nos', 'nas', 'por', 'nem', 'diz',
            'vez', 'bem', 'ter', 'ser', 'ver', 'fez', 'dar', 'sur', 'luz', 'voz',
            'paz', 'dez', 'faz', 'giz', 'noz', 'gás', 'pás', 'nós', 'vós',
            'vol', 'dor', 'cor', 'mar', 'sul', 'mil', 'par', 'for', 'ler',
            'val', 'sol', 'mal', 'tal', 'mel', 'rol', 'fim', 'bom', 'dom',
            'tom', 'som', 'rum', 'gol', 'bol', 'col', 'mol', 'pôr', 'cir'):
            sinais_corte += 1
        # Termina em padrão típico de corte (sílaba aberta incompleta)
        if re.match(r'.*[aeiouáéíóúãõâêô](?:me|ne|se|te|le|re|ge|ce|ve|je|pe|be|de|fe)$', p) and len(p) > 5:
            sinais_corte += 1
    if sinais_corte >= 2:
        return True
    return False


def extrair_frases_relevantes(texto: str, max_frases: int = 4) -> str:
    """Extrai as frases mais relevantes (com conteúdo macro/estratégia)."""
    texto = re.sub(r'\n+', ' ', texto)
    texto = re.sub(r'\s{2,}', ' ', texto)
    frases = re.split(r'(?<=[.!?])\s+', texto)
    resultado = []
    for f in frases:
        f = f.strip()
        if len(f) < 30:
            continue
        # Pula disclaimers
        if re.search(r'regulamento|prospecto|administrador|CVM|CNPJ|exclusivo|SAC|ouvidoria', f, re.I):
            continue
        if re.search(r'@|\.com\.br|\.pdf', f, re.I):
            continue
        # Pula frases de performance/rentabilidade (pertencem à seção de performance)
        if re.search(r'(?:o\s+fundo|rentabilidade|retorno)\s+.{0,30}(?:\d+[,.]?\d*\s*%)', f, re.I):
            continue
        # Pula tabelas residuais
        digitos = len(re.findall(r'[\d%]', f))
        if digitos / max(len(f), 1) > 0.3:
            continue
        # Pula frases com palavras grudadas
        if re.search(r'[a-záéíóúãõâêô]{25,}', f, re.I):
            continue
        # Pula frases com headers misturados
        if re.search(r'(?:Carta\s+Mensal|Atribuição\s*de\s+Performance|Relatório\s+Mensal|Comentário\s+Mensal)', f):
            continue
        # Pula frases fragmentadas por extração de coluna
        if frase_fragmentada(f):
            continue
        resultado.append(f)
        if len(resultado) >= max_frases:
            break
    return " ".join(resultado)


def extrair_pontos_chave(texto: str) -> list[str]:
    """Extrai pontos-chave do texto da carta para uma lista de bullets."""
    texto_limpo = limpar_texto_profundo(texto)
    # Normaliza quebras de linha em espaços para juntar frases cortadas por coluna
    texto_limpo = re.sub(r'\n+', ' ', texto_limpo)
    texto_limpo = re.sub(r'\s{2,}', ' ', texto_limpo)
    frases = re.split(r'(?<=[.!?])\s+', texto_limpo)

    # Scoring: frases com termos relevantes ganham pontos
    termos_macro = ['inflação', 'juros', 'selic', 'fed', 'pib', 'câmbio', 'dólar',
                    'petróleo', 'commodities', 'fiscal', 'monetária', 'crescimento',
                    'recessão', 'desaceleração', 'aceleração', 'emprego', 'desemprego',
                    'oriente médio', 'china', 'eua', 'europa', 'emergentes',
                    'treasury', 'treasuries', 'yield', 'spread', 'crédito',
                    'bolsa', 'ações', 'renda fixa', 'debênture', 'cdi',
                    'risco', 'volatilidade', 'cenário', 'perspectiva',
                    'tarifa', 'guerra', 'conflito', 'acordo', 'negociação',
                    'brent', 'wti', 'energia', 'gás']

    termos_estrategia = ['posição', 'posições', 'comprado', 'vendido', 'aplicado',
                         'tomado', 'hedge', 'alocação', 'exposição', 'livro',
                         'book', 'contribuição', 'detrator', 'destaque',
                         'reduziu', 'aumentou', 'manteve', 'zerou',
                         'rendimento', 'retorno', 'performance', 'resultado']

    scored = []
    for frase in frases:
        frase = frase.strip()
        if len(frase) < 40 or len(frase) > 500:
            continue
        # Pula disclaimers
        if re.search(r'regulamento|prospecto|administrador|CVM|CNPJ|SAC|ouvidoria|exclusivo|passada|garantia', frase, re.I):
            continue
        if re.search(r'@|\.com\.br|\.pdf', frase, re.I):
            continue
        digitos = len(re.findall(r'[\d%]', frase))
        if digitos / max(len(frase), 1) > 0.3:
            continue
        # Rejeita frases com palavras grudadas (>25 chars sem espaço)
        if re.search(r'[a-záéíóúãõâêô]{25,}', frase, re.I):
            continue
        # Rejeita frases com headers de seção misturados no texto
        if re.search(r'(?:Carta\s+Mensal|Atribuição\s*de\s+Performance|Relatório\s+Mensal|Comentário\s+Mensal)', frase):
            continue
        # Rejeita frases de performance/rentabilidade
        if re.search(r'(?:o\s+fundo|rentabilidade|retorno)\s+.{0,30}(?:\d+[,.]?\d*\s*%)', frase, re.I):
            continue
        # Rejeita frases fragmentadas por extração de coluna
        if frase_fragmentada(frase):
            continue

        fl = frase.lower()
        score = 0
        for t in termos_macro:
            if t in fl:
                score += 2
        for t in termos_estrategia:
            if t in fl:
                score += 1.5
        # Penaliza frases genéricas/curtas
        if score == 0:
            continue
        scored.append((score, frase))

    scored.sort(key=lambda x: -x[0])

    # Deduplica: remove frases muito parecidas
    pontos = []
    for _, frase in scored:
        duplicado = False
        for existente in pontos:
            # Compara primeiras 50 chars
            if frase[:50].lower() == existente[:50].lower():
                duplicado = True
                break
        if not duplicado:
            pontos.append(frase)
        if len(pontos) >= 6:
            break

    return pontos


def gerar_resumo_fundo(carta: dict) -> dict:
    """Gera resumo estruturado para um fundo."""
    texto = carta.get("texto_raw") or carta.get("texto_completo", "")
    perf = carta.get("performance", {})
    periodo = carta.get("periodo", "N/D")
    fundo = carta.get("fundo", "")
    gestora = carta.get("gestora", "")

    texto_limpo = limpar_texto_profundo(texto)
    secoes = extrair_secoes(texto_limpo)

    # Performance
    perf_mes = perf.get("mes", "N/D")
    perf_bench = perf.get("benchmark_mes", "N/D")
    perf_ano = perf.get("ano", "N/D")

    if perf_mes != "N/D" and perf_bench != "N/D":
        try:
            diff = float(perf_mes) - float(perf_bench)
            comp = f"+{diff:.2f}pp" if diff > 0 else f"{diff:.2f}pp"
            perf_texto = f"Rentabilidade no mês: {perf_mes}% (CDI: {perf_bench}%, {comp} vs CDI)"
        except ValueError:
            perf_texto = f"Rentabilidade no mês: {perf_mes}% (CDI: {perf_bench}%)"
    elif perf_mes != "N/D":
        perf_texto = f"Rentabilidade no mês: {perf_mes}%"
    else:
        perf_texto = "Rentabilidade do mês não disponível na carta"

    if perf_ano != "N/D":
        try:
            val_ano = float(perf_ano)
            if val_ano > 50:
                perf_ano = "N/D"
            else:
                perf_texto += f". Acumulado no ano: {perf_ano}%"
        except ValueError:
            pass

    # Cenário Macro
    cenario = encontrar_secao(secoes, [
        "cenário", "cenario", "macro", "conjuntura", "ambiente",
        "mercado", "perspectiva", "comentário", "comentario",
        "visão", "visao", "contexto",
    ])
    cenario_resumo = extrair_frases_relevantes(cenario, 3) if cenario else ""

    # Estratégia / Posicionamento
    estrategia = encontrar_secao(secoes, [
        "estratégia", "estrategia", "posicion", "alocação", "alocacao",
        "carteira", "portfolio", "gestão", "gestao", "book", "livro",
    ])
    estrategia_resumo = extrair_frases_relevantes(estrategia, 3) if estrategia else ""

    # Atribuição
    atribuicao = encontrar_secao(secoes, [
        "atribuição", "atribuicao", "contribui", "resultado",
        "performance", "desempenho",
    ])
    atribuicao_resumo = extrair_frases_relevantes(atribuicao, 3) if atribuicao else ""

    # Perspectivas
    perspectivas = encontrar_secao(secoes, [
        "perspectiva", "próximo", "proximo", "futuro", "outlook",
        "junho", "julho", "frente",
    ])
    perspectivas_resumo = extrair_frases_relevantes(perspectivas, 2) if perspectivas else ""

    # Se não achou seções específicas, usa texto geral
    if not cenario_resumo and not estrategia_resumo and not atribuicao_resumo:
        cenario_resumo = extrair_frases_relevantes(texto_limpo, 4)

    # Pontos-chave (novidade!)
    pontos_chave = extrair_pontos_chave(texto)

    # Monta o resumo
    resumo = {
        "periodo": periodo,
        "periodo_legivel": periodo_legivel(periodo),
        "performance": perf_texto,
    }

    if pontos_chave:
        resumo["pontos_chave"] = pontos_chave
    if cenario_resumo:
        resumo["tese_macro"] = cenario_resumo
    if atribuicao_resumo:
        resumo["atribuicao"] = atribuicao_resumo
    if estrategia_resumo:
        resumo["posicionamento"] = estrategia_resumo
    if perspectivas_resumo:
        resumo["observar"] = perspectivas_resumo

    # WhatsApp (limpo, sem repetições)
    linhas_wpp = []
    per_leg = periodo_legivel(periodo)
    linhas_wpp.append(f"*{fundo}* - Carta {per_leg}")
    linhas_wpp.append(perf_texto)

    textos_usados = set()
    for campo in [cenario_resumo, estrategia_resumo, perspectivas_resumo]:
        if campo:
            primeira = re.split(r'(?<=[.!?])\s+', campo)[0]
            if len(primeira) > 20 and primeira not in textos_usados:
                linhas_wpp.append(primeira)
                textos_usados.add(primeira)

    if pontos_chave:
        for ponto in pontos_chave[:2]:
            ponto_curto = re.split(r'(?<=[.!?])\s+', ponto)[0]
            if len(ponto_curto) > 20 and ponto_curto not in textos_usados:
                linhas_wpp.append(f"• {ponto_curto}")
                textos_usados.add(ponto_curto)

    resumo["whatsapp"] = "\n".join(linhas_wpp[:7])

    return resumo


def gerar_todos():
    if not CARTAS_JSON.exists():
        print("Nenhuma carta processada. Rode processar_pdfs.py primeiro.")
        return

    with open(CARTAS_JSON, encoding="utf-8") as f:
        cartas = json.load(f)

    resumos = {}

    gerados = 0
    for carta in cartas:
        nome = carta["fundo"]
        resumo = gerar_resumo_fundo(carta)
        resumos[nome] = resumo
        n_pontos = len(resumo.get("pontos_chave", []))
        gerados += 1
        print(f"  [OK] {nome} - {resumo.get('periodo_legivel', 'N/D')} ({n_pontos} pontos-chave)")

    with open(RESUMOS_JSON, "w", encoding="utf-8") as f:
        json.dump(resumos, f, ensure_ascii=False, indent=2)

    print(f"\n{gerados} resumos gerados. Salvo em {RESUMOS_JSON}")


if __name__ == "__main__":
    gerar_todos()
