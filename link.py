#!/usr/bin/env python3
"""Compone il link personale del wizard RC auto: #pre (dati dell'auto) e #salta.

Nel #pre vanno solo i dati del veicolo e i fatti letti dai documenti, fra le chiavi
ammesse dalla banca (link.pre.ammessi). Mai nomi, nascite, indirizzi, targa, telaio,
matricola, IBAN, nazionalità o permesso; mai le dichiarazioni del cliente (chilometri,
garage, uso, viaggi, preferenze, officina, pagamento): il programma le rifiuta.
Nel #salta vanno solo nomi di domande o di documenti già noti a Giorgio.

Uso:
  python3 link.py marca=Fiat modello_versione=Panda prima_immatricolazione=12.06.2019 \\
      potenza_kw=51 cilindrata=1242 carburante=benzina cambio=manuale posti=5 provenienza=cambio \\
      --salta doc_permesso_io,cellulare,email
  python3 link.py ... --base https://indirizzo-della-pagina/   (di default la prova locale :8776)
  python3 link.py ... --formato kv     (#pre in «id=valore;…» invece del JSON della banca)

Il link contiene dati dell'auto del cliente: si manda solo a lui, per un canale privato.
"""
import argparse
import base64
import json
import re
import sys
from datetime import date
from pathlib import Path

QUI = Path(__file__).resolve().parent
BASE_DEFAULT = "http://localhost:8776/"
DICHIARAZIONI = {"km_annui", "garage", "garage_lavoro", "impiego", "utilizzo_speciale", "viaggi_estero",
                 "luogo_stazionamento", "officine_partner", "modo_pagamento"}


def carica_pagina():
    t = (QUI / "domande.js").read_text(encoding="utf-8")
    return json.loads(t[t.index("{"):t.rindex("}") + 1])


def domande_per_id(pag):
    out = {}
    for p in pag["passi"]:
        for d in p["domande"]:
            out[d["id"]] = d
    return out


def valida(d, v):
    """Ritorna il valore normalizzato o solleva ValueError."""
    t = d["tipo"]
    if t in ("scelta", "si_no"):
        codici = [o["v"] for o in d.get("opzioni", [])]
        if v not in codici:
            raise ValueError(f"valore «{v}» non ammesso; scegli fra: {', '.join(codici)}")
        return v
    if t == "scelta_multipla":
        codici = [o["v"] for o in d.get("opzioni", [])]
        lista = [x.strip() for x in v.split(",") if x.strip()]
        for x in lista:
            if x not in codici:
                raise ValueError(f"valore «{x}» non ammesso; scegli fra: {', '.join(codici)}")
        return lista
    if t == "data":
        m = re.fullmatch(r"(\d{2})\.(\d{2})\.(\d{4})", v)
        if not m:
            raise ValueError("data da scrivere come GG.MM.AAAA")
        try:
            date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            raise ValueError(f"la data {v} non esiste")
        return v
    if t in ("numero", "importo"):
        n = v.replace("'", "").replace("’", "").replace(" ", "")
        if not re.fullmatch(r"\d+(\.\d+)?", n):
            raise ValueError("serve un numero, per esempio 1984")
        return n
    if t == "testo":
        if len(v) > 80 or re.search(r"[<>\x00-\x1f]", v):
            raise ValueError("testo troppo lungo o con caratteri non ammessi")
        return v
    raise ValueError(f"tipo «{t}» non ammesso nel #pre")


def b64url(s):
    return base64.urlsafe_b64encode(s.encode("utf-8")).decode("ascii").rstrip("=")


def main():
    ap = argparse.ArgumentParser(description="Link personale del wizard RC auto (#pre e #salta).")
    ap.add_argument("coppie", nargs="*", help="chiave=valore per il #pre")
    ap.add_argument("--salta", default="", help="id separati da virgole")
    ap.add_argument("--base", default=BASE_DEFAULT)
    ap.add_argument("--formato", choices=("json", "kv"), default="json")
    a = ap.parse_args()

    pag = carica_pagina()
    Q = domande_per_id(pag)
    docs = {d["id"] for d in pag["documenti"]}
    ammessi = set(pag["pre_ammessi"])
    errori, pre = [], {}
    for c in a.coppie:
        if "=" not in c:
            errori.append(f"«{c}»: serve chiave=valore")
            continue
        k, v = c.split("=", 1)
        k, v = k.strip(), v.strip()
        if k in DICHIARAZIONI or k.startswith("pref_"):
            errori.append(f"{k}: è una dichiarazione del cliente, non va nel link")
            continue
        if k not in ammessi or k not in Q:
            errori.append(f"{k}: chiave non ammessa nel #pre (ammesse: {', '.join(sorted(ammessi))})")
            continue
        if Q[k].get("personale"):
            errori.append(f"{k}: dato personale, non va nel link")
            continue
        if a.formato == "kv" and (";" in v or "=" in v):
            errori.append(f"{k}: nel formato kv il valore non può contenere «;» o «=»: usa il formato json")
            continue
        try:
            pre[k] = valida(Q[k], v)
        except ValueError as e:
            errori.append(f"{k}: {e}")
    salta = [s.strip() for s in a.salta.split(",") if s.strip()]
    for s in salta:
        if s not in pag["salta_ammessi"]:
            errori.append(f"#salta: «{s}» non è un id ammesso")
        elif s not in Q and s not in docs:
            errori.append(f"#salta: «{s}» non esiste")
    if errori:
        for e in errori:
            print("  ERRORE:", e, file=sys.stderr)
        sys.exit(f"{len(errori)} errori: nessun link.")

    pezzi = []
    if pre:
        if a.formato == "json":
            testo = json.dumps(pre, ensure_ascii=False, separators=(",", ":"))
        else:
            testo = ";".join(f"{k}={','.join(v) if isinstance(v, list) else v}" for k, v in pre.items())
        pezzi.append("pre=" + b64url(testo))
    if salta:
        pezzi.append("salta=" + ",".join(salta))
    link = a.base + ("#" + "&".join(pezzi) if pezzi else "")
    print(link)
    print(f"\n{len(pre)} dati nel #pre, {len(salta)} voci saltate. Il link è personale: solo al cliente.",
          file=sys.stderr)


if __name__ == "__main__":
    main()
