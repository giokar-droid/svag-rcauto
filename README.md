# La tua auto: i dati per l'assicurazione — wizard RC auto SVAG

Versione **1.0.2** dell'11.10.2026. Copia **locale**: nessun repository remoto, nessun push.
Si pubblica solo quando Giorgio lo decide.

Pagina statica che il cliente apre dal telefono, come il wizard del budget (v1.5): risponde
alle domande che servono a chiedere i preventivi RC (responsabilità civile) auto a Generali,
Helvetia e Zurich alla pari, e alla fine manda tutto a Giorgio su WhatsApp. Le foto dei
documenti le manda nella stessa chat: il messaggio elenca quelle promesse.

## I file

| File | Cosa fa |
|---|---|
| `index.html` | La pagina: grafica, passi, condizioni, riepilogo, invio. Non contiene domande |
| `domande.js` | La parte per il cliente della banca domande. **Generato**: non si modifica a mano |
| `build.py` | Genera `domande.js` dalla banca `rcauto_domande_v1.json` e fa i controlli |
| `link.py` | Compone il link personale con `#pre` e `#salta`, e rifiuta quello che non ci deve stare |
| `.nojekyll` | Per GitHub Pages, il giorno in cui si pubblica |

La banca sta in `RESOURCES/SVAG/TOOL/RC AUTO WIZARD/rcauto_domande_v1.json` (Dropbox) e la
genera `_lavoro/genera_domande.py`. Una domanda si corregge lì, si rigenera la banca e poi:

```bash
python3 build.py            # rigenera domande.js
python3 build.py --controlla  # solo i controlli
```

`build.py` copia nella pagina solo introduzione, rami, passi, documenti, riepilogo, ritorno e
le chiavi ammesse di `#pre` e `#salta`. Toglie le note interne (`per_giorgio`, `porta_a`,
`inventario`, il valore «garage» delle opzioni, le formule). Si ferma se trova:

- un nome di un caso reale (l'elenco lo legge dal generatore della banca, non sta qui);
- un punto centrale «·» in un testo;
- una condizione che punta a una domanda, un ramo o un elenco che non esiste;
- nel `#pre` un dato personale o una dichiarazione del cliente.

## Il link personale

Tutto quello che sta dopo `#` resta nel browser: il sito che ospita la pagina non lo riceve.

- `#pre=` porta i dati del veicolo letti dai documenti, in base64url. La pagina accetta:
  - il JSON compatto della banca, `{"marca":"Fiat","modello_versione":"Panda",…}` (consigliato);
  - il formato del budget, `marca=Fiat;modello_versione=Panda;…` (solo valori senza `;` e `=`).
- `#salta=` porta solo nomi di domande o di documenti già noti, separati da virgole.
- Le due parti si uniscono con `&`: `…/#pre=…&salta=doc_permesso_io,cellulare`.

Mai nel link: nomi di persona, nascite, indirizzi, telefono, e-mail, nazionalità, permesso,
targa, telaio, matricola, IBAN. Mai le dichiarazioni del cliente: chilometri, garage, uso,
viaggi, dove sta l'auto, preferenze, officina, pagamento. La pagina ignora ogni chiave fuori
dall'elenco ammesso e ogni valore che non è un'opzione valida; `link.py` le rifiuta prima.

```bash
python3 link.py marca=Fiat modello_versione=Panda prima_immatricolazione=12.06.2019 \
  potenza_kw=51 cilindrata=1242 carburante=benzina cambio=manuale posti=5 provenienza=cambio \
  --salta doc_permesso_io,doc_patente_io,cellulare,email
```

Senza `--base` il link punta alla prova locale (`http://localhost:8776/`).

Il link contiene dati dell'auto del cliente: si manda solo a lui, per un canale privato.
Riaperto uguale riprende le risposte; un `#pre` diverso riparte da capo (tiene solo il nome).

## Come funziona la pagina

- Prima schermata: tempo stimato, cosa succede, come funziona, cosa non si chiede (`#salta`),
  informativa sui dati, nome.
- Poi i passi della banca (16 o 17, secondo i rami), con barra di avanzamento, «Indietro»,
  «Avanti». Un passo senza domande visibili non compare (per esempio «La dogana»).
- Le domande che dipendono da una risposta compaiono al tocco, senza ridisegnare la pagina.
  Mentre si digita non succede niente: il valore si salva quando si lascia il campo o si
  cambia passo.
- «Non lo so» e le scelte rapide sono pulsanti accanto al campo.
- Date in testo `GG.MM.AAAA` con i punti messi in automatico, mai il campo data del browser.
  Danni, ritiri e rifiuti accettano anche solo l'anno. «Da quando la usi» è `MM.AAAA`.
- Numeri e importi in testo: `12'500`, `12 500`, `12.500` vanno bene; si vedono come `12'500`.
  Accanto agli importi che possono essere in euro, i pulsanti CHF ed EUR.
- Le schede ripetibili (conducenti, altre auto, danni, ritiri, rifiuti) hanno «Aggiungi»,
  «Togli» e la risposta «nessuno». Nel passo dei danni c'è «Nessuna di queste tre cose».
- I valori arrivati dal `#pre` portano l'etichetta «dai tuoi documenti» finché il cliente non
  li tocca; i dati del veicolo stanno in una tabella da confermare.
- Le risposte restano nel browser (`localStorage`, chiave `svag-rcauto-wizard-v1`, con
  try/catch): chi chiude la pagina riprende da dove era. «Cancella» toglie solo questa chiave.
- Testo mai sotto 15 px, niente risorse da fuori (font, CDN, statistiche), niente cookie.

## Il ritorno

Il pulsante principale apre WhatsApp verso Giorgio (+41 78 871 69 00) con il messaggio già
scritto. Le alternative sono e-mail (giorgio.carrara@svag.ch), «Copia i dati» e «Scarica il
file»; «Copia» e «Scarica» non mandano niente. Il messaggio è fatto così:

```
Ciao Giorgio, ecco le risposte per l'assicurazione dell'auto (Nome), compilate il GG.MM.AAAA.
(«l'08.…» e «l'11.…» con l'apostrofo)
Ti mando queste foto:
- <documento segnato «Te lo mando»>
Il testo qui sotto serve al tuo programma ed è giusto così: va mandato com'è.

{…JSON…}
```

| Chiave | Cosa contiene |
|---|---|
| `tipo`, `versione`, `banca` | `svag-rcauto-wizard`, versione della pagina, banca e sua versione |
| `creato` | `GG.MM.AAAA hh:mm` della compilazione |
| `nome` | come l'ha scritto il cliente |
| `risposte` | `{id: valore}` con gli id della banca, sottodomande comprese. Scelta = codice; scelta multipla = elenco di codici; numeri senza apostrofi; importo in euro = anche `{id}_valuta: "EUR"`; date `GG.MM.AAAA`; mese e anno `MM.AAAA`; «Non lo so» = `nonso`; scelta rapida = il suo codice. Ci sono anche i valori del `#pre`, confermati o no |
| `conducenti`, `sinistri` | una riga per persona o per danno; `[]` = «nessuno» confermato; `null` = senza risposta. Ogni conducente ha `rif` (`c1`, `c2`…); nei danni `chi: "cond:c1"` più `chi_nome` |
| `altri_veicoli`, `ritiro_licenza`, `proposta_rifiutata` | come sopra, solo se la domanda era visibile |
| `precompilato` | id arrivati dal `#pre` che contano ancora: visibili, nascosti solo dal `#pre` stesso (i dati del veicolo) o cambiati dal cliente. Un valore del `#pre` la cui domanda è sparita per un'altra risposta (per esempio la provenienza cambiata) non c'è più, né qui né in `risposte` |
| `modificate` | quelli che il cliente ha cambiato |
| `non_so` | id con «Non lo so»; per le righe `elenco.N.campo` |
| `documenti_da_mandare` | documenti segnati «Te lo mando» |
| `documenti` | `{id: mando, dopo, non_ho, non_so}` per i documenti visibili |
| `saltate` | id tolti con `#salta` |
| `rami` | rami attivi all'invio (import, leasing, giovani, licenza_estera…) |
| `nota_finale` | testo libero, se c'è |

Rispetto al formato scritto nel METODO della banca: `r` qui si chiama `risposte`, `doc` si
chiama `documenti`, gli elenchi stanno al primo livello invece che sotto `elenchi`, `data` è
`creato`, `v` è `versione`; le «confermate» sono `precompilato` meno `modificate`.

Il motore `~/SVAG-tools/rcauto_wizard/rcauto.py importa` legge tutti e due i formati: dal
collaudo dell'11.10.2026 (caso vero, risposte di prova) la funzione `normalizza` porta il
formato della pagina a quello della banca, e i «Chi guidava? → cond:c1» dei danni diventano
«convivente» o «altra» col nome accanto. Se qui cambia una chiave, va cambiata anche lì.

## Prova in locale

In `Dropbox/.claude/launch.json` c'è la configurazione `rcauto`:
`python3 -m http.server 8776 --bind 127.0.0.1 --directory ~/svag-rcauto-repo`.

## Collaudo dell'11.10.2026

Fatto nel browser di anteprima, a 390×844 e a 1280×800, in tema chiaro e scuro:

- cambio di compagnia con auto già in Svizzera, senza link;
- import dall'Italia col `#pre` dei dati del veicolo e `#salta`, due conducenti (una sotto i
  25 anni con patente estera) e un danno all'estero in euro;
- auto nuova dal garage, elettrica, in leasing, con posteggio pubblico (garage precompilato);
- `#pre` nei due formati, con chiavi vietate, valori sbagliati e testo illeggibile;
- date e numeri digitati tasto per tasto, ripresa dopo il ricaricamento, «Cancella».

Nessun errore in console, nessun testo sotto i 15 px, nessuno scorrimento orizzontale.

## Collaudo col caso vero (11.10.2026, sera)

Link generato dal motore con la scheda vera del cliente (solo dati del veicolo nel `#pre`),
pagina compilata a 390×844 con risposte di prova dichiarate come tali, «Copia i dati» con un
clic vero (questa volta è riuscita: il testo è arrivato negli appunti del Mac), import nel
motore con `--prova`. Corretto nella pagina:

- il riepilogo diceva «non ne hai corretto nessuno» anche dopo «Qualcosa non torna» sui dati
  dell'auto: ora dice che la segnalazione c'è e che la controlla Giorgio;
- «compilate il 11.10.2026» → «compilate l'11.10.2026» (e «l'08»).

## Revisione avversaria finale (11.10.2026, notte) — versione 1.0.2

- **WhatsApp aperto due volte.** `window.open(url, "_blank", "noopener")` risponde sempre `null`
  (è la regola del browser con «noopener»), quindi scattava anche `location.href = url`: la
  pagina stessa andava su wa.me. Ora si apre senza «noopener» e il legame `opener` si toglie a mano;
  `location.href` resta solo se il browser blocca la finestra.
- **Valori del `#pre` orfani.** Un valore precompilato contava anche quando la sua domanda era
  sparita per un'altra risposta (provenienza cambiata da «import» a «cambio»: restavano paese,
  intestazione e le domande che ne dipendono). Ora conta solo se la domanda è visibile o è
  nascosta dal `#pre` stesso («mai», «non se arriva dal #pre», `#salta`).
- Testi della banca 1.2: «Società o banca delle rate», il perché di «Fino a quando paghi le
  rate?», l'aiuto della patente degli altri conducenti, il sottotitolo di «Chi tiene l'auto».

## Limiti

- WhatsApp ed e-mail non sono stati aperti davvero (aprirli manderebbe i dati a WhatsApp o al
  programma di posta): sul percorso più lungo provato il link `wa.me` è di circa 5'900
  caratteri, sul caso vero di 5'029. Va provato su un telefono vero prima del primo cliente;
  se WhatsApp taglia il testo resta «Copia i dati». Alcuni programmi di posta (Outlook su
  Windows) tagliano i `mailto:` oltre circa 2'000 caratteri.
- «Copia i dati»: nel primo collaudo non era riuscita, nel secondo sì. Da riprovare anche sul telefono.
- I punti aperti della banca restano aperti (prova sul portale Helvetia): vedi «Prima di mandare il
  link» nel METODO. La tendina «Garage» di Generali è rilevata dal 26.10.2026: la banca 1.3 chiede anche
  dove sta l'auto sul posto di lavoro (`garage_lavoro`, solo col tragitto al lavoro).
