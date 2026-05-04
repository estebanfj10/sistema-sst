import streamlit as st
import os
import requests
import base64
from datetime import datetime

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

def obtener_base_github(ruta):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    res = []

    def recorrer(r):
        url = f"https://api.github.com/repos/{repo}/contents/{r}"
        rqs = requests.get(url, headers={"Authorization": f"token {token}"})
        if rqs.status_code == 200:
            for i in rqs.json():
                if i["type"] == "dir":
                    recorrer(i["path"])
                elif i["name"].endswith(".pdf"):
                    res.append({"nombre": i["name"], "url": i["download_url"]})

    recorrer(f"ventana/{ruta}")
    return res

def obtener_registros_github(ruta):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    res = []

    def recorrer(r):
        url = f"https://api.github.com/repos/{repo}/contents/{r}"
        rqs = requests.get(url, headers={"Authorization": f"token {token}"})
        if rqs.status_code != 200:
            return
        for i in rqs.json():
            if i["type"] == "dir":
                recorrer(i["path"])
            elif i["name"].endswith(".pdf"):
                partes = i["path"].split("/")
                sub = partes[-2] if len(partes) > 2 else "general"
                res.append({
                    "nombre": i["name"],
                    "url": i["download_url"],
                    "subtipo": sub
                })

    recorrer(f"ventana/{ruta}")
    return res

def obtener_subcarpetas_github(ruta):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/ventana/{ruta}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    if r.status_code == 200:
        return [i["name"] for i in r.json() if i["type"] == "dir"]
    return []

def obtener_tipos_github(ruta):
    token = st.secrets["GITHUB_TOKEN"]
    repo = st.secrets["GITHUB_REPO"]
    url = f"https://api.github.com/repos/{repo}/contents/ventana/{ruta}"
    r = requests.get(url, headers={"Authorization": f"token {token}"})
    if r.status_code == 200:
        return [i["name"] for i in r.json() if i["type"] == "dir"]
    return []

# =========================
# CONTROL
# =========================
REGLAS = {
    "default": {
        "base": ["procedimiento", "permiso", "ats", "emergencia"],
        "registros": ["procedimiento", "permiso", "ats", "emergencia"]
    }
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
# BASE
# =========================
empresa = st.selectbox("Empresa", os.listdir("ventana"))
obra = st.selectbox("Obra", os.listdir(f"ventana/{empresa}"))
tipos = obtener_tipos_github(f"{empresa}/{obra}")

# =========================
# 🚨 VENCIMIENTOS
# =========================
alertas = obtener_alertas(empresa, obra, tipos)
vencidos = [a for a in alertas if a["estado"] == "vencido"]
proximos = [a for a in alertas if a["estado"] == "proximo"]

if vencidos:
    st.markdown("## 🚨 Documentos vencidos")

    c1, c2 = st.columns(2)
    c1.metric("🔴 Vencidos", len(vencidos))
    c2.metric("🟡 Próximos", len(proximos))

    for a in vencidos:
        st.error(f"🔴 {a['archivo']} ({a['tipo']})")

with st.expander("📅 Ver todos los vencimientos"):
    if alertas:
        for a in alertas:
            if a["estado"] == "vencido":
                st.error(f"🔴 {a['archivo']} ({a['tipo']})")
            else:
                st.warning(f"🟡 {a['archivo']} ({a['tipo']})")
    else:
        st.success("Sin vencimientos")

# =========================
# 📊 RESUMEN
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

# =========================
# CONSULTA + CONTROL
# =========================
st.markdown("## 🔎 Consulta")

tipo_sel = st.selectbox("Tipo", tipos)

base = obtener_base_github(f"{empresa}/datos_bases/{tipo_sel}")
reg = obtener_registros_github(f"{empresa}/{obra}/{tipo_sel}")

for b in base:
    st.write(b["nombre"])

for r in reg:
    st.write(r["nombre"])

estado, faltantes = evaluar_control(tipo_sel, base, reg)

st.write("Estado:", estado)

for f in faltantes:
    st.write("❌", f)
