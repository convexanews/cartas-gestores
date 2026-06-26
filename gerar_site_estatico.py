"""
Gera site estático a partir do Flask app para deploy no GitHub Pages.
Renderiza todas as páginas como HTML e salva na pasta docs/.
"""
import json
import re
import shutil
import unicodedata
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

BASE = Path(__file__).parent
DOCS = BASE / "docs"
TEMPLATES = BASE / "site" / "templates"
FUNDOS_JSON = BASE / "fundos.json"
CARTAS_JSON = BASE / "output" / "cartas_processadas.json"
RESUMOS_JSON = BASE / "output" / "resumos.json"


def carregar_json(path):
    if not path.exists():
        return [] if path.name.startswith("cartas") or path.name == "fundos.json" else {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def slugify(nome):
    s = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    s = re.sub(r"[^\w\s-]", "", s).strip().lower()
    return re.sub(r"[-\s]+", "-", s)


def fix_links(html, depth=0, slug_map=None):
    prefix = "../" * depth
    html = html.replace('href="/"', f'href="{prefix}index.html"')
    html = html.replace('href="/comparativo"', f'href="{prefix}comparativo/index.html"')
    html = html.replace('href="/whatsapp"', f'href="{prefix}whatsapp/index.html"')
    html = html.replace('href="/upload"', '')
    html = html.replace('<a href="" class="nav-link">Upload</a>', '')
    if slug_map:
        def fix_fundo_link(m):
            raw_name = m.group(1)
            # raw_name is URL-encoded fund name from Jinja urlencode
            from urllib.parse import unquote
            decoded = unquote(raw_name)
            slug = slug_map.get(decoded, slugify(decoded))
            return f'href="{prefix}fundo/{slug}/index.html"'
        html = re.sub(r'href="/fundo/([^"]+)"', fix_fundo_link, html)
    html = re.sub(r'href="/download/fundo/[^"]*"', 'href="#"', html)
    return html


def build():
    fundos = carregar_json(FUNDOS_JSON)
    cartas = carregar_json(CARTAS_JSON)
    resumos = carregar_json(RESUMOS_JSON)
    cartas_por_fundo = {c["fundo"]: c for c in cartas}

    # Build slug map: fund name -> slug
    all_names = [c["fundo"] for c in cartas] + [f["nome"] for f in fundos]
    slug_map = {name: slugify(name) for name in set(all_names)}

    env = Environment(loader=FileSystemLoader(str(TEMPLATES)), autoescape=False)
    env.globals["get_flashed_messages"] = lambda: []

    if DOCS.exists():
        shutil.rmtree(DOCS)
    DOCS.mkdir()

    dados = []
    for fundo in fundos:
        carta = cartas_por_fundo.get(fundo["nome"], {})
        resumo = resumos.get(fundo["nome"], {})
        dados.append({
            "fundo": fundo,
            "carta": carta,
            "resumo": resumo,
            "tem_carta": bool(carta),
            "tem_resumo": bool(resumo),
        })

    total = len(fundos)
    processados = sum(1 for d in dados if d["tem_carta"])
    resumidos = sum(1 for d in dados if d["tem_resumo"])
    dados_com_carta = [d for d in dados if d["tem_carta"]]

    # INDEX
    tpl = env.get_template("index.html")
    html = tpl.render(dados=dados_com_carta, total=total, processados=processados, resumidos=resumidos)
    html = fix_links(html, depth=0, slug_map=slug_map)
    (DOCS / "index.html").write_text(html, encoding="utf-8")
    print(f"  [OK] index.html ({len(dados_com_carta)} fundos)")

    # FUNDO PAGES (depth=2: docs/fundo/slug/)
    fundo_dir = DOCS / "fundo"
    fundo_dir.mkdir()
    tpl = env.get_template("fundo.html")
    for carta in cartas:
        nome = carta["fundo"]
        resumo = resumos.get(nome, {})
        fundo = next((f for f in fundos if f["nome"] == nome), {"nome": nome})
        html = tpl.render(fundo=fundo, carta=carta, resumo=resumo)
        html = fix_links(html, depth=2, slug_map=slug_map)
        slug = slug_map[nome]
        page_dir = fundo_dir / slug
        page_dir.mkdir(exist_ok=True)
        (page_dir / "index.html").write_text(html, encoding="utf-8")
    print(f"  [OK] {len(cartas)} paginas de fundos")

    # COMPARATIVO
    tpl = env.get_template("comparativo.html")
    dados_comp = [{"carta": c, "resumo": resumos.get(c["fundo"], {})} for c in cartas]
    html = tpl.render(dados=dados_comp)
    html = fix_links(html, depth=1, slug_map=slug_map)
    comp_dir = DOCS / "comparativo"
    comp_dir.mkdir()
    (comp_dir / "index.html").write_text(html, encoding="utf-8")
    print("  [OK] comparativo")

    # WHATSAPP
    tpl = env.get_template("whatsapp.html")
    html = tpl.render(resumos=resumos)
    html = fix_links(html, depth=1, slug_map=slug_map)
    wpp_dir = DOCS / "whatsapp"
    wpp_dir.mkdir()
    (wpp_dir / "index.html").write_text(html, encoding="utf-8")
    print("  [OK] whatsapp")

    (DOCS / ".nojekyll").write_text("", encoding="utf-8")
    print(f"\nSite estatico gerado em {DOCS}")


if __name__ == "__main__":
    build()
