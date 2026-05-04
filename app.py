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


def obtener_base_github(ruta_relativa):
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
                        "url": item["download_url"]
                    })

    recorrer(f"ventana/{ruta_relativa}")
    return resultados


def obtener_registros_github(ruta_relativa):
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

    recorrer(f"ventana/{ruta_relativa}")
    return resultados


# =========================
# BASE
# =========================
base_dir = "ventana"
os.makedirs(base_dir, exist_ok=True)

# =========================
# EMPRESAS
# =========================
empresas = [
    d for d in os.listdir(base_dir)
    if os.path.isdir(os.path.join(base_dir, d))
]

if not empresas:
    st.error("❌ No hay empresas en la carpeta 'ventana'")
    st.stop()

empresa_sel = st.selectbox("Empresa", empresas, key="empresa")
ruta_empresa = os.path.join(base_dir, empresa_sel)

# =========================
# OBRAS
# =========================
obras = [
    d for d in os.listdir(ruta_empresa)
    if d.startswith("registro_obra") and os.path.isdir(os.path.join(ruta_empresa, d))
]

if not obras:
    st.warning("⚠️ No hay obras cargadas")
    st.stop()

obra_sel = st.selectbox("Obra", obras, key="obra")

# =========================
# TIPOS
# =========================
ruta_tipos = os.path.join(ruta_empresa, obra_sel)

if os.path.exists(ruta_tipos):
    tipos = os.listdir(ruta_tipos)
else:
    tipos = []

# =========================
# 📊 RESUMEN
# =========================
st.markdown("## 📊 Resumen general")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

def evaluar_tipo_resumen(tipo):
    base = obtener_base_github(f"{empresa_sel}/datos_bases/{tipo}")
    reg = obtener_registros_github(f"{empresa_sel}/{obra_sel}/{tipo}")

    base_ok = any("procedimiento" in normalizar(a["nombre"]) for a in base)
    reg_ok = any("permiso" in normalizar(a["nombre"]) for a in reg)

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

if archivo and tipos:
    tipo = st.selectbox("Tipo", tipos, key="tipo_carga")
    subtipo = st.text_input("Subtipo (permisos, ats, checklist)")

    if st.button("Guardar"):
        ruta = os.path.join(base_dir, empresa_sel, obra_sel, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        with open(os.path.join(ruta, archivo.name), "wb") as f:
            f.write(archivo.getbuffer())

        subir_a_github(
            f"ventana/{empresa_sel}/{obra_sel}/{tipo}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        st.success("✔ Guardado")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

if not tipos:
    st.warning("⚠️ No hay tipos")
    st.stop()

tipo_sel = st.selectbox("Tipo", tipos, key="tipo_consulta")

# =========================
# 📄 BASE
# =========================
st.markdown("### 📄 Documentación base")

archivos_base = []
base = obtener_base_github(f"{empresa_sel}/datos_bases/{tipo_sel}")

if base:
    for item in base:
        nombre = item["nombre"]
        url = item["url"]

        archivos_base.append((nombre, "github"))

        try:
            r = requests.get(url)
            if r.status_code == 200:
                st.download_button("📥 Descargar", r.content, nombre)
        except:
            st.error("Error descarga base")
else:
    st.warning("⚠️ Sin base")

# =========================
# 📊 REGISTROS
# =========================
st.markdown("### 📊 Registros")

archivos_reg = []
reg = obtener_registros_github(f"{empresa_sel}/{obra_sel}/{tipo_sel}")

if reg:
    carpetas = {}

    for item in reg:
        carpetas.setdefault(item["subtipo"], []).append(item)

    for carpeta, archivos in carpetas.items():
        st.markdown(f"### 📁 {carpeta}")

        for item in archivos:
            nombre = item["nombre"]
            url = item["url"]

            archivos_reg.append((nombre, carpeta))
            st.write(f"📄 {nombre}")

            try:
                r = requests.get(url)
                if r.status_code == 200:
                    st.download_button("📥 Descargar", r.content, nombre)
            except:
                st.error("Error descarga")

else:
    st.warning("⚠️ Sin registros")

# =========================
# 📋 CONTROL
# =========================
st.markdown("## 🚨 Estado")

base_ok = any("procedimiento" in normalizar(a[0]) for a in archivos_base)
reg_ok = any("permiso" in normalizar(a[0]) for a in archivos_reg)

if base_ok and reg_ok:
    st.success("🟢 COMPLETO")
elif base_ok or reg_ok:
    st.warning("🟡 PARCIAL")
else:
    st.error("🔴 CRÍTICO")
