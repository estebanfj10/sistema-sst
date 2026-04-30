import streamlit as st
import os
import requests
import base64

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Sistema SST", page_icon="🦺", layout="wide")

# =========================
# HEADER
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
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🦺 Sistema SST</h1>
    <p>Gestión de Seguridad e Higiene</p>
</div>
""", unsafe_allow_html=True)

st.image("banner.png", use_container_width=True)

# =========================
# FUNCIONES
# =========================
def normalizar(txt):
    return txt.lower().replace("_"," ").replace("-"," ").strip()

def subir_a_github(ruta, nombre, contenido):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    if not token or not repo:
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    requests.put(url, json={
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }, headers={"Authorization": f"token {token}"})

def obtener_tipos_github():
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    if r.status_code == 200:
        return [i["name"] for i in r.json() if i["type"] == "dir"]
    return []

def obtener_subtipos_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")
    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{tipo}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    if r.status_code == 200:
        return [i["name"] for i in r.json() if i["type"] == "dir"]
    return []

def obtener_registros_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    resultados = []
    if not token or not repo:
        return resultados

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        r = requests.get(url, headers={"Authorization": f"token {token}"})

        if r.status_code == 200:
            for item in r.json():
                if item["type"] == "dir":
                    recorrer(item["path"])
                elif item["name"].endswith(".pdf"):
                    resultados.append({
                        "nombre": item["name"],
                        "url": item["download_url"],
                        "subtipo": item["path"].split("/")[-2]
                    })

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
tipos = list(set(
    (os.listdir(reg_dir) if os.path.exists(reg_dir) else [])
    + obtener_tipos_github()
))

# =========================
# 📊 RESUMEN
# =========================
st.markdown("## 📊 Resumen general")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

def evaluar_tipo_resumen(tipo):

    archivos_base_local = []
    ruta = os.path.join(base_dir, tipo)

    if os.path.exists(ruta):
        for _, _, files in os.walk(ruta):
            archivos_base_local += files

    reg = obtener_registros_github(tipo)
    archivos_reg_local = [r["nombre"] for r in reg]

    base_ok = any("procedimiento" in normalizar(a) for a in archivos_base_local)
    reg_ok = any("permiso" in normalizar(a) for a in archivos_reg_local)

    if base_ok and reg_ok:
        return "ok"
    elif not base_ok and not reg_ok:
        return "critico"
    else:
        return "parcial"

ok = parcial = critico = 0

for t in tipos:
    if t in criticos:
        estado = evaluar_tipo_resumen(t)
        if estado == "ok":
            ok += 1
        elif estado == "parcial":
            parcial += 1
        else:
            critico += 1

c1, c2, c3 = st.columns(3)
c1.metric("🟢 Completos", ok)
c2.metric("🟡 Parciales", parcial)
c3.metric("🔴 Críticos", critico)

# =========================
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)
    sub = obtener_subtipos_github(tipo) or ["otros"]
    subtipo = st.selectbox("Subtipo", sub)

    if st.button("Guardar"):
        ruta = os.path.join(reg_dir, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        with open(os.path.join(ruta, archivo.name), "wb") as f:
            f.write(archivo.getbuffer())

        subir_a_github(f"documentos/registros/{tipo}/{subtipo}", archivo.name, archivo.getbuffer())
        st.success("✔ Guardado")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Tipo", tipos)

# =========================
# 📄 BASE
# =========================
st.markdown("### 📄 Documentación base")

archivos_base = []
ruta = os.path.join(base_dir, tipo_sel)

if os.path.exists(ruta):
    for root, _, files in os.walk(ruta):
        for f in files:
            if f.endswith(".pdf"):
                archivos_base.append((f, os.path.join(root, f)))

if archivos_base:
    for n, r in archivos_base:
        with open(r, "rb") as f:
            st.download_button(n, f, n)
else:
    st.warning("⚠️ Sin base")

# =========================
# 📊 REGISTROS
# =========================
st.markdown("### 📊 Registros")

archivos_reg = []
reg = obtener_registros_github(tipo_sel)

if reg:
    for item in reg:
        archivos_reg.append((item["nombre"], item["subtipo"]))

        r = requests.get(item["url"])
        if r.status_code == 200:
            st.download_button(item["nombre"], r.content, item["nombre"])
else:
    st.warning("⚠️ Sin registros")

# =========================
# 📋 CONTROL DETALLADO
# =========================
st.markdown("### 📋 Control documentación base")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

base_completa = False

if tipo_sel in criticos:
    req_base = ["procedimiento","permiso","ats","checklist","emergencia"]

    faltantes_base = [
        r for r in req_base
        if not any(r in normalizar(a[0]) for a in archivos_base)
    ]

    if faltantes_base:
        st.error(f"❌ Base faltante: {', '.join(faltantes_base)}")
    else:
        st.success("✔ Base completa")
        base_completa = True

# REGISTROS
st.markdown("### 📋 Control registros")

reg_completo = False

if tipo_sel in criticos:
    req_reg = ["permiso","ats","checklist","capacitacion"]

    faltantes_reg = [
        r for r in req_reg
        if not any(r in normalizar(a[0]) for a in archivos_reg)
    ]

    if faltantes_reg:
        st.error(f"❌ Registros faltantes: {', '.join(faltantes_reg)}")
    else:
        st.success("✔ Registros completos")
        reg_completo = True

# =========================
# 🚨 SEMÁFORO
# =========================
st.markdown("## 🚨 Estado general SST")

if tipo_sel not in criticos:
    st.info("ℹ️ No crítico")
else:
    if base_completa and reg_completo:
        st.success("🟢 COMPLETO")
    elif base_completa or reg_completo:
        st.warning("🟡 PARCIAL")
    else:
        st.error("🔴 CRÍTICO")
