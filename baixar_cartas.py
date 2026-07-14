"""
Baixador de Cartas dos Gestores
Tenta baixar automaticamente os PDFs das fontes mapeadas.
"""
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

import requests

BASE = Path(__file__).parent
FONTES_JSON = BASE / "fontes.json"
PASTA_PDFS = BASE / "pdfs"

MESES_PT = {
    1: ("Janeiro", "Jan"), 2: ("Fevereiro", "Fev"), 3: ("Março", "Mar"),
    4: ("Abril", "Abr"), 5: ("Maio", "Mai"), 6: ("Junho", "Jun"),
    7: ("Julho", "Jul"), 8: ("Agosto", "Ago"), 9: ("Setembro", "Set"),
    10: ("Outubro", "Out"), 11: ("Novembro", "Nov"), 12: ("Dezembro", "Dez"),
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36",
    "Accept": "application/pdf,*/*",
}


def mes_referencia():
    hoje = datetime.now()
    ref = hoje.replace(day=1) - timedelta(days=1)
    return ref.month, ref.year


def baixar_pdf(url: str, destino: Path) -> bool:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=30, allow_redirects=True)
        if resp.status_code == 200 and len(resp.content) > 5000:
            content_type = resp.headers.get("content-type", "")
            if "pdf" in content_type or resp.content[:5] == b"%PDF-":
                destino.write_bytes(resp.content)
                print(f"    OK: {destino.name} ({len(resp.content)//1024} KB)")
                return True
            else:
                print(f"    AVISO: Não é PDF (content-type: {content_type})")
        else:
            print(f"    FALHA: HTTP {resp.status_code} ou arquivo muito pequeno")
    except Exception as e:
        print(f"    ERRO: {e}")
    return False


def nome_arquivo(fundo: str, mes: int, ano: int) -> str:
    nome = fundo.lower()
    nome = re.sub(r"[^a-z0-9]+", "_", nome).strip("_")
    return f"{nome}_{ano}{mes:02d}.pdf"


def tentar_urls_kapitalo(mes: int, ano: int) -> list[str]:
    nome_mes = MESES_PT[mes][0]
    return [
        f"https://www.kapitalo.com.br/wp-content/uploads/2022/09/Carta-do-Gestor_K10-{nome_mes}{ano}.pdf",
        f"https://www.kapitalo.com.br/wp-content/uploads/2022/09/Carta-K10-{nome_mes}-{ano}.pdf",
        f"https://www.kapitalo.com.br/wp-content/uploads/2022/09/Carta-do-Gestor_K10_{nome_mes}{ano}.pdf",
    ]


def tentar_urls_genoa(mes: int, ano: int) -> list[str]:
    abrev = MESES_PT[mes][1]
    ano_abrev = str(ano)[2:]
    return [
        f"https://www.genoacapital.com.br/docs/CartaMensalGenoaCapital_{abrev}{ano_abrev}.pdf",
        f"https://www.genoacapital.com.br/docs/CartaMensal_GenoaCapital_{abrev}{ano_abrev}.pdf",
    ]


def tentar_urls_legacy(mes: int, ano: int) -> list[str]:
    return [
        f"https://legacywebsite.blob.core.windows.net/site/cartamensal/{ano}/{ano}{mes:02d}_CartaMensal.pdf",
        f"https://legacywebsite.blob.core.windows.net/site/cartamensal/{ano}{mes:02d}_CartaMensal.pdf",
    ]


def tentar_urls_jgp(mes: int, ano: int) -> list[str]:
    abrev = MESES_PT[mes][1]
    ano_abrev = str(ano)[2:]
    return [
        f"https://jgp.com.br/wp-content/uploads/{ano}/{mes:02d}/JGP_Relatorio-de-Gestao_Fundos-de-Credito_{abrev}{ano_abrev}.pdf",
        f"https://jgp.com.br/wp-content/uploads/{ano}/{mes:02d + 1 if mes < 12 else 1:02d}/JGP_Relatorio-de-Gestao_Fundos-de-Credito_{abrev}{ano_abrev}.pdf",
    ]


def baixar_todos():
    PASTA_PDFS.mkdir(exist_ok=True)
    with open(FONTES_JSON, encoding="utf-8") as f:
        fontes = json.load(f)

    mes, ano = mes_referencia()
    nome_mes = MESES_PT[mes][0]
    print(f"Mês de referência: {nome_mes}/{ano}\n")

    resultados = {"ok": [], "falha": [], "manual": []}

    for fonte in fontes:
        fundo = fonte["fundo"]
        tipo = fonte["tipo"]
        print(f"\n{'='*60}")
        print(f"  {fundo}")
        print(f"  Tipo: {tipo}")
        print(f"{'='*60}")

        destino = PASTA_PDFS / nome_arquivo(fundo, mes, ano)
        if destino.exists():
            print(f"  Já existe: {destino.name}")
            resultados["ok"].append(fundo)
            continue

        sucesso = False

        if tipo == "pdf_fixo" and fonte.get("padrao_pdf"):
            print(f"  Tentando URL fixa...")
            sucesso = baixar_pdf(fonte["padrao_pdf"], destino)

        elif tipo == "pdf_direto":
            urls = []
            if "kapitalo" in fundo.lower():
                urls = tentar_urls_kapitalo(mes, ano)
            elif "genoa" in fundo.lower():
                urls = tentar_urls_genoa(mes, ano)
            elif "legacy" in fundo.lower():
                urls = tentar_urls_legacy(mes, ano)
            elif fonte.get("padrao_pdf"):
                url = fonte["padrao_pdf"]
                url = url.replace("{Ano}", str(ano))
                url = url.replace("{AnoAbrev}", str(ano)[2:])
                url = url.replace("{MesNum}", f"{mes:02d}")
                url = url.replace("{MesNome}", nome_mes)
                url = url.replace("{MesAbrev}", MESES_PT[mes][1])
                urls = [url]

            for url in urls:
                print(f"  Tentando: {url}")
                sucesso = baixar_pdf(url, destino)
                if sucesso:
                    break

        if sucesso:
            resultados["ok"].append(fundo)
        elif tipo in ("pagina_com_links", "plataforma", "cvm"):
            print(f"  -> Requer download manual.")
            if fonte.get("pagina_cartas"):
                print(f"     Página: {fonte['pagina_cartas']}")
            if fonte.get("notas"):
                print(f"     Nota: {fonte['notas']}")
            resultados["manual"].append(fundo)
        else:
            resultados["falha"].append(fundo)

    print(f"\n\n{'='*60}")
    print(f"RESULTADO FINAL")
    print(f"{'='*60}")
    print(f"  Baixados automaticamente: {len(resultados['ok'])}")
    for f in resultados["ok"]:
        print(f"    [OK] {f}")
    print(f"\n  Requerem download manual: {len(resultados['manual'])}")
    for f in resultados["manual"]:
        print(f"    [>>] {f}")
    print(f"\n  Falharam: {len(resultados['falha'])}")
    for f in resultados["falha"]:
        print(f"    [X] {f}")

    with open(BASE / "output" / "resultado_download.json", "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    baixar_todos()
