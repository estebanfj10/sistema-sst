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
.header h1 {
    margin: 0;
    font-size: 32px;
}
.header p {
    margin: 0;
    font-size: 16px;
    opacity: 0.8;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header">
    <h1>🦺 Sistema SST</h1>
    <p>Gestión de Seguridad e Higiene Laboral</p>
</div>
""", unsafe_allow_html=True)

# 🖼️ BANNER
st.image("banner.png", use_container_width=True)

# =========================
# NORMALIZAR
# =========================
def normalizar(txt):
    return txt.lower().replace("_"," ").replace("-"," ").strip()

# =========================
# GITHUB
# =========================
def subir_a_github(ruta, nombre, contenido):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return False

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    headers = {"Authorization": f"token {token}"}

    requests.put(url, json={
        "message": f"Subida {nombre}",
        "content": contenido_base64
    }, headers=headers)

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

def obtener_subtipos_github(tipo):
    token = st.secrets.get("GITHUB_TOKEN")
    repo = st.secrets.get("GITHUB_REPO")

    if not token or not repo:
        return []

    url = f"https://api.github.com/repos/{repo}/contents/documentos/registros/{tipo}"
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
# 📤 CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("Seleccionar PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)

    subtipos = obtener_subtipos_github(tipo)
    if not subtipos:
        subtipos = ["otros"]

    subtipo = st.selectbox("Subtipo", subtipos)

    if st.button("Guardar archivo"):
        ruta = os.path.join(reg_dir, tipo, subtipo)
        os.makedirs(ruta, exist_ok=True)

        with open(os.path.join(ruta, archivo.name), "wb") as f:
            f.write(archivo.getbuffer())

        subir_a_github(
            f"documentos/registros/{tipo}/{subtipo}",
            archivo.name,
            archivo.getbuffer()
        )

        st.success("✔ Archivo guardado")

# =========================
# 🔎 CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Seleccionar tipo", tipos)

# =========================
# 📄 BASE
# =========================
st.markdown("### 📄 Documentación base")

archivos_base = []
ruta_base = os.path.join(base_dir, tipo_sel)

if os.path.exists(ruta_base):
    for root, _, files in os.walk(ruta_base):
        for f in files:
            if f.endswith(".pdf"):
                archivos_base.append((f, os.path.join(root, f)))

if archivos_base:
    for nombre, ruta in archivos_base:
        st.write(f"📄 {nombre}")
        with open(ruta, "rb") as file:
            st.download_button(
                label=f"📥 Descargar {nombre}",
                data=file,
                file_name=nombre,
                key=f"base_{nombre}"
            )
else:
    st.warning("⚠️ Sin documentación base")

# =========================
# 📊 REGISTROS
# =========================
st.markdown("### 📊 Registros")

archivos_reg = []
reg = obtener_registros_github(tipo_sel)

if reg:

    carpetas = {}

    for item in reg:
        subtipo = item["subtipo"]
        carpetas.setdefault(subtipo, []).append(item)

    for carpeta, archivos in carpetas.items():

        st.markdown(f"### 📁 {carpeta}")

        for item in archivos:

            nombre = item["nombre"]
            url = item["url"]

            archivos_reg.append((nombre, carpeta))

            icono = "📄"
            if "permiso" in normalizar(nombre):
                icono = "📝"
            elif "ats" in normalizar(nombre):
                icono = "📋"
            elif "checklist" in normalizar(nombre):
                icono = "✅"
            elif "capacitacion" in normalizar(nombre):
                icono = "🎓"

            st.write(f"{icono} {nombre}")

            try:
                r = requests.get(url)
                if r.status_code == 200:
                    st.download_button(
                        label="📥 Descargar",
                        data=r.content,
                        file_name=nombre,
                        key=f"reg_{carpeta}_{nombre}"
                    )
            except:
                st.error(f"Error al cargar {nombre}")

else:
    st.warning("⚠️ Sin registros")

# =========================
# 📋 CONTROL BASE
# =========================
st.markdown("### 📋 Control documentación base")

criticos = ["altura","excavacion","izaje","trabajo en caliente","espacio confinado","electricidad"]

base_completa = False

if tipo_sel in criticos:
    requisitos_base = ["procedimiento","permiso","ats","checklist","emergencia"]

    faltantes = [r for r in requisitos_base if not any(r in normalizar(a[0]) for a in archivos_base)]

    if faltantes:
        st.error(f"❌ Faltan: {', '.join(faltantes)}")
    else:
        st.success("✔ Base completa")
        base_completa = True

# =========================
# 📋 CONTROL REGISTROS
# =========================
st.markdown("### 📋 Control registros")

reg_completo = False

if tipo_sel in criticos:
    requisitos = ["permiso","ats","checklist","capacitacion"]

    faltantes = [r for r in requisitos if not any(r in normalizar(a[0]) for a in archivos_reg)]

    if faltantes:
        st.error(f"❌ Faltan: {', '.join(faltantes)}")
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
