import streamlit as st
import os
import requests
import base64
from datetime import datetime
from collections import defaultdict

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

def obtener_fecha(nombre):
    try:
        partes = nombre.replace(".pdf", "").split("_")
        for p in partes:
            if "-" in p:
                return datetime.strptime(p, "%d-%m-%Y")
    except:
        return None

def estado_fecha(fecha):
    if not fecha:
        return "sin_fecha"
    dias = (fecha - datetime.now()).days
    if dias < 0:
        return "vencido"
    elif dias <= 7:
        return "proximo"
    else:
        return "vigente"

# =========================
# CACHE API
# =========================
@st.cache_data(ttl=300)
def github_api(ruta):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    if r.status_code == 200:
        return r.json()
    return []

# =========================
# GITHUB DATA
# =========================
@st.cache_data(ttl=300)
def obtener_base_github(ruta):
    res = []
    data = github_api(f"ventana/{ruta}")
    for i in data:
        if i["type"] == "file" and i["name"].endswith(".pdf"):
            res.append({"nombre": i["name"], "url": i["download_url"]})
    return res

@st.cache_data(ttl=300)
def obtener_registros_github(ruta):
    res = []
    data = github_api(f"ventana/{ruta}")

    for i in data:
        if i["type"] == "file" and i["name"].endswith(".pdf"):
            res.append({
                "nombre": i["name"],
                "url": i["download_url"],
                "subtipo": "general"
            })

        elif i["type"] == "dir":
            sub_data = github_api(i["path"])
            for j in sub_data:
                if j["type"] == "file" and j["name"].endswith(".pdf"):
                    res.append({
                        "nombre": j["name"],
                        "url": j["download_url"],
                        "subtipo": i["name"]
                    })

    return res

@st.cache_data(ttl=300)
def obtener_subcarpetas_github(ruta):
    data = github_api(f"ventana/{ruta}")
    return [i["name"] for i in data if i["type"] == "dir"]

@st.cache_data(ttl=300)
def obtener_tipos_github(ruta):
    data = github_api(f"ventana/{ruta}")
    return [i["name"] for i in data if i["type"] == "dir"]

# =========================
# ALERTAS
# =========================
def obtener_alertas(emp, obra, tipos):
    alertas = []
    for t in tipos:
        reg = obtener_registros_github(f"{emp}/{obra}/{t}")
        for i in reg:
            f = obtener_fecha(i["nombre"])
            est = estado_fecha(f)
            if est in ["vencido", "proximo"]:
                alertas.append({"archivo": i["nombre"], "tipo": t, "estado": est})
    return alertas

# =========================
# SUBIR
# =========================
def subir_a_github(ruta, nombre, contenido):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]

    url = f"https://api.github.com/repos/{repo}/contents/{ruta}/{nombre}"
    contenido_base64 = base64.b64encode(contenido).decode()

    r = requests.put(
        url,
        json={"message": f"Subida {nombre}", "content": contenido_base64},
        headers={"Authorization": f"token {token}"}
    )
    return r.status_code in [200, 201]

# =========================
# CONTROL
# =========================
REGLAS = {
    "altura": {"base": ["procedimiento"], "registros": ["permiso", "ats", "emergencia"]},
    "excavacion": {"base": ["procedimiento"], "registros": ["permiso", "ats", "emergencia"]},
    "demolicion": {"base": ["procedimiento", "emergencia"], "registros": ["permiso", "ats"]},
    "herramientas": {"base": [], "registros": ["checklist"]},
    "aviso_de_obra": {"base": [], "registros": []},
    "accidentes": {"base": [], "registros": []},
    "default": {"base": ["procedimiento"], "registros": ["checklist"]}
}

def cumple(lista, palabra):
    return any(palabra in normalizar(a) for a in lista)

def evaluar_control(tipo, base, reg):
    reglas = REGLAS.get(tipo, REGLAS["default"])
    base_n = [a["nombre"] for a in base]
    reg_n = [a["nombre"] for a in reg]

    faltantes = []

    for r in reglas["base"]:
        if not cumple(base_n, r):
            faltantes.append(f"Base: {r}")

    for r in reglas["registros"]:
        if not cumple(reg_n, r):
            faltantes.append(f"Registro: {r}")

    if not faltantes:
        return "completo", faltantes
    elif len(faltantes) == len(reglas["base"]) + len(reglas["registros"]):
        return "critico", faltantes
    else:
        return "parcial", faltantes

def resumen_general(emp, obra, tipos):
    data = []
    for t in tipos:
        base = obtener_base_github(f"{emp}/datos_bases/{t}")
        reg = obtener_registros_github(f"{emp}/{obra}/{t}")
        estado, faltantes = evaluar_control(t, base, reg)
        data.append({"tipo": t, "estado": estado, "faltantes": faltantes})
    return data

# =========================
# BASE
# =========================
empresa = st.selectbox("Empresa", os.listdir("ventana"))
obra = st.selectbox("Obra", os.listdir(f"ventana/{empresa}"))
tipos = obtener_tipos_github(f"{empresa}/{obra}")

# =========================
# VENCIMIENTOS
# =========================
with st.expander("📅 Ver vencimientos"):
    alertas = obtener_alertas(empresa, obra, tipos)
    if alertas:
        for a in alertas:
            if a["estado"] == "vencido":
                st.error(f"🔴 {a['archivo']} ({a['tipo']})")
            else:
                st.warning(f"🟡 {a['archivo']} ({a['tipo']})")
    else:
        st.success("Sin vencimientos")

# =========================
# RESUMEN
# =========================
with st.expander("📊 Ver resumen general"):
    resumen = resumen_general(empresa, obra, tipos)
    for r in resumen:
        if r["estado"] == "completo":
            st.success(f"🟢 {r['tipo']}")
        else:
            with st.expander(f"{r['estado']} - {r['tipo']}"):
                for f in r["faltantes"]:
                    st.write(f"❌ {f}")

# =========================
# CARGA
# =========================
st.markdown("## 📤 Cargar documento")

archivo = st.file_uploader("PDF", type=["pdf"])

if archivo:
    tipo = st.selectbox("Tipo", tipos)
    subs = obtener_subcarpetas_github(f"{empresa}/{obra}/{tipo}")

    ruta = f"ventana/{empresa}/{obra}/{tipo}"
    if subs:
        ruta += f"/{st.selectbox('Subtipo', subs)}"

    if st.button("Guardar"):
        if subir_a_github(ruta, archivo.name, archivo.getbuffer()):
            st.success("Subido")
            st.cache_data.clear()

# =========================
# CONSULTA
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Tipo", tipos)

base = obtener_base_github(f"{empresa}/datos_bases/{tipo_sel}")
reg = obtener_registros_github(f"{empresa}/{obra}/{tipo_sel}")

st.markdown("### 📄 Base")
for i, b in enumerate(base):
    st.write(f"📄 {b['nombre']}")
    st.link_button("📥 Descargar", b["url"])

# 🔥 AGRUPADO POR SUBCARPETA
st.markdown("### 📊 Registros")

grupos = defaultdict(list)

for r in reg:
    grupos[r["subtipo"]].append(r)

for subtipo, archivos in grupos.items():
    st.markdown(f"#### 📁 {subtipo}")
    for i, a in enumerate(archivos):
        st.write(f"📄 {a['nombre']}")
        st.link_button("📥 Descargar", a["url"], key=f"{subtipo}_{i}")

# =========================
# CONTROL
# =========================
estado, faltantes = evaluar_control(tipo_sel, base, reg)

st.markdown("## 🚨 Control")
st.write("Estado:", estado)

for f in faltantes:
    st.write("❌", f)
