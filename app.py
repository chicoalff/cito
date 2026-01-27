#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import re
from urllib.parse import quote_plus, unquote_plus
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from pymongo.collection import Collection

# -------------------------
# Config (ajuste conforme seu projeto)
# -------------------------
MONGO_USER = "cito"
MONGO_PASS = "fyu9WxkHakGKHeoq"
MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@cluster0.gb8bzlp.mongodb.net/?appName=Cluster0"
DB_NAME = "cito-v-a33-240125"
COLLECTION_NAME = "case_data"

DEFAULT_LIMIT = int(os.getenv("WEB_LIMIT", "200"))
MAX_LIMIT = int(os.getenv("WEB_MAX_LIMIT", "2000"))

# -------------------------
# App / Templates
# -------------------------
app = FastAPI(title="CITO | Consulta Doutrinas", version="1.0.0")
templates = Jinja2Templates(directory="templates")


def get_collection() -> Collection:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    return db[COLLECTION_NAME]


def escape_regex(s: str) -> str:
    return re.escape(s.strip())


def make_contains_regex(s: str) -> Dict[str, Any]:
    # Correspondência parcial, case-insensitive
    # Ex: "barroso" -> /barroso/i
    return {"$regex": escape_regex(s), "$options": "i"}


def clamp_limit(limit: int) -> int:
    if limit < 1:
        return DEFAULT_LIMIT
    return min(limit, MAX_LIMIT)


# ============================================================
# 1) Página principal: agregação (autor + título) + ocorrências
# ============================================================
@app.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    author: Optional[str] = Query(default=None, description="Correspondência parcial do autor"),
    title: Optional[str] = Query(default=None, description="Correspondência parcial do título"),
    limit: int = Query(default=DEFAULT_LIMIT, description="Limite de linhas no resultado"),
):
    col = get_collection()
    lim = clamp_limit(limit)

    match: Dict[str, Any] = {}
    if author and author.strip():
        match["caseData.caseDoctrineReferences.author"] = make_contains_regex(author)
    if title and title.strip():
        match["caseData.caseDoctrineReferences.publicationTitle"] = make_contains_regex(title)

    # Pipeline:
    # - unwind refs
    # - match (se tiver filtros)
    # - group por (author, publicationTitle) contando processos distintos
    # - sort e limit
    pipeline: List[Dict[str, Any]] = [
        {"$match": {"caseData.caseDoctrineReferences": {"$exists": True, "$ne": []}}},
        {"$unwind": "$caseData.caseDoctrineReferences"},
    ]
    if match:
        pipeline.append({"$match": match})

    pipeline.extend(
        [
            # dedup por processo + par (author,title)
            {
                "$group": {
                    "_id": {
                        "author": "$caseData.caseDoctrineReferences.author",
                        "publicationTitle": "$caseData.caseDoctrineReferences.publicationTitle",
                        "caseId": "$_id",
                    }
                }
            },
            # agora conta por par (author,title)
            {
                "$group": {
                    "_id": {
                        "author": "$_id.author",
                        "publicationTitle": "$_id.publicationTitle",
                    },
                    "occurrences": {"$sum": 1},
                }
            },
            {"$sort": {"occurrences": -1}},
            {"$limit": lim},
            {
                "$project": {
                    "_id": 0,
                    "author": "$_id.author",
                    "publicationTitle": "$_id.publicationTitle",
                    "occurrences": 1,
                }
            },
        ]
    )

    rows = list(col.aggregate(pipeline, allowDiskUse=True))

    # Para montar o link de detalhes com parâmetros seguros
    for r in rows:
        a = r.get("author") or ""
        t = r.get("publicationTitle") or ""
        r["details_url"] = f"/details?author_exact={quote_plus(a)}&title_exact={quote_plus(t)}"

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "author": author or "",
            "title": title or "",
            "limit": lim,
            "rows": rows,
            "count": len(rows),
        },
    )


# ============================================================
# 2) Página de detalhes: lista de processos do par (autor,título)
# ============================================================
@app.get("/details", response_class=HTMLResponse)
def details(
    request: Request,
    author_exact: str = Query(..., description="Autor exato (vindo do link)"),
    title_exact: str = Query(..., description="Título exato (vindo do link)"),
    limit: int = Query(default=500, description="Limite de processos listados"),
):
    col = get_collection()
    lim = clamp_limit(limit)

    author_value = unquote_plus(author_exact).strip()
    title_value = unquote_plus(title_exact).strip()

    pipeline: List[Dict[str, Any]] = [
        {"$match": {"caseData.caseDoctrineReferences": {"$exists": True, "$ne": []}}},
        {"$unwind": "$caseData.caseDoctrineReferences"},
        {
            "$match": {
                "caseData.caseDoctrineReferences.author": author_value,
                "caseData.caseDoctrineReferences.publicationTitle": title_value,
            }
        },
        {
            "$project": {
                "_id": 0,
                "caseTitle": 1,
                "caseStfId": 1,
                "caseUrl": 1,
            }
        },
        {"$sort": {"caseStfId": 1}},
        {"$limit": lim},
    ]

    cases = list(col.aggregate(pipeline, allowDiskUse=True))

    return templates.TemplateResponse(
        "details.html",
        {
            "request": request,
            "author": author_value,
            "title": title_value,
            "cases": cases,
            "count": len(cases),
            "limit": lim,
        },
    )


# ============================================================
# Templates embutidos (auto-criação em ./templates)
# ============================================================
def ensure_templates() -> None:
    os.makedirs("templates", exist_ok=True)

    home_html = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>CITO | Doutrinas</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
  <h1 class="h4 mb-3">Consulta de Doutrinas citadas (case_data)</h1>

  <form method="get" class="card card-body mb-3">
    <div class="row g-2">
      <div class="col-md-5">
        <label class="form-label">Autor (parcial)</label>
        <input name="author" class="form-control" value="{{ author }}" placeholder="ex.: BARROSO">
      </div>
      <div class="col-md-5">
        <label class="form-label">Título (parcial)</label>
        <input name="title" class="form-control" value="{{ title }}" placeholder="ex.: controle de constitucionalidade">
      </div>
      <div class="col-md-2">
        <label class="form-label">Limite</label>
        <input name="limit" type="number" min="1" class="form-control" value="{{ limit }}">
      </div>
    </div>
    <div class="mt-3 d-flex gap-2">
      <button class="btn btn-primary" type="submit">Pesquisar</button>
      <a class="btn btn-outline-secondary" href="/">Limpar</a>
    </div>
    <div class="mt-2 text-muted small">
      Resultado: {{ count }} linhas (agrupadas por autor + título), ordenadas por ocorrências desc.
    </div>
  </form>

  <div class="card">
    <div class="table-responsive">
      <table class="table table-sm table-striped align-middle mb-0">
        <thead class="table-dark">
          <tr>
            <th>Autor</th>
            <th>Título da publicação</th>
            <th class="text-end">Ocorrências</th>
            <th class="text-center">Detalhes</th>
          </tr>
        </thead>
        <tbody>
          {% if rows %}
            {% for r in rows %}
            <tr>
              <td style="min-width: 260px;">{{ r.author }}</td>
              <td>{{ r.publicationTitle }}</td>
              <td class="text-end" style="width: 140px;">{{ r.occurrences }}</td>
              <td class="text-center" style="width: 120px;">
                <a class="btn btn-sm btn-outline-primary" href="{{ r.details_url }}">ver</a>
              </td>
            </tr>
            {% endfor %}
          {% else %}
            <tr><td colspan="4" class="text-center text-muted py-4">Sem resultados.</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  </div>
</div>
</body>
</html>
"""
    details_html = """<!doctype html>
<html lang="pt-br">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>CITO | Detalhes</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
  <div class="d-flex align-items-center justify-content-between mb-2">
    <h1 class="h5 mb-0">Detalhes da citação</h1>
    <a class="btn btn-outline-secondary btn-sm" href="/">Voltar</a>
  </div>

  <div class="card card-body mb-3">
    <div><strong>Autor:</strong> {{ author }}</div>
    <div><strong>Título:</strong> {{ title }}</div>
    <div class="text-muted small mt-2">Processos listados: {{ count }} (limite: {{ limit }})</div>
  </div>

  <div class="card">
    <div class="table-responsive">
      <table class="table table-sm table-striped align-middle mb-0">
        <thead class="table-dark">
          <tr>
            <th>caseTitle</th>
            <th>caseStfId</th>
            <th>caseUrl</th>
          </tr>
        </thead>
        <tbody>
          {% if cases %}
            {% for c in cases %}
            <tr>
              <td style="min-width: 240px;">{{ c.caseTitle }}</td>
              <td style="width: 140px;">{{ c.caseStfId }}</td>
              <td>
                {% if c.caseUrl %}
                  <a href="{{ c.caseUrl }}" target="_blank" rel="noreferrer">{{ c.caseUrl }}</a>
                {% else %}
                  <span class="text-muted">—</span>
                {% endif %}
              </td>
            </tr>
            {% endfor %}
          {% else %}
            <tr><td colspan="3" class="text-center text-muted py-4">Sem processos para este par autor+título.</td></tr>
          {% endif %}
        </tbody>
      </table>
    </div>
  </div>
</div>
</body>
</html>
"""

    with open("templates/home.html", "w", encoding="utf-8") as f:
        f.write(home_html)
    with open("templates/details.html", "w", encoding="utf-8") as f:
        f.write(details_html)


# Criar templates automaticamente ao iniciar (para facilitar execução)
ensure_templates()
