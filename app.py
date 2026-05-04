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
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    response = requests.put(
        url,
        json={"message": f"Subida {nombre}", "content": contenido_base64},
        headers={"Authorization": f"token {token}"}
    )

    return response.status_code in [200, 201]

def obtener_base_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    resultados = []

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        r = requests.get(url, headers={"Authorization": f"token {token}"})

        if r.status_code == 200:
            for item in r.json():
                if item["type"] == "dir":
                    recorrer(item["path"])
                elif item["name"].lower().endswith(".pdf"):
                    resultados.append(item)

    recorrer(f"ventana/{ruta_relativa}")
    return resultados

def obtener_registros_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    resultados = []

    def recorrer(ruta):
        url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
        r = requests.get(url, headers={"Authorization": f"token {token}"})

        if r.status_code != 200:
            return

        for item in r.json():
            if item["type"] == "dir":
                recorrer(item["path"])
            elif item["name"].lower().endswith(".pdf"):
                partes = item["path"].split("/")
                subtipo = partes[-2] if len(partes) > 2 else "general"
                resultados.append({
                    "nombre": item["name"],
                    "url": item["download_url"],
                    "subtipo": subtipo
                })

    recorrer(f"ventana/{ruta_relativa}")
    return resultados

def obtener_subcarpetas_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    url = f"https://api.github.com/repos/{repo}/contents/ventana/{ruta_relativa}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})

    if r.status_code == 200:
        return sorted([i["name"] for i in r.json() if i["type"] == "dir"])
    return []

def obtener_tipos_github(ruta_relativa):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    url = f"https://api.github.com/repos/{repo}/contents/ventana/{ruta_relativa}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})

    if r.status_code == 200:
        return sorted([i["name"] for i in r.json() if i["type"] == "dir"])
    return []

# =========================
# CONTROL POR TIPO
# =========================
REGLAS = {
    "altura": {"base": ["procedimiento"], "registros": ["permiso", "ats", "checklist"]},
    "excavacion": {"base": ["procedimiento"], "registros": ["permiso", "ats", "checklist"]},
    "demolicion": {"base": ["procedimiento", "emergencia"], "registros": ["permiso", "ats"]},
    "herramientas": {"base": [], "registros": ["checklist"]},
    "aviso_de_obra": {"base": [], "registros": []},
    "default": {"base": ["procedimiento"], "registros": ["checklist"]}
}

def cumple(lista, palabra):
    return any(palabra in normalizar(a) for a in lista)

def evaluar_control(tipo, base, reg):
    reglas = REGLAS.get(tipo, REGLAS["default"])

    base_nombres = [a["name"] for a in base]
    reg_nombres = [a["nombre"] for a in reg]

    faltantes = []

    for r in reglas["base"]:
        if not cumple(base_nombres, r):
            faltantes.append(f"Base: {r}")

    for r in reglas["registros"]:
        if not cumple(reg_nombres, r):
            faltantes.append(f"Registro: {r}")

    if not faltantes:
        return "completo", faltantes
    elif len(faltantes) == len(reglas["base"]) + len(reglas["registros"]):
        return "critico", faltantes
    else:
        return "parcial", faltantes

def resumen_general(empresa, obra, tipos):
    data = []
    for t in tipos:
        base = obtener_base_github(f"{empresa}/datos_bases/{t}")
        reg = obtener_registros_github(f"{empresa}/{obra}/{t}")
        estado, faltantes = evaluar_control(t, base, reg)
        data.append({"tipo": t, "estado": estado, "faltantes": faltantes})
    return data

# =========================
# BASE
# =========================
base_dir = "ventana"

empresa = st.selectbox("Empresa", os.listdir(base_dir))
obra = st.selectbox("Obra", os.listdir(os.path.join(base_dir, empresa)))

tipos = obtener_tipos_github(f"{empresa}/{obra}")

# =========================
# RESUMEN GENERAL
# =========================
with st.expander("📊 Ver resumen general"):

    resumen = resumen_general(empresa, obra, tipos)

    c = sum(1 for x in resumen if x["estado"] == "completo")
    p = sum(1 for x in resumen if x["estado"] == "parcial")
    cr = sum(1 for x in resumen if x["estado"] == "critico")

    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Completos", c)
    col2.metric("🟡 Parciales", p)
    col3.metric("🔴 Críticos", cr)

    for item in resumen:
        if item["estado"] == "completo":
            st.success(f"🟢 {item['tipo']}")
        else:
            with st.expander(f"{'🟡' if item['estado']=='parcial' else '🔴'} {item['tipo']}"):
                for f in item["faltantes"]:
                    st.write(f"❌ {f}")

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)
    subcarpetas = obtener_subcarpetas_github(f"{empresa}/{obra}/{tipo}")

    ruta = f"ventana/{empresa}/{obra}/{tipo}"

    if subcarpetas:
        subtipo = st.selectbox("Subtipo", subcarpetas)
        ruta += f"/{subtipo}"

    if st.button("Guardar"):
        if subir_a_github(ruta, archivo.name, archivo.getbuffer()):
            st.success("✔ Subido correctamente")

# =========================
# CONSULTA + CONTROL
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Tipo", tipos)

base = obtener_base_github(f"{empresa}/datos_bases/{tipo_sel}")
reg = obtener_registros_github(f"{empresa}/{obra}/{tipo_sel}")

st.markdown("### 📄 Base")
if base:
    for item in base:
        st.write(item["name"])
        r = requests.get(item["download_url"])
        if r.status_code == 200:
            st.download_button("Descargar", r.content, item["name"])
else:
    st.warning("Sin base")

st.markdown("### 📊 Registros")
for item in reg:
    st.write(item["nombre"])

# CONTROL
st.markdown("## 🚨 Control")
estado, faltantes = evaluar_control(tipo_sel, base, reg)

if estado == "completo":
    st.success("🟢 COMPLETO")
elif estado == "parcial":
    st.warning("🟡 PARCIAL")
else:
    st.error("🔴 CRÍTICO")

for f in faltantes:
    st.write(f"❌ {f}")
