import json, subprocess, shutil, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = Path(__file__).resolve().parent
REVIEW = APP / "review"
CONFIG = json.loads((APP / "config.json").read_text())

tex = ROOT / CONFIG["tex_file"]
pdf = ROOT / CONFIG["pdf_file"]

def run(cmd, cwd=ROOT):
    print(">", " ".join(cmd))
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)

def save(name, text):
    (REVIEW / name).write_text(text, encoding="utf-8")

def main():
    REVIEW.mkdir(exist_ok=True)

    print("== 1. Compilo LuaLaTeX ==")
    r = run(["latexmk", "-lualatex", "-synctex=1", "-interaction=nonstopmode", "-halt-on-error", tex.name])
    save("build_stdout.txt", r.stdout)
    save("build_stderr.txt", r.stderr)

    if r.returncode != 0:
        print("ERRORE compilazione. Vedi review/build_stdout.txt")
        return

    print("== 2. Copio PDF ==")
    shutil.copy2(pdf, REVIEW / pdf.name)

    print("== 3. Render pagine PNG ==")
    rendered = []
    for p in CONFIG["pages_to_render"]:
        out = REVIEW / f"page{p:02d}"
        r = run(["pdftoppm", "-png", "-f", str(p), "-l", str(p), "-r", str(CONFIG["dpi"]), str(pdf), str(out)])
        pngs = sorted(REVIEW.glob(f"page{p:02d}-*.png"))
        rendered += pngs

    print("== 4. Git diff ==")
    d = run(["git", "diff", "--", tex.name])
    save("diff.patch", d.stdout)

    print("== 5. Prompt per ChatGPT ==")
    files = "\n".join(f"- {x.name}" for x in rendered)
    prompt = f"""Analizza graficamente il PDF/PNG allegato.

OBIETTIVO:
Verifica pagina/e renderizzate del formulario LaTeX McCabe-Thiele.

FILE ALLEGATI ATTESI:
- {pdf.name}
{files}

CONTROLLA:
- margini
- testo/formule tagliate
- sovrapposizioni
- elementi troppo vicini ai bordi
- leggibilità
- equilibrio spaziale della pagina
- regressioni grafiche

CONTESTO:
- formato documento: 384 x 192 bp
- pagina critica principale: 3, sezione 02 Conversioni
- Kilo compila ma non ha vera visione grafica
- devi fare tu controllo visivo reale

RISPOSTA RICHIESTA:
1. Esito: OK / DA CORREGGERE
2. Problemi visivi precisi
3. Coordinate approssimative se possibile
4. Patch o istruzioni precise da dare a Kilo
5. Se OK, scrivi esattamente: REVISIONE COMPLETATA
"""
    save("prompt_chatgpt.txt", prompt)

    subprocess.run(["pbcopy"], input=prompt, text=True)
    subprocess.run(["open", str(REVIEW)])
    subprocess.run(["open", CONFIG["chatgpt_url"]])

    print("")
    print("FATTO.")
    print("Cartella review aperta.")
    print("Prompt copiato negli appunti.")
    print("Ora in ChatGPT allega:")
    print(f"- {REVIEW / pdf.name}")
    for x in rendered:
        print(f"- {x}")
    print("Poi incolla il prompt con Cmd+V.")

if __name__ == "__main__":
    main()
