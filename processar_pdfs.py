"""
Processador de Cartas de Gestores
Lê PDFs da pasta /pdfs, extrai texto e salva em JSON estruturado.
"""
import json
import os
import re
import sys
from pathlib import Path

import pdfplumber

PASTA_PDFS = Path(__file__).parent / "pdfs"
PASTA_OUTPUT = Path(__file__).parent / "output"
FUNDOS_JSON = Path(__file__).parent / "fundos.json"


def separar_colunas(pagina) -> str:
    """Detecta e separa texto em duas colunas usando layout mode."""
    t = pagina.extract_text(layout=True)
    if not t:
        return ""
    linhas = t.split("\n")
    largura = max((len(l) for l in linhas), default=0)
    if largura < 80:
        return pagina.extract_text() or ""

    # Encontra a posição do gap entre colunas
    # Conta espaços em cada posição em linhas com texto dos dois lados
    gap_counts = [0] * largura
    linhas_com_texto = 0
    for linha in linhas:
        if len(linha) < largura * 0.5:
            continue
        for i in range(len(linha)):
            if linha[i] == ' ':
                gap_counts[i] += 1
        linhas_com_texto += 1

    if linhas_com_texto < 3:
        return pagina.extract_text() or ""

    # Procura faixa de espaços consistente no meio (entre 30% e 70% da largura)
    melhor_gap = -1
    melhor_score = 0
    inicio = int(largura * 0.25)
    fim = int(largura * 0.75)
    for i in range(inicio, fim):
        score = gap_counts[i]
        if score > melhor_score:
            melhor_score = score
            melhor_gap = i

    # Se menos de 60% das linhas têm espaço nessa posição, não é duas colunas
    if melhor_gap < 0 or melhor_score < linhas_com_texto * 0.6:
        return pagina.extract_text() or ""

    # Expande o gap para encontrar bordas reais
    gap_start = melhor_gap
    gap_end = melhor_gap
    while gap_start > 0 and gap_counts[gap_start - 1] > linhas_com_texto * 0.5:
        gap_start -= 1
    while gap_end < largura - 1 and gap_counts[gap_end + 1] > linhas_com_texto * 0.5:
        gap_end += 1

    if gap_end - gap_start < 3:
        return pagina.extract_text() or ""

    col_esq = []
    col_dir = []
    for linha in linhas:
        esq = linha[:gap_start].rstrip() if len(linha) > gap_start else linha.rstrip()
        dir_ = linha[gap_end + 1:].strip() if len(linha) > gap_end else ""
        col_esq.append(esq)
        col_dir.append(dir_)

    texto_esq = "\n".join(l for l in col_esq)
    texto_dir = "\n".join(l for l in col_dir)
    return texto_esq + "\n\n" + texto_dir


def extrair_texto_raw(caminho_pdf: Path, max_pages: int = 0) -> str:
    """Extrai texto simples (sem separação de colunas)."""
    texto = []
    with pdfplumber.open(caminho_pdf) as pdf:
        pages = pdf.pages if max_pages == 0 else pdf.pages[:max_pages]
        for pagina in pages:
            t = pagina.extract_text() or ""
            if t:
                texto.append(t)
    return "\n".join(texto)


def extrair_texto_pdf(caminho_pdf: Path) -> str:
    texto = []
    with pdfplumber.open(caminho_pdf) as pdf:
        for pagina in pdf.pages:
            t = separar_colunas(pagina)
            if t:
                texto.append(t)
    raw = "\n".join(texto)
    raw = limpar_texto_grudado(raw)
    return formatar_paragrafos(raw)


def limpar_artefatos(texto: str) -> str:
    # Corrige caracteres duplicados do pdfplumber (ex: "wwwwww..lleeggaaccyy" -> "www.legacy")
    resultado = []
    i = 0
    while i < len(texto):
        ch = texto[i]
        if i + 1 < len(texto) and texto[i + 1] == ch:
            resultado.append(ch)
            i += 2
        else:
            resultado.append(ch)
            i += 1
    dedup = "".join(resultado)
    if len(dedup) < len(texto) * 0.75:
        return dedup
    return texto


def limpar_texto_espacado(texto: str) -> str:
    # Corrige texto com letras espaçadas: "s t r a t é g i a" -> "estratégia"
    return re.sub(
        r'(?<![a-zA-ZÀ-ú])([a-zA-ZÀ-ú])((?:\s[a-zA-ZÀ-ú]){3,})(?![a-zA-ZÀ-ú])',
        lambda m: m.group(0).replace(" ", ""),
        texto,
    )


def limpar_texto_grudado(texto: str) -> str:
    """Corrige palavras grudadas vindas de PDFs com colunas mal parseadas."""
    # Insere espaço antes de maiúscula precedida de minúscula (mínimo 2 chars de cada lado)
    texto = re.sub(r'([a-záéíóúãõâêô]{2})([A-ZÁÉÍÓÚÃÕÂÊÔ][a-záéíóúãõâêô]{2})', r'\1 \2', texto)
    # Insere espaço após pontuação grudada
    texto = re.sub(r'([.!?])([A-ZÁÉÍÓÚÃÕÂÊÔ])', r'\1 \2', texto)
    texto = re.sub(r'([a-záéíóúãõâêô]),([a-záéíóúãõâêô])', r'\1, \2', texto)
    return texto


def formatar_paragrafos(texto: str) -> str:
    linhas = texto.split("\n")
    paragrafos = []
    atual = []
    for linha in linhas:
        stripped = linha.strip()
        if not stripped:
            if atual:
                paragrafos.append(" ".join(atual))
                atual = []
            continue
        # Detecta e limpa linhas com caracteres duplicados
        tem_duplo = sum(1 for a, b in zip(stripped, stripped[1:]) if a == b) / max(len(stripped) - 1, 1)
        if tem_duplo > 0.4:
            cleaned = limpar_artefatos(stripped)
            if cleaned != stripped:
                stripped = cleaned
        # Corrige letras espaçadas ("s t r a t é g i a" -> "estratégia")
        stripped = limpar_texto_espacado(stripped)
        # Remove linhas-lixo: só símbolos/números/%, ou muito curtas sem sentido
        if re.match(r"^[\d\s%,.\-+/()]+$", stripped):
            continue
        if re.match(r"^\d{1,3}$", stripped):
            continue
        if re.match(r"^(p[aá]gina|page)\s+\d+", stripped, re.I):
            continue
        # Linha curta que termina sem pontuação = provavelmente título/header
        if len(stripped) < 60 and stripped[-1:] not in ".,:;)%":
            if atual:
                paragrafos.append(" ".join(atual))
                atual = []
            paragrafos.append(stripped)
            continue
        atual.append(stripped)
    if atual:
        paragrafos.append(" ".join(atual))
    # Remove parágrafos duplicados consecutivos (headers repetidos de páginas)
    dedup = []
    for p in paragrafos:
        if not dedup or p != dedup[-1]:
            dedup.append(p)
    return "\n\n".join(dedup)


def detectar_fundo(nome_arquivo: str, fundos: list[dict]) -> dict | None:
    nome = nome_arquivo.lower().replace("_", " ").replace("-", " ")
    melhor = None
    melhor_score = 0
    for fundo in fundos:
        palavras = fundo["nome"].lower().split()
        score = sum(1 for p in palavras if p in nome)
        if score > melhor_score:
            melhor_score = score
            melhor = fundo
    if melhor_score >= 2:
        return melhor
    return None


def extrair_performance(texto: str) -> dict:
    perf = {}
    txt = texto.lower()

    padroes_mes = [
        r"rentabilidade\s+(?:no\s+)?m[eê]s[:\s]+([+-]?\d+[.,]\d+)\s*%",
        r"fundo\s+(?:no\s+)?m[eê]s[:\s]+([+-]?\d+[.,]\d+)\s*%",
        r"retorno\s+(?:no\s+)?m[eê]s[:\s]+([+-]?\d+[.,]\d+)\s*%",
        r"(?:resultado|performance)\s+(?:no\s+)?m[eê]s[:\s]+([+-]?\d+[.,]\d+)\s*%",
        # "rendimento de X,XX% no mês" ou "rendeu X,XX%"
        r"rendimento\s+de\s+([+-]?\d+[.,]\d+)\s*%\s+no\s+m[eê]s",
        r"rendeu\s+([+-]?\d+[.,]\d+)\s*%\s+(?:no|em)\s+m",
        # Tabelas: "Fundo¹ X,XX%" (Itau, SPX)
        r"fundo[¹²³\d]*\s+([+-]?\d+[.,]\d+)\s*%",
        # "resultado de X,XX%"
        r"resultado\s+de\s+([+-]?\d+[.,]\d+)\s*%",
        # Tabelas com header "Mês" ou "Mai/26" etc
        r"(?:mai|abr|mar|fev|jan|jun|jul|ago|set|out|nov|dez)[/\s]*\d{2}\s+([+-]?\d+[.,]\d+)\s*%",
        r"m[eê]s\s+([+-]?\d+[.,]\d+)\s*%",
        # "teve rendimento de X,XX% no mês e de Y,YY% no ano"
        r"rendimento\s+de\s+([+-]?\d+[.,]\d+)\s*%",
        # "retorno de +X,XX%" (SPX)
        r"retorno\s+de\s+\+?([+-]?\d+[.,]\d+)\s*%",
    ]
    for padrao in padroes_mes:
        m = re.search(padrao, txt)
        if m:
            # Ignora "% do CDI"
            pos_fim = m.end()
            contexto_depois = txt[pos_fim:pos_fim+20]
            if "do cdi" in contexto_depois.lower():
                continue
            val = m.group(1).replace(",", ".")
            if 0 < abs(float(val)) < 30:
                perf["mes"] = val
                break

    padroes_ano = [
        r"(?:ano|ytd|acumulado\s+(?:no\s+)?ano)[:\s]+([+-]?\d+[.,]\d+)\s*%",
        # "X,XX% no mês e de Y,YY% no ano"
        r"no\s+m[eê]s\s+e\s+de\s+([+-]?\d+[.,]\d+)\s*%\s+no\s+ano",
        r"12\s*meses[:\s]+([+-]?\d+[.,]\d+)\s*%",
    ]
    for padrao in padroes_ano:
        m = re.search(padrao, txt)
        if m:
            # Verifica se é "% do CDI" — nesse caso não é retorno absoluto
            pos_fim = m.end()
            contexto_depois = txt[pos_fim:pos_fim+20]
            if "do cdi" in contexto_depois.lower() or "% do cdi" in contexto_depois.lower():
                continue
            val = m.group(1).replace(",", ".")
            # Retorno anual razoável: entre -50% e +50%
            try:
                if abs(float(val)) > 50:
                    continue
            except ValueError:
                continue
            perf["ano"] = val
            break

    padroes_cdi = [
        r"cdi\s+(?:no\s+)?m[eê]s[:\s]+([+-]?\d+[.,]\d+)\s*%",
        r"bench\s+([+-]?\d+[.,]\d+)\s*%",
        r"cdi[:\s]+([+-]?\d+[.,]\d+)\s*%",
        r"benchmark[:\s]+([+-]?\d+[.,]\d+)\s*%",
    ]
    for padrao in padroes_cdi:
        m = re.search(padrao, txt)
        if m:
            val = m.group(1).replace(",", ".")
            if 0 < abs(float(val)) < 30:
                perf["benchmark_mes"] = val
                break

    return perf


def extrair_periodo(texto: str) -> str:
    meses = {
        "janeiro": "01", "fevereiro": "02", "março": "03", "marco": "03",
        "abril": "04", "maio": "05", "junho": "06", "julho": "07",
        "agosto": "08", "setembro": "09", "outubro": "10",
        "novembro": "11", "dezembro": "12",
    }
    cabecalho = texto[:2000].lower()
    # Formato "maio, 2026" ou "maio/2026" ou "maio de 2026"
    for nome_mes, num in meses.items():
        padrao = rf"{nome_mes}\s*[,/]\s*(\d{{4}})"
        m = re.search(padrao, cabecalho)
        if m:
            return f"{num}/{m.group(1)}"
    # Contexto: carta/relatório + mês + ano
    for nome_mes, num in meses.items():
        padrao = rf"(?:carta\s+(?:mensal|do\s+gestor)|relat[oó]rio\s+mensal|refer[eê]ncia|coment[aá]rio\s+mensal).*?{nome_mes}\s*(?:de\s+|/\s*)?(\d{{4}})"
        m = re.search(padrao, cabecalho, re.DOTALL)
        if m:
            return f"{num}/{m.group(1)}"
    # Mês + ano solto (incluindo só espaço entre eles, ex: "MAIO 2026", "Maio  2026")
    for nome_mes, num in meses.items():
        padrao = rf"{nome_mes}\s*(?:de\s+|/\s*)?(\d{{4}})"
        m = re.search(padrao, cabecalho)
        if m:
            return f"{num}/{m.group(1)}"
    # Mês e ano separados por espaços grandes (layout mode de PDF)
    for nome_mes, num in meses.items():
        padrao = rf"{nome_mes}\s+(\d{{4}})"
        m = re.search(padrao, cabecalho)
        if m:
            return f"{num}/{m.group(1)}"
    # MM/AAAA apenas com anos plausíveis (2020-2029)
    m = re.search(r"(0[1-9]|1[0-2])/(202[0-9])", cabecalho)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return "N/D"


def processar_todos():
    with open(FUNDOS_JSON, encoding="utf-8") as f:
        fundos = json.load(f)

    PASTA_OUTPUT.mkdir(exist_ok=True)
    resultados = []
    pdfs = sorted(PASTA_PDFS.glob("*.pdf"))

    if not pdfs:
        print(f"Nenhum PDF encontrado em {PASTA_PDFS}")
        print("Coloque os PDFs das cartas na pasta 'pdfs/' e rode novamente.")
        return

    print(f"Encontrados {len(pdfs)} PDFs para processar.\n")

    for pdf_path in pdfs:
        print(f"Processando: {pdf_path.name}")
        texto = extrair_texto_pdf(pdf_path)
        texto_raw = extrair_texto_raw(pdf_path, max_pages=0)
        texto_raw_head = extrair_texto_raw(pdf_path, max_pages=3)
        if not texto.strip() and not texto_raw.strip():
            print(f"  AVISO: PDF vazio ou não extraível - {pdf_path.name}")
            continue

        if not texto.strip():
            texto = texto_raw

        fundo = detectar_fundo(pdf_path.stem, fundos)
        nome_fundo = fundo["nome"] if fundo else pdf_path.stem
        gestora = fundo["gestora"] if fundo else "N/D"
        categoria = fundo["categoria"] if fundo else "N/D"
        benchmark = fundo["benchmark"] if fundo else "CDI"

        performance = extrair_performance(texto)
        periodo = extrair_periodo(texto)
        # Fallback: tenta extrair do texto raw se não achou
        if periodo == "N/D":
            periodo = extrair_periodo(texto_raw_head)
        if not performance.get("mes"):
            perf_raw = extrair_performance(texto_raw)
            for k, v in perf_raw.items():
                if k not in performance:
                    performance[k] = v

        resultado = {
            "arquivo": pdf_path.name,
            "fundo": nome_fundo,
            "gestora": gestora,
            "categoria": categoria,
            "benchmark": benchmark,
            "periodo": periodo,
            "performance": performance,
            "texto_completo": texto[:15000],
            "texto_raw": texto_raw[:15000],
            "tamanho_texto": len(texto),
        }
        resultados.append(resultado)
        print(f"  -> {nome_fundo} | Período: {periodo} | Perf mês: {performance.get('mes', 'N/D')}%")

    output_path = PASTA_OUTPUT / "cartas_processadas.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)

    print(f"\n{len(resultados)} cartas processadas. Salvo em {output_path}")
    return resultados


if __name__ == "__main__":
    processar_todos()
