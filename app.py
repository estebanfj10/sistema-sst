import streamlit as st
import os
import requests
import base64

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

# =========================
# 🎨 HEADER CORPORATIVO
# =========================
st.markdown("""
<style>
.header {
    background: linear-gradient(90deg, #0f172a, #1e3a8a);
    padding: 20px;
    border-radius: 10px;
    color: white;
    margin-bottom: 20px;
}
.card {
    padding: 15px;
    border-radius: 10px;
    background-color: #f1f5f9;
    text-align: center;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🦺 Sistema SST</h1>
    <p>Gestión de Seguridad e Higiene Laboral</p>
</div>
""", unsafe_allow_html=True)

st.image("banner.png", use_container_width=True)

# =========================
# NORMALIZAR
# =========================
def normalizar(txt):
    return txt.lower().replace("_"," ").replace("-"," ").strip()

# =========================
# GITHUB
# =========================
def obtener_tipos_github():
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    if not token or not repo:
        return []
    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros"
    headers = {"Authorization": f"token {token}"}
    try:
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return [i["name"] for i in r.json() if i["type"] == "dir"]
    except:
        pass
    return []

def obtener_registros_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    resultados = []
    if not token or not repo:
        return resultados

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        headers = {"Authorization": f"token {token}"}
        try:
            r = requests.get(url, headers=headers)
            if r.status_code == 200:
                for item in r.json():
                    if item["type"] == "dir":
                        recorrer(item["path"])
                    elif item["type"] == "file" and item["name"].endswith(".pdf"):
                        carpeta = item["path"].split("/")[-2]
                        resultados.append({
                            "nombre": item["name"],
                            "url": item["download_url"],
                            "subtipo": carpeta
                        })
        except:
            pass

    recorrer(f"documentos/registros/{tipo}")
    return resultados

# =========================
# BASE
# =========================
base_dir = "documentos"
reg_dir = os.path.join(base_dir, "registros")

os.makedirs(base_dir, exist_ok=True)
os.makedirs(reg_dir, exist_ok=True)

# =========================
# TIPOS
# =========================
tipos = []
if os.path.exists(reg_dir):
    tipos += os.listdir(reg_dir)

tipos += obtener_tipos_github()
tipos = sorted(list(set(tipos)))

# =========================
# 🚀 PANEL RESUMEN (NUEVO)
# =========================
criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

ok = parcial = critico = 0

def evaluar_tipo(tipo):

    # BASE
    archivos_base = []
    ruta_base = os.path.join(base_dir, tipo)

    if os.path.exists(ruta_base):
        for root, _, files in os.walk(ruta_base):
            for f in files:
                if f.endswith(".pdf"):
                    archivos_base.append(f)

    # REGISTROS
    reg = obtener_registros_github(tipo)
    archivos_reg = [r["nombre"] for r in reg]

    req_base = ["procedimiento","permiso","ats","checklist","emergencia"]
    req_reg = ["permiso","ats","checklist","capacitacion"]

    base_ok = all(any(r in normalizar(a) for a in archivos_base) for r in req_base)
    reg_ok = all(any(r in normalizar(a) for a in archivos_reg) for r in req_reg)

    if base_ok and reg_ok:
        return "ok"
    if base_ok or reg_ok:
        return "parcial"
    return "critico"

for t in tipos:
    if t in criticos:
        estado = evaluar_tipo(t)
        if estado == "ok":
            ok += 1
        elif estado == "parcial":
            parcial += 1
        else:
            critico += 1

# 🔢 RESUMEN
col1, col2, col3 = st.columns(3)

col1.metric("🟢 Completos", ok)
col2.metric("🟡 Parciales", parcial)
col3.metric("🔴 Críticos", critico)

# =========================
# 🧱 TARJETAS POR TIPO
# =========================
st.markdown("### 📊 Estado por tipo")

cols = st.columns(3)

for i, t in enumerate(tipos):
    if t in criticos:
        estado = evaluar_tipo(t)

        if estado == "ok":
            texto = "🟢 COMPLETO"
        elif estado == "parcial":
            texto = "🟡 PARCIAL"
        else:
            texto = "🔴 CRÍTICO"

        cols[i % 3].markdown(f"""
        <div class="card">
            <h4>{t.upper()}</h4>
            <p>{texto}</p>
        </div>
        """, unsafe_allow_html=True)

# =========================
# 🔎 CONSULTA (TODO LO TUYO SIGUE IGUAL)
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

# (👉 acá sigue TODO tu código sin cambios)
