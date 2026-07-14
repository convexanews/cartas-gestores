"""
Gera PDFs de resumo individuais e consolidados das cartas dos gestores.
Usa fpdf2 para criar PDFs com visual profissional.
"""
import json
from pathlib import Path

from fpdf import FPDF

PASTA_OUTPUT = Path(__file__).parent / "output"
PASTA_PDFS_RESUMO = PASTA_OUTPUT / "resumos_pdf"
CARTAS_JSON = PASTA_OUTPUT / "cartas_processadas.json"
RESUMOS_JSON = PASTA_OUTPUT / "resumos.json"
FUNDOS_JSON = Path(__file__).parent / "fundos.json"

MESES = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março", "04": "Abril",
    "05": "Maio", "06": "Junho", "07": "Julho", "08": "Agosto",
    "09": "Setembro", "10": "Outubro", "11": "Novembro", "12": "Dezembro",
}


def periodo_extenso(periodo: str) -> str:
    if "/" in periodo:
        m, a = periodo.split("/")
        return f"{MESES.get(m, m)} de {a}"
    return periodo


class ResumoPDF(FPDF):

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font("Arial", "", fname="C:/Windows/Fonts/arial.ttf")
        self.add_font("Arial", "B", fname="C:/Windows/Fonts/arialbd.ttf")

    def header(self):
        self.set_font("Arial", "B", 9)
        self.set_text_color(150, 150, 150)
        self.cell(0, 8, "Cartas dos Gestores — Resumo Executivo", align="R")
        self.ln(4)
        self.set_draw_color(220, 220, 220)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 7)
        self.set_text_color(160, 160, 160)
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}}", align="C")

    def titulo_fundo(self, nome: str, gestora: str, categoria: str, periodo: str):
        self.set_font("Arial", "B", 16)
        self.set_text_color(26, 29, 43)
        self.multi_cell(0, 8, nome)
        self.set_font("Arial", "", 10)
        self.set_text_color(107, 112, 128)
        self.cell(0, 6, f"{gestora}  |  {categoria}  |  {periodo_extenso(periodo)}")
        self.ln(10)

    def secao(self, titulo: str):
        self.set_font("Arial", "B", 11)
        self.set_text_color(37, 99, 235)
        self.cell(0, 7, titulo.upper())
        self.ln(2)
        self.set_draw_color(37, 99, 235)
        self.line(10, self.get_y(), 60, self.get_y())
        self.ln(5)

    def texto(self, conteudo: str):
        self.set_font("Arial", "", 10)
        self.set_text_color(55, 55, 55)
        self.multi_cell(0, 5.5, conteudo)
        self.ln(3)

    def bullet(self, texto_bullet: str):
        self.set_font("Arial", "", 10)
        self.set_text_color(55, 55, 55)
        x = self.get_x()
        self.cell(6, 5.5, "•")
        self.multi_cell(0, 5.5, texto_bullet)
        self.ln(1.5)

    def performance_box(self, perf_mes, perf_cdi, perf_ano):
        y_start = self.get_y()
        box_h = 20
        col_w = 60

        for i, (label, val) in enumerate([
            ("RENTAB. MÊS", perf_mes),
            ("CDI NO MÊS", perf_cdi),
            ("ACUM. ANO", perf_ano),
        ]):
            x = 10 + i * col_w + i * 3
            self.set_xy(x, y_start)
            self.set_fill_color(248, 249, 251)
            self.set_draw_color(232, 234, 239)
            self.rect(x, y_start, col_w, box_h, style="DF")

            self.set_xy(x, y_start + 2)
            self.set_font("Arial", "B", 14)
            if val and val != "N/D":
                try:
                    fv = float(val)
                    if fv >= 0:
                        self.set_text_color(5, 150, 105)
                        display = f"+{val}%"
                    else:
                        self.set_text_color(220, 38, 38)
                        display = f"{val}%"
                except ValueError:
                    self.set_text_color(100, 100, 100)
                    display = val
            else:
                self.set_text_color(155, 161, 176)
                display = "N/D"
            self.cell(col_w, 9, display, align="C")

            self.set_xy(x, y_start + 12)
            self.set_font("Arial", "", 7)
            self.set_text_color(155, 161, 176)
            self.cell(col_w, 5, label, align="C")

        self.set_y(y_start + box_h + 8)

    def separador(self):
        self.ln(3)
        self.set_draw_color(232, 234, 239)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)


def gerar_pdf_fundo(nome: str, carta: dict, resumo: dict, fundo_info: dict) -> Path:
    """Gera PDF de resumo para um fundo individual."""
    pdf = ResumoPDF()
    pdf.alias_nb_pages()
    pdf.add_page()

    gestora = fundo_info.get("gestora", carta.get("gestora", "N/D"))
    categoria = fundo_info.get("categoria", carta.get("categoria", "N/D"))
    periodo = resumo.get("periodo", carta.get("periodo", "N/D"))

    pdf.titulo_fundo(nome, gestora, categoria, periodo)

    # Performance boxes
    perf = carta.get("performance", {})
    perf_mes = perf.get("mes", "N/D")
    perf_cdi = perf.get("benchmark_mes", "N/D")
    perf_ano = perf.get("ano", "N/D")
    try:
        if perf_ano != "N/D" and float(perf_ano) > 50:
            perf_ano = "N/D"
    except ValueError:
        pass
    pdf.performance_box(perf_mes, perf_cdi, perf_ano)

    # Pontos-chave
    pontos = resumo.get("pontos_chave", [])
    if pontos:
        pdf.secao("Pontos-Chave")
        for ponto in pontos:
            pdf.bullet(ponto)
        pdf.ln(3)

    # Seções do resumo
    secoes = [
        ("tese_macro", "Cenário Macroeconômico"),
        ("atribuicao", "Atribuição de Performance"),
        ("posicionamento", "Posicionamento e Estratégia"),
        ("observar", "Perspectivas"),
    ]
    for campo, titulo in secoes:
        conteudo = resumo.get(campo, "")
        if conteudo and len(conteudo) > 30:
            pdf.secao(titulo)
            pdf.texto(conteudo)

    # Salva
    PASTA_PDFS_RESUMO.mkdir(parents=True, exist_ok=True)
    nome_safe = nome.lower().replace(" ", "_").replace("/", "_")
    nome_safe = "".join(c for c in nome_safe if c.isalnum() or c == '_')
    caminho = PASTA_PDFS_RESUMO / f"resumo_{nome_safe}.pdf"
    pdf.output(str(caminho))
    return caminho


def gerar_pdf_consolidado() -> Path:
    """Gera PDF consolidado com todos os fundos."""
    if not RESUMOS_JSON.exists() or not CARTAS_JSON.exists():
        print("Processe as cartas e gere resumos antes.")
        return None

    with open(CARTAS_JSON, encoding="utf-8") as f:
        cartas = json.load(f)
    with open(RESUMOS_JSON, encoding="utf-8") as f:
        resumos = json.load(f)
    with open(FUNDOS_JSON, encoding="utf-8") as f:
        fundos = json.load(f)

    fundos_map = {f["nome"]: f for f in fundos}
    cartas_map = {c["fundo"]: c for c in cartas}

    pdf = ResumoPDF()
    pdf.alias_nb_pages()

    # Capa
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(26, 29, 43)
    pdf.cell(0, 14, "Cartas dos Gestores", align="C")
    pdf.ln(12)
    pdf.set_font("Arial", "", 14)
    pdf.set_text_color(107, 112, 128)
    pdf.cell(0, 8, "Resumo Executivo Consolidado", align="C")
    pdf.ln(8)

    # Descobre período predominante
    periodos = [r.get("periodo_legivel", "") for r in resumos.values() if r.get("periodo_legivel")]
    if periodos:
        from collections import Counter
        periodo_mais_comum = Counter(periodos).most_common(1)[0][0]
        pdf.cell(0, 8, periodo_mais_comum, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(155, 161, 176)
    pdf.cell(0, 8, f"{len(resumos)} fundos analisados", align="C")

    # Tabela resumo
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(26, 29, 43)
    pdf.cell(0, 10, "Quadro Comparativo")
    pdf.ln(10)

    # Header da tabela
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(248, 249, 251)
    pdf.set_text_color(107, 112, 128)
    col_w = [70, 25, 25, 25, 45]
    headers = ["FUNDO", "PERÍODO", "RENT. MÊS", "CDI MÊS", "CATEGORIA"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(55, 55, 55)
    for nome_fundo, resumo in resumos.items():
        carta = cartas_map.get(nome_fundo, {})
        fundo = fundos_map.get(nome_fundo, {})
        perf = carta.get("performance", {})
        nome_display = nome_fundo[:30] + "..." if len(nome_fundo) > 30 else nome_fundo
        pdf.cell(col_w[0], 7, nome_display, border=1)
        pdf.cell(col_w[1], 7, resumo.get("periodo_legivel", "N/D"), border=1, align="C")
        pm = perf.get("mes", "N/D")
        pdf.cell(col_w[2], 7, f"{pm}%" if pm != "N/D" else "N/D", border=1, align="C")
        pb = perf.get("benchmark_mes", "N/D")
        pdf.cell(col_w[3], 7, f"{pb}%" if pb != "N/D" else "N/D", border=1, align="C")
        pdf.cell(col_w[4], 7, fundo.get("categoria", "N/D"), border=1, align="C")
        pdf.ln()

    # Páginas individuais por fundo
    for nome_fundo, resumo in resumos.items():
        carta = cartas_map.get(nome_fundo, {})
        fundo = fundos_map.get(nome_fundo, {})
        pdf.add_page()

        gestora = fundo.get("gestora", carta.get("gestora", "N/D"))
        categoria = fundo.get("categoria", carta.get("categoria", "N/D"))
        periodo = resumo.get("periodo", "N/D")

        pdf.titulo_fundo(nome_fundo, gestora, categoria, periodo)

        perf = carta.get("performance", {})
        perf_mes = perf.get("mes", "N/D")
        perf_cdi = perf.get("benchmark_mes", "N/D")
        perf_ano = perf.get("ano", "N/D")
        try:
            if perf_ano != "N/D" and float(perf_ano) > 50:
                perf_ano = "N/D"
        except ValueError:
            pass
        pdf.performance_box(perf_mes, perf_cdi, perf_ano)

        pontos = resumo.get("pontos_chave", [])
        if pontos:
            pdf.secao("Pontos-Chave")
            for ponto in pontos:
                pdf.bullet(ponto)
            pdf.ln(2)

        secoes_det = [
            ("tese_macro", "Cenário Macro"),
            ("atribuicao", "Atribuição"),
            ("posicionamento", "Posicionamento"),
            ("observar", "Perspectivas"),
        ]
        for campo, titulo in secoes_det:
            conteudo = resumo.get(campo, "")
            if conteudo and len(conteudo) > 30:
                pdf.secao(titulo)
                pdf.texto(conteudo)

    PASTA_PDFS_RESUMO.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_PDFS_RESUMO / "resumo_consolidado.pdf"
    pdf.output(str(caminho))
    print(f"PDF consolidado salvo em: {caminho}")
    return caminho


def gerar_todos_pdfs():
    """Gera PDFs individuais + consolidado."""
    if not RESUMOS_JSON.exists() or not CARTAS_JSON.exists():
        print("Processe as cartas e gere resumos antes.")
        return

    with open(CARTAS_JSON, encoding="utf-8") as f:
        cartas = json.load(f)
    with open(RESUMOS_JSON, encoding="utf-8") as f:
        resumos = json.load(f)
    with open(FUNDOS_JSON, encoding="utf-8") as f:
        fundos = json.load(f)

    fundos_map = {f_["nome"]: f_ for f_ in fundos}
    cartas_map = {c["fundo"]: c for c in cartas}

    PASTA_PDFS_RESUMO.mkdir(parents=True, exist_ok=True)

    for nome, resumo in resumos.items():
        carta = cartas_map.get(nome, {})
        fundo = fundos_map.get(nome, {})
        caminho = gerar_pdf_fundo(nome, carta, resumo, fundo)
        print(f"  [PDF] {nome} -> {caminho.name}")

    gerar_pdf_consolidado()
    print(f"\nTodos os PDFs gerados em: {PASTA_PDFS_RESUMO}")


if __name__ == "__main__":
    gerar_todos_pdfs()
