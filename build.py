"""Gera o index.html protegido por senha a partir do fonte.html.
Uso (PowerShell):  $env:INDEX_SENHA="sua senha"; python build.py
A senha NAO fica salva em nenhum arquivo."""
import os, base64, sys
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

senha = os.environ.get("INDEX_SENHA")
if not senha:
    sys.exit("Defina INDEX_SENHA")
ITER = 250000
salt, iv = os.urandom(16), os.urandom(12)
key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(senha.encode())
dados = open("fonte.html", "rb").read()
ct = AESGCM(key).encrypt(iv, dados, None)
b64 = lambda b: base64.b64encode(b).decode()

html = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Meus Projetos</title>
<style>
:root{--bg:#f4f6fb;--card:#fff;--txt:#1b2333;--mut:#5d6882;--brand:#2f6df6;--bd:#e1e6f0;--err:#dc2626}
@media (prefers-color-scheme:dark){:root{--bg:#0f1420;--card:#182033;--txt:#e9eefb;--mut:#9aa7c4;--brand:#6c9bff;--bd:#2a3550;--err:#f87171}}
body{margin:0;min-height:100vh;display:grid;place-items:center;padding:16px;background:var(--bg);color:var(--txt);font-family:system-ui,-apple-system,"Segoe UI",sans-serif}
form{background:var(--card);border:1px solid var(--bd);border-radius:18px;padding:28px;width:100%;max-width:340px;text-align:center}
h1{margin:0 0 6px;font-size:1.4rem}p{margin:0 0 16px;color:var(--mut);font-size:.95rem}
input,button{width:100%;font:inherit;padding:12px;border-radius:10px;border:1px solid var(--bd)}
input{background:var(--bg);color:var(--txt);margin-bottom:10px}
button{background:var(--brand);border-color:var(--brand);color:#fff;font-weight:600;cursor:pointer}
#msg{color:var(--err);min-height:1.2em;margin:10px 0 0;font-size:.9rem}
</style></head><body>
<form id="f"><div style="font-size:2.2rem">🔒</div><h1>Meus Projetos</h1><p>Digite a senha para entrar.</p>
<input id="s" type="password" placeholder="Senha" autocomplete="current-password" autofocus>
<button type="submit">Entrar</button><div id="msg"></div></form>
<script>
const D={salt:"@@SALT@@",iv:"@@IV@@",ct:"@@CT@@",it:@@IT@@};
const u=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function abrir(senha){
  const k0=await crypto.subtle.importKey("raw",new TextEncoder().encode(senha),"PBKDF2",false,["deriveKey"]);
  const k=await crypto.subtle.deriveKey({name:"PBKDF2",salt:u(D.salt),iterations:D.it,hash:"SHA-256"},k0,{name:"AES-GCM",length:256},false,["decrypt"]);
  const b=await crypto.subtle.decrypt({name:"AES-GCM",iv:u(D.iv)},k,u(D.ct));
  return new TextDecoder().decode(b);
}
function mostrar(h){document.open();document.write(h);document.close();}
document.getElementById("f").addEventListener("submit",async e=>{
  e.preventDefault();const m=document.getElementById("msg");m.textContent="";
  const senha=document.getElementById("s").value;
  try{const h=await abrir(senha);try{sessionStorage.setItem("k",senha)}catch(_){}mostrar(h);}
  catch(_){m.textContent="Senha incorreta.";document.getElementById("s").select();}
});
(async()=>{try{const s=sessionStorage.getItem("k");if(s)mostrar(await abrir(s));}catch(_){}})();
</script></body></html>
"""
html = html.replace("@@SALT@@", b64(salt)).replace("@@IV@@", b64(iv)).replace("@@CT@@", b64(ct)).replace("@@IT@@", str(ITER))
open("index.html", "w", encoding="utf-8").write(html)
print("index.html gerado")
