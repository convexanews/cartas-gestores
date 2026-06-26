"""
Dashboard Cartas dos Gestores
Flask app para visualizar resumos das cartas de fundos.
"""
import json
import os
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__, template_folder="site/templates", static_folder="site/static")
app.secret_key = "cartas-gestores-2026"

BASE = Path(__file__).parent
PASTA_PDFS = BASE / "pdfs"
PASTA_OUTPUT = BASE / "output"
FUNDOS_JSON = BASE / "fundos.json"
CARTAS_JSON = PASTA_OUTPUT / "cartas_processadas.json"
RESUMOS_JSON = PASTA_OUTPUT / "resumos.json"


def carregar_fundos():
    with open(FUNDOS_JSON, encoding="utf-8") as f:
        return json.load(f)


def carregar_cartas():
    if not CARTAS_JSON.exists():
        return []
    with open(CARTAS_JSON, encoding="utf-8") as f:
        return json.load(f)


def carregar_resumos():
    if not RESUMOS_JSON.exists():
        return {}
    with open(RESUMOS_JSON, encoding="utf-8") as f:
        return json.load(f)


def salvar_resumos(resumos):
    PASTA_OUTPUT.mkdir(exist_ok=True)
    with open(RESUMOS_JSON, "w", encoding="utf-8") as f:
        json.dump(resumos, f, ensure_ascii=False, indent=2)


@app.route("/")
def index():
    fundos = carregar_fundos()
    cartas = carregar_cartas()
    resumos = carregar_resumos()
    cartas_por_fundo = {c["fundo"]: c for c in cartas}
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
    return render_template("index.html", dados=dados, total=total,
                           processados=processados, resumidos=resumidos)


@app.route("/fundo/<path:nome>")
def detalhe_fundo(nome):
    cartas = carregar_cartas()
    resumos = carregar_resumos()
    carta = next((c for c in cartas if c["fundo"] == nome), None)
    resumo = resumos.get(nome, {})
    fundos = carregar_fundos()
    fundo = next((f for f in fundos if f["nome"] == nome), {"nome": nome})
    return render_template("fundo.html", fundo=fundo, carta=carta, resumo=resumo)


@app.route("/comparativo")
def comparativo():
    cartas = carregar_cartas()
    resumos = carregar_resumos()
    dados = []
    for carta in cartas:
        resumo = resumos.get(carta["fundo"], {})
        dados.append({"carta": carta, "resumo": resumo})
    return render_template("comparativo.html", dados=dados)


@app.route("/whatsapp")
def whatsapp():
    resumos = carregar_resumos()
    return render_template("whatsapp.html", resumos=resumos)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        arquivos = request.files.getlist("pdfs")
        salvos = 0
        for arq in arquivos:
            if arq and arq.filename.lower().endswith(".pdf"):
                nome = secure_filename(arq.filename)
                arq.save(PASTA_PDFS / nome)
                salvos += 1
        if salvos:
            flash(f"{salvos} PDF(s) enviado(s). Rode o processador para extrair os dados.")
        return redirect(url_for("upload"))
    pdfs = sorted(PASTA_PDFS.glob("*.pdf"))
    return render_template("upload.html", pdfs=pdfs)


@app.route("/processar", methods=["POST"])
def processar():
    import subprocess
    result = subprocess.run(
        ["python", str(BASE / "processar_pdfs.py")],
        capture_output=True, text=True, cwd=str(BASE)
    )
    flash(result.stdout or result.stderr or "Processamento concluído.")
    return redirect(url_for("upload"))


@app.route("/api/salvar-resumo", methods=["POST"])
def salvar_resumo():
    data = request.get_json()
    nome = data.get("fundo")
    resumo = data.get("resumo")
    if not nome or not resumo:
        return jsonify({"error": "fundo e resumo obrigatórios"}), 400
    resumos = carregar_resumos()
    resumos[nome] = resumo
    salvar_resumos(resumos)
    return jsonify({"ok": True})


@app.route("/download/fundo/<path:nome>")
def download_fundo(nome):
    cartas = carregar_cartas()
    carta = next((c for c in cartas if c["fundo"] == nome), None)
    if carta and carta.get("arquivo"):
        caminho = PASTA_PDFS / carta["arquivo"]
        if caminho.exists():
            return send_file(caminho, as_attachment=True, download_name=carta["arquivo"])
    flash("PDF original não encontrado para este fundo.")
    return redirect(url_for("detalhe_fundo", nome=nome))


if __name__ == "__main__":
    PASTA_PDFS.mkdir(exist_ok=True)
    PASTA_OUTPUT.mkdir(exist_ok=True)
    app.run(debug=True, port=5000)
