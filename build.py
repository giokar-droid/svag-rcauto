#!/usr/bin/env python3
"""Genera domande.js, la parte della banca RC auto che entra nella pagina del cliente.

La banca è rcauto_domande_v1.json (cartella «RC AUTO WIZARD» nel Dropbox di Giorgio).
Le domande si correggono nel generatore della banca (_lavoro/genera_domande.py) e si
rilancia questo script: la pagina non si tocca a mano per le domande.

Nella pagina entra solo la parte per il cliente:
  introduzione, rami, passi, documenti, riepilogo, ritorno, chiavi ammesse di #pre e #salta.
Restano fuori le note interne (per_giorgio, porta_a, inventario, il valore «garage» delle
opzioni, le formule) e le sezioni per Giorgio (resta_a_giorgio, alla_call, controlli,
traduzione delle preferenze, decisioni, punti aperti, copertura, esempio del link).

Prima di scrivere controlla:
  1. nessun nome di un caso reale nella parte pubblica;
  2. nessun punto centrale «·» nei testi;
  3. condizioni che puntano a domande, rami ed elenchi esistenti;
  4. #pre: solo domande «pre», mai dati personali né dichiarazioni del cliente;
  5. #salta: solo domande o documenti esistenti.
Se un controllo fallisce non scrive niente.

Uso:
  python3 build.py                 # legge la banca dal percorso di sempre
  python3 build.py --banca FILE    # da un altro file
  python3 build.py --controlla     # solo i controlli, non scrive
"""
import argparse
import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

QUI = Path(__file__).resolve().parent
USCITA = QUI / "domande.js"
BANCA_DEFAULT = (Path.home() / "Library/CloudStorage/Dropbox/RESOURCES/SVAG/TOOL/RC AUTO WIZARD"
                 / "rcauto_domande_v1.json")

# chiavi interne che non entrano mai nella pagina, a qualsiasi livello di una domanda o di un documento
CHIAVI_INTERNE = {"per_giorgio", "porta_a", "inventario", "passo"}
# dichiarazioni del cliente: mai nel #pre (METODO § 9)
DICHIARAZIONI = {"km_annui", "garage", "impiego", "utilizzo_speciale", "viaggi_estero",
                 "luogo_stazionamento", "officine_partner", "modo_pagamento"}
# tipi che la pagina sa disegnare
TIPI = {"scelta", "scelta_multipla", "si_no", "numero", "importo", "testo", "testo_lungo",
        "telefono", "email", "data", "data_o_anno", "mese_anno", "conferma_veicolo", "elenco"}
# rami calcolati in pagina (index.html, funzione ramoCalcolato)
RAMI_CALCOLATI = {"auto_recente", "altra_persona", "detentore_diviso", "giovani", "licenza_estera"}


def pulisci(o):
    """Toglie le chiavi interne da una domanda, da un campo o da un documento (ricorsivo)."""
    if isinstance(o, list):
        return [pulisci(x) for x in o]
    if not isinstance(o, dict):
        return o
    fuori = {}
    for k, v in o.items():
        if k in CHIAVI_INTERNE:
            continue
        if k == "garage" and "v" in o and "t" in o:      # valore per Giorgio attaccato all'opzione
            continue
        if k == "calcolo" and isinstance(v, dict):         # la formula è per Giorgio
            v = {kk: vv for kk, vv in v.items() if kk in ("mostra", "avviso_se_sotto")}
        fuori[k] = pulisci(v)
    return fuori


def parte_cliente(b):
    intro = b["introduzione"]
    rit = b["ritorno"]
    rami = []
    for r in b["rami"]:
        if "condizione" in r:
            rami.append({"id": r["id"], "condizione": r["condizione"]})
        else:
            rami.append({"id": r["id"], "calcolato": True})
    passi = []
    for p in b["passi"]:
        q = {"id": p["id"], "n": p["n"], "titolo": p["titolo"], "sottotitolo": p.get("sottotitolo", "")}
        for k in ("nota", "visibile_se", "istruzioni", "documenti"):
            if k in p:
                q[k] = p[k]
        if "tutto_no" in p:
            q["tutto_no"] = {"testo": p["tutto_no"]["testo"], "imposta": list(p["tutto_no"]["imposta"].keys())}
        q["domande"] = pulisci(p.get("domande", []))
        passi.append(q)
    return {
        "banca": "rcauto_domande_v1",
        "versione_banca": b["meta"]["versione"],
        "data_banca": b["meta"]["data"],
        "introduzione": {
            "titolo": intro["titolo"],
            "sottotitolo": intro["sottotitolo"],
            "tempo_tipico": intro["tempo_stimato"]["tipico"],
            "cosa_succede": intro["cosa_succede"],
            "come_funziona": intro["come_funziona"],
            "gia_note": intro["gia_note"]["testo"],
            "privacy": intro["privacy"],
            "nome": {k: intro["nome"][k] for k in ("id", "testo", "tipo", "perche") if k in intro["nome"]},
        },
        "rami": rami,
        "passi": passi,
        "documenti": pulisci(b["documenti"]),
        "riepilogo": {k: b["riepilogo"][k] for k in ("titolo", "sottotitolo", "nota_finale")},
        "ritorno": {k: rit[k] for k in ("whatsapp", "whatsapp_leggibile", "email", "pulsanti",
                                        "prima_di_inviare", "esiti", "cancella")},
        "pre_ammessi": b["link"]["pre"]["ammessi"],
        "salta_ammessi": b["link"]["salta"]["ammessi"],
    }


def nomi_vietati(b, percorso_banca):
    """Nomi dei casi reali da non pubblicare. Non stanno in questo repository (che potrebbe
    diventare pubblico): si leggono dal generatore della banca e dalle sezioni interne."""
    nomi = set()
    gen = percorso_banca.parent / "_lavoro" / "genera_domande.py"
    if gen.exists():
        m = re.search(r"NOMI\s*=\s*(\([^)]*\))", gen.read_text(encoding="utf-8"))
        if m:
            nomi.update(ast.literal_eval(m.group(1)))
    else:
        print(f"  avviso: generatore della banca non trovato ({gen}): controllo dei nomi ridotto")
    interne = json.dumps({k: v for k, v in b.items() if k not in ("introduzione", "passi", "documenti",
                                                                  "riepilogo", "ritorno", "rami", "meta")},
                         ensure_ascii=False)
    interne += json.dumps([[d.get("per_giorgio", "") for d in p.get("domande", [])] for p in b["passi"]],
                          ensure_ascii=False)
    for m in re.finditer(r"\b[Cc]as[oi] ([A-ZÀ-Ý][a-zà-ÿ]+(?: [A-ZÀ-Ý][a-zà-ÿ]+)?)", interne):
        for parola in m.group(1).split():
            nomi.add(parola)
    # parole che seguono «caso» ma non sono nomi di persona
    nomi -= {"Zurich", "Generali", "Helvetia", "Svizzera", "Italia", "Ticino", "Import", "Denunciato"}
    return sorted(n for n in nomi if len(n) >= 4)


def testi(o, salta=()):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in salta:
                continue
            yield from testi(v, salta)
    elif isinstance(o, list):
        for v in o:
            yield from testi(v, salta)


def verifica(pag, nomi):
    errori = []
    domande, sotto, elenchi, campi_elenco = {}, set(), set(), set()

    def registra_campi(lst, dentro_elenco):
        for c in lst or []:
            (campi_elenco if dentro_elenco else sotto).add(c["id"])
            if c.get("tipo") not in TIPI:
                errori.append(f"campo {c['id']}: tipo sconosciuto {c.get('tipo')}")
            registra_campi(c.get("campi"), dentro_elenco)

    for p in pag["passi"]:
        for d in p["domande"]:
            if d["id"] in domande:
                errori.append(f"id doppio: {d['id']}")
            domande[d["id"]] = d
            if d["tipo"] not in TIPI:
                errori.append(f"{d['id']}: tipo sconosciuto {d['tipo']}")
            if d["tipo"] == "elenco":
                elenchi.add(d["id"])
                registra_campi(d.get("campi"), True)
            else:
                registra_campi(d.get("campi"), False)
            if d["tipo"] in ("scelta", "scelta_multipla", "si_no", "conferma_veicolo") and not d.get("opzioni"):
                errori.append(f"{d['id']}: scelta senza opzioni")
    docs = {x["id"] for x in pag["documenti"]}
    rami = {r["id"] for r in pag["rami"]}
    for r in pag["rami"]:
        if r.get("calcolato") and r["id"] not in RAMI_CALCOLATI:
            errori.append(f"ramo calcolato che la pagina non sa calcolare: {r['id']}")
    noti = set(domande) | sotto | campi_elenco

    def scorri(c, dove):
        if not isinstance(c, dict):
            return
        if "r" in c and c["r"] not in noti:
            errori.append(f"{dove}: condizione su id inesistente {c['r']}")
        if "ramo" in c and c["ramo"] not in rami:
            errori.append(f"{dove}: ramo inesistente {c['ramo']}")
        if "pre" in c and c["pre"] not in domande:
            errori.append(f"{dove}: #pre su id inesistente {c['pre']}")
        if "elenco" in c and c["elenco"] not in elenchi:
            errori.append(f"{dove}: elenco inesistente {c['elenco']}")
        for k in ("tutte", "una"):
            for x in c.get(k, []):
                scorri(x, dove)
        if "non" in c:
            scorri(c["non"], dove)
        if "se" in c:
            scorri(c["se"], dove)

    def scorri_domanda(d, dove):
        scorri(d.get("visibile_se"), dove)
        for o in d.get("opzioni") or []:
            scorri(o.get("visibile_se"), dove + "/" + o["v"])
        for a in d.get("avvisi") or []:
            scorri(a["se"], dove + "/avviso")
        for a in d.get("precompila") or []:
            scorri(a["se"], dove + "/precompila")
        if d.get("vuoto_disattivo_se"):
            scorri(d["vuoto_disattivo_se"], dove + "/vuoto_disattivo_se")
        for c in d.get("campi") or []:
            scorri_domanda(c, dove + "/" + c["id"])

    for p in pag["passi"]:
        scorri(p.get("visibile_se"), "passo " + p["id"])
        for k in (p.get("tutto_no") or {}).get("imposta", []):
            if k not in elenchi:
                errori.append(f"passo {p['id']}: tutto_no su un id che non è un elenco: {k}")
        for k in p.get("documenti", []):
            if k not in docs:
                errori.append(f"passo {p['id']}: documento inesistente {k}")
        for d in p["domande"]:
            scorri_domanda(d, d["id"])
    for x in pag["documenti"]:
        scorri(x.get("visibile_se"), x["id"])
    for r in pag["rami"]:
        scorri(r.get("condizione"), "ramo " + r["id"])

    for k in pag["pre_ammessi"]:
        d = domande.get(k)
        if d is None:
            errori.append(f"#pre: chiave senza domanda {k}")
            continue
        if not d.get("pre"):
            errori.append(f"#pre: la domanda {k} non è marcata «pre»")
        if d.get("personale"):
            errori.append(f"#pre: dato personale ammesso {k}")
        if k in DICHIARAZIONI or k.startswith("pref_"):
            errori.append(f"#pre: dichiarazione del cliente ammessa {k}")
    for k in pag["salta_ammessi"]:
        if k not in domande and k not in docs:
            errori.append(f"#salta: id inesistente {k}")

    for t in testi(pag):
        if "·" in t:
            errori.append(f"punto centrale in un testo: {t[:70]}")
        for n in nomi:
            if re.search(r"\b" + re.escape(n) + r"\b", t):
                errori.append(f"nome di un caso reale nella parte pubblica: {n} in «{t[:60]}»")
    return errori, domande


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--banca", type=Path, default=BANCA_DEFAULT)
    ap.add_argument("--controlla", action="store_true", help="solo i controlli, non scrive domande.js")
    a = ap.parse_args()
    if not a.banca.exists():
        sys.exit(f"Banca non trovata: {a.banca}")
    banca = json.loads(a.banca.read_text(encoding="utf-8"))
    pag = parte_cliente(banca)
    nomi = nomi_vietati(banca, a.banca)
    errori, domande = verifica(pag, nomi)
    if errori:
        for e in errori:
            print("  ERRORE:", e)
        sys.exit(f"{len(errori)} errori: domande.js non scritto.")
    corpo = json.dumps(pag, ensure_ascii=False, separators=(",", ":"))
    if a.controlla:
        print(f"Controlli superati ({len(nomi)} nomi vietati controllati). Niente scritto.")
        return
    testa = (f"/* Generato da build.py il {datetime.now():%d.%m.%Y %H:%M} dalla banca "
             f"{pag['banca']} {pag['versione_banca']} del {pag['data_banca']}.\n"
             f"   Non modificare a mano: si corregge la banca e si rilancia build.py. */\n")
    USCITA.write_text(testa + "window.SVAG_RCAUTO = " + corpo + ";\n", encoding="utf-8")
    n_dom = sum(1 for d in domande.values() if d.get("visibile_se") != {"mai": True})
    print(f"Scritto {USCITA.name}: {len(pag['passi'])} passi, {n_dom} domande "
          f"(+ {len(domande) - n_dom} solo da #pre), {len(pag['documenti'])} documenti, "
          f"{len(pag['rami'])} rami, {len(corpo) // 1024} KB.")
    print(f"Controlli superati: {len(nomi)} nomi vietati, nessun «·», condizioni, #pre e #salta.")


if __name__ == "__main__":
    main()
