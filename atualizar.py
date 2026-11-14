"""Atualiza o Index: acha repositorios publicos novos com GitHub Pages, adiciona na
lista, recriptografa com a senha e publica nos 2 repositorios.
Uso:  python atualizar.py            (so publica se houver mudanca)
      python atualizar.py --forcar   (republica mesmo sem mudanca)
A senha fica em senha.local (so neste computador, nunca vai para o GitHub)."""
import os, sys, json, base64, subprocess, tempfile, shutil
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

AQUI = os.path.dirname(os.path.abspath(__file__))
DONO = "marcelokielwagen"
IGNORAR = {"index", f"{DONO}.github.io"}
ITER = 250000
P = lambda *a: os.path.join(AQUI, *a)

def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, r.stdout

def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, text=True)

def publicos_com_pages():
    _, out = gh("repo", "list", DONO, "--limit", "200", "--visibility", "public",
                "--json", "name,description,isArchived,isFork")
    achados = {}
    for r in json.loads(out):
        if r["name"] in IGNORAR or r["isArchived"] or r["isFork"]:
            continue
        code, _ = gh("api", f"repos/{DONO}/{r['name']}/pages", "-q", ".html_url")
        if code == 0:
            achados[r["name"]] = r.get("description") or ""
    return achados

def cifrar(senha, dados):
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(senha.encode())
    b64 = lambda b: base64.b64encode(b).decode()
    return b64(salt), b64(iv), b64(AESGCM(key).encrypt(iv, dados, None))

def main():
    forcar = "--forcar" in sys.argv
    senha = os.environ.get("INDEX_SENHA") or open(P("senha.local"), encoding="utf-8").read().strip()
    proj = json.load(open(P("projetos.json"), encoding="utf-8"))
    vivos = publicos_com_pages()
    mudou = forcar
    conhecidos = {p["pasta"] for p in proj}
    for nome, desc in vivos.items():
        if nome not in conhecidos:
            titulo = nome.replace("-", " ").replace("_", " ").title()
            proj.append({"icone": "🧩", "nome": titulo, "tag": "Novo", "pasta": nome,
                         "desc": desc or "Projeto novo."})
            print("Novo projeto:", nome); mudou = True
    antes = len(proj)
    proj = [p for p in proj if p["pasta"] in vivos]
    if len(proj) != antes:
        print("Removidos:", antes - len(proj)); mudou = True
    if not mudou:
        print("Nada novo."); return
    json.dump(proj, open(P("projetos.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    modelo = open(P("modelo.html"), encoding="utf-8").read()
    fonte = modelo.replace("/*PROJETOS*/[]", json.dumps(proj, ensure_ascii=False, indent=1))
    open(P("fonte.html"), "w", encoding="utf-8").write(fonte)
    salt, iv, ct = cifrar(senha, fonte.encode("utf-8"))
    html = open(P("tela_senha.html"), encoding="utf-8").read()
    for k, v in (("@@SALT@@", salt), ("@@IV@@", iv), ("@@CT@@", ct), ("@@IT@@", str(ITER))):
        html = html.replace(k, v)
    open(P("index.html"), "w", encoding="utf-8").write(html)

    msg = "Index atualizado automaticamente\n\nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
    git(AQUI, "add", "index.html"); 
    git(AQUI, "commit", "-m", msg); git(AQUI, "push")
    tmp = tempfile.mkdtemp()
    try:
        destino = os.path.join(tmp, "site")
        subprocess.run(["gh", "repo", "clone", f"{DONO}/{DONO}.github.io", destino, "--", "-q"], check=True)
        shutil.copy(P("index.html"), os.path.join(destino, "index.html"))
        git(destino, "add", "index.html"); git(destino, "commit", "-m", msg); git(destino, "push", "-q")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("Publicado. Projetos:", len(proj))

main()
