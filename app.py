import streamlit as st
import requests
import base64
from datetime import datetime
from collections import defaultdict

# =========================
# PAGE CONFIG — PRIMERO
# =========================
st.set_page_config(
    page_title="Sistema SST",
    page_icon="🦺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================
# CSS DARK THEME
# =========================
st.markdown("""
<style>
.stApp { background-color: #0f172a; color: #e2e8f0; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span { color: #94a3b8 !important; }

h1, h2, h3, h4 { color: #f1f5f9 !important; }

.stSelectbox > div > div,
.stTextInput > div > div > input {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
    border: 1px solid #334155 !important;
    border-radius: 8px !important;
}
.stButton > button {
    background: linear-gradient(135deg, #1e40af, #3b82f6);
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.5rem 1.2rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1d4ed8, #60a5fa);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(59,130,246,0.4);
}
[data-testid="stFileUploader"] {
    background: #1e293b !important;
    border: 2px dashed #334155 !important;
    border-radius: 10px !important;
}
hr { border-color: #334155 !important; }

.card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 12px;
}
.card-title {
    font-size: 0.75rem; color: #64748b;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px;
}
.card-value { font-size: 1.5rem; font-weight: 700; color: #f1f5f9; }

.badge {
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: 0.75rem; font-weight: 600; letter-spacing: 0.04em;
}
.badge-ok      { background:#14532d; color:#86efac; border:1px solid #166534; }
.badge-warn    { background:#451a03; color:#fcd34d; border:1px solid #78350f; }
.badge-danger  { background:#450a0a; color:#fca5a5; border:1px solid #7f1d1d; }
.badge-partial { background:#1e3a5f; color:#93c5fd; border:1px solid #1d4ed8; }

.main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #1e40af 100%);
    padding: 24px 28px; border-radius: 14px; margin-bottom: 24px;
    border: 1px solid #1e40af; box-shadow: 0 4px 24px rgba(30,64,175,0.3);
}
.main-header h1 { margin: 0 0 4px 0; font-size: 1.8rem; }
.main-header p  { margin: 0; color: #93c5fd !important; font-size: 0.9rem; }

label, .stMarkdown p { color: #cbd5e1 !important; }
</style>
""", unsafe_allow_html=True)

# =========================
# LOGIN
# =========================
USUARIOS = {"esteban": "seguridad2026"}

def login():
    st.markdown("""
    <div style="max-width:380px; margin:80px auto 0 auto;">
      <div style="background:linear-gradient(135deg,#0f172a,#1e3a8a);
                  border:1px solid #1e40af; border-radius:16px;
                  padding:36px 32px; box-shadow:0 8px 32px rgba(30,64,175,0.3);">
        <div style="text-align:center; margin-bottom:28px;">
          <span style="font-size:3rem;">🦺</span>
          <h2 style="color:#f1f5f9; margin:8px 0 4px;">Sistema SST</h2>
          <p style="color:#64748b; font-size:0.85rem; margin:0;">Seguridad y Salud en el Trabajo</p>
        </div>
    """, unsafe_allow_html=True)
    user = st.text_input("👤 Usuario", placeholder="Ingresá tu usuario")
    pwd  = st.text_input("🔑 Contraseña", type="password", placeholder="••••••••")
    if st.button("Ingresar →", use_container_width=True):
        if user.lower() in USUARIOS and USUARIOS[user.lower()] == pwd:
            st.session_state["login"]   = True
            st.session_state["usuario"] = user.lower()
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos")
    st.markdown("</div></div>", unsafe_allow_html=True)

if "login" not in st.session_state:
    st.session_state["login"] = False
if not st.session_state["login"]:
    login()
    st.stop()

# =========================
# UTILIDADES
# =========================
def normalizar(txt):
    return txt.lower().replace("_", " ").replace("-", " ").strip()

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
    hoy = datetime.now()
    if fecha < hoy:
        return "vencido"
    if fecha.month == hoy.month and fecha.year == hoy.year:
        return "proximo"
    return "vigente"

# =========================
# API GITHUB
# =========================
def gh_headers():
    return {"Authorization": f"token {st.secrets['GITHUB_TOKEN']}"}

def gh_repo():
    return st.secrets["GITHUB_REPO"]

@st.cache_data(ttl=300)
def github_api(ruta):
    url = f"https://api.github.com/repos/{gh_repo()}/contents/{ruta}"
    r   = requests.get(url, headers=gh_headers())
    if r.status_code == 200:
        return r.json()
    return []

@st.cache_data(ttl=300)
def github_api_url(url):
    r = requests.get(url, headers=gh_headers())
    if r.status_code == 200:
        return r.json()
    return []

# =========================
# ESTRUCTURA DEL REPO
#
# ventana/
#   empresa_n1/
#     datos_bases/          ← base documental (fija)
#       altura/ excavacion/ ...
#     registro_obra1/       ← registros por obra
#       altura/ excavacion/ ...
#     registro_obra2/
#     registro_obra3/
# =========================

CARPETA_BASES = "datos_bases"   # nombre exacto en tu repo

@st.cache_data(ttl=300)
def obtener_empresas():
    """Carpetas dentro de ventana/"""
    data = github_api("ventana")
    if not isinstance(data, list):
        return []
    return [i["name"] for i in data if i["type"] == "dir"]

@st.cache_data(ttl=300)
def obtener_obras(empresa):
    """Carpetas dentro de ventana/empresa/ que NO sean datos_bases"""
    data = github_api(f"ventana/{empresa}")
    if not isinstance(data, list):
        return []
    return [i["name"] for i in data
            if i["type"] == "dir" and i["name"] != CARPETA_BASES]

@st.cache_data(ttl=300)
def obtener_tipos(obra_ruta):
    """
    Subcarpetas dentro de una obra (altura, excavacion, etc.)
    obra_ruta = ventana/empresa/registro_obraX
    """
    data = github_api(obra_ruta)
    if not isinstance(data, list):
        return []
    return [i["name"] for i in data if i["type"] == "dir"]

@st.cache_data(ttl=300)
def obtener_pdfs_carpeta(ruta_completa):
    """
    Devuelve lista de PDFs (y PDFs en subcarpetas) de una ruta.
    ruta_completa = ventana/empresa/datos_bases/altura
    """
    res  = []
    data = github_api(ruta_completa)
    if not isinstance(data, list):
        return res
    for i in data:
        if i["type"] == "file" and i["name"].endswith(".pdf"):
            res.append({"nombre": i["name"], "url": i["download_url"], "subtipo": "general"})
        elif i["type"] == "dir":
            sub = github_api_url(i["url"])
            for j in sub:
                if j["type"] == "file" and j["name"].endswith(".pdf"):
                    res.append({"nombre": j["name"], "url": j["download_url"], "subtipo": i["name"]})
    return res

# =========================
# CONTROL DE CUMPLIMIENTO
# =========================
REGLAS = {
    "altura":            {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "excavacion":        {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "caliente":          {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "espacio_confinado": {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "izaje":             {"base": ["procedimiento"], "registros": ["permiso", "ats"]},
    "electricidad":      {"base": ["procedimiento"], "registros": ["permiso"]},
    "herramientas":      {"base": [],                "registros": ["checklist"]},
    "epp":               {"base": [],                "registros": []},
    "accidentes":        {"base": [],                "registros": []},
    "capacitacion":      {"base": [],                "registros": []},
    "default":           {"base": ["procedimiento"], "registros": ["checklist"]},
}

def cumple(archivos, palabra):
    return any(palabra in normalizar(a["nombre"]) for a in archivos)

def cumple_subtipo(archivos, palabra):
    return any(a["subtipo"] == palabra for a in archivos)

def evaluar_control(tipo, base_docs, reg_docs):
    reglas    = REGLAS.get(tipo, REGLAS["default"])
    faltantes = []
    for r in reglas["base"]:
        if not cumple(base_docs, r):
            faltantes.append(f"Base: {r}")
    for r in reglas["registros"]:
        if not (cumple(reg_docs, r) or cumple_subtipo(reg_docs, r)):
            faltantes.append(f"Registro: {r}")
    total = len(reglas["base"]) + len(reglas["registros"])
    if not faltantes:
        return "completo", faltantes
    if total > 0 and len(faltantes) == total:
        return "critico", faltantes
    return "parcial", faltantes

# =========================
# ALERTAS
# =========================
def obtener_alertas(empresa, obra, tipos):
    alertas = []
    for t in tipos:
        docs = obtener_pdfs_carpeta(f"ventana/{empresa}/{obra}/{t}")
        for d in docs:
            f   = obtener_fecha(d["nombre"])
            est = estado_fecha(f)
            if est in ["vencido", "proximo"]:
                alertas.append({"archivo": d["nombre"], "tipo": t, "estado": est})
    return alertas

def resumen_general(empresa, obra, tipos):
    data = []
    for t in tipos:
        base_docs = obtener_pdfs_carpeta(f"ventana/{empresa}/{CARPETA_BASES}/{t}")
        reg_docs  = obtener_pdfs_carpeta(f"ventana/{empresa}/{obra}/{t}")
        estado, faltantes = evaluar_control(t, base_docs, reg_docs)
        data.append({"tipo": t, "estado": estado, "faltantes": faltantes})
    return data

# =========================
# SUBIR
# =========================
def subir_a_github(ruta_completa, nombre, contenido):
    url = f"https://api.github.com/repos/{gh_repo()}/contents/{ruta_completa}/{nombre}"
    b64 = base64.b64encode(contenido).decode()
    r   = requests.put(
        url,
        json={"message": f"Subida: {nombre}", "content": b64},
        headers=gh_headers()
    )
    return r.status_code in [200, 201]

# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.markdown("""
    <div style="padding:16px 0 8px 0; text-align:center;">
        <span style="font-size:2.2rem;">🦺</span>
        <p style="color:#93c5fd; font-weight:700; font-size:1rem; margin:4px 0 0 0;">SST</p>
        <p style="color:#475569; font-size:0.75rem; margin:0;">Sistema de Seguridad</p>
    </div>
    <hr style="border-color:#334155; margin:12px 0;">
    """, unsafe_allow_html=True)

    empresas = obtener_empresas()
    if not empresas:
        st.error("⚠️ No se pudo leer el repositorio. Verificá el token y el nombre del repo en secrets.")
        st.stop()

    empresa = st.selectbox("🏢 Empresa", empresas, key="empresa")

    obras = obtener_obras(empresa)
    if not obras:
        st.warning("Sin obras cargadas para esta empresa.")
        st.stop()

    obra = st.selectbox("🏗️ Obra", obras, key="obra")

    st.markdown("<hr style='border-color:#334155; margin:12px 0;'>", unsafe_allow_html=True)

    seccion = st.radio(
        "Navegación",
        ["📊 Dashboard", "🔎 Consulta", "📤 Cargar documento"],
        key="seccion"
    )

    st.markdown("<hr style='border-color:#334155; margin:12px 0;'>", unsafe_allow_html=True)

    if st.button("🔄 Actualizar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("🔒 Cerrar sesión", use_container_width=True):
        st.session_state["login"] = False
        st.rerun()

    st.markdown(f"""
    <div style="margin-top:20px; text-align:center;">
        <p style="color:#334155; font-size:0.7rem; margin:0;">
            Usuario: <span style="color:#64748b">{st.session_state['usuario']}</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# =========================
# HEADER
# =========================
# Tipos = subcarpetas de la obra seleccionada
tipos = obtener_tipos(f"ventana/{empresa}/{obra}")

st.markdown(f"""
<div class="main-header">
    <h1>🦺 Sistema SST</h1>
    <p>📍 {empresa} &nbsp;›&nbsp; {obra}</p>
</div>
""", unsafe_allow_html=True)

# =========================
# DASHBOARD
# =========================
if seccion == "📊 Dashboard":
    alertas = obtener_alertas(empresa, obra, tipos)
    resumen = resumen_general(empresa, obra, tipos)

    vencidos  = sum(1 for a in alertas if a["estado"] == "vencido")
    proximos  = sum(1 for a in alertas if a["estado"] == "proximo")
    completos = sum(1 for r in resumen if r["estado"] == "completo")
    criticos  = sum(1 for r in resumen if r["estado"] == "critico")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="card">
            <div class="card-title">Tipos activos</div>
            <div class="card-value">{len(tipos)}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="card">
            <div class="card-title">Completos</div>
            <div class="card-value" style="color:#86efac">{completos}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="card">
            <div class="card-title">Próx. a vencer</div>
            <div class="card-value" style="color:#fcd34d">{proximos}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="card">
            <div class="card-title">Vencidos</div>
            <div class="card-value" style="color:#fca5a5">{vencidos}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 📅 Vencimientos")
        if alertas:
            for a in alertas:
                badge = '<span class="badge badge-danger">VENCIDO</span>' \
                        if a["estado"] == "vencido" \
                        else '<span class="badge badge-warn">PRÓXIMO</span>'
                st.markdown(f"""<div class="card" style="padding:12px 16px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:0.85rem;color:#cbd5e1">{a['archivo']}</span>
                        {badge}
                    </div>
                    <div style="color:#475569;font-size:0.75rem;margin-top:4px;">📁 {a['tipo']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;padding:24px;">
                <span style="font-size:2rem;">✅</span>
                <p style="color:#86efac;margin:8px 0 0 0;font-weight:600;">Sin vencimientos</p>
            </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown("### 📊 Cumplimiento por tipo")
        badge_map = {
            "completo": ("badge-ok",      "COMPLETO"),
            "parcial":  ("badge-partial", "PARCIAL"),
            "critico":  ("badge-danger",  "CRÍTICO"),
        }
        for r in resumen:
            cls, lbl = badge_map.get(r["estado"], ("badge-partial", r["estado"].upper()))
            falt_html = ""
            if r["faltantes"]:
                items = "".join(f'<li style="color:#94a3b8;font-size:0.78rem">{f}</li>'
                                for f in r["faltantes"])
                falt_html = f'<ul style="margin:6px 0 0 16px;padding:0">{items}</ul>'
            st.markdown(f"""<div class="card" style="padding:12px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;">
                    <span style="font-size:0.9rem;color:#e2e8f0;font-weight:500;">{r['tipo']}</span>
                    <span class="badge {cls}">{lbl}</span>
                </div>
                {falt_html}
            </div>""", unsafe_allow_html=True)

# =========================
# CONSULTA
# =========================
elif seccion == "🔎 Consulta":
    st.markdown("### 🔎 Consulta de documentos")

    if not tipos:
        st.warning("Esta obra no tiene tipos de registro cargados.")
        st.stop()

    tipo_sel = st.selectbox("Seleccioná el tipo", tipos, key="tipo_consulta")

    # Base documental = datos_bases/tipo
    base_docs = obtener_pdfs_carpeta(f"ventana/{empresa}/{CARPETA_BASES}/{tipo_sel}")
    # Registros de la obra = registro_obraX/tipo
    reg_docs  = obtener_pdfs_carpeta(f"ventana/{empresa}/{obra}/{tipo_sel}")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📄 Documentos Base")
        if base_docs:
            for i, b in enumerate(base_docs):
                st.markdown(f"""<div class="card" style="padding:12px 16px;margin-bottom:6px;">
                    <div style="color:#e2e8f0;font-size:0.85rem;margin-bottom:8px;">📄 {b['nombre']}</div>
                </div>""", unsafe_allow_html=True)
                st.link_button("📥 Descargar", b["url"], key=f"base_{i}", use_container_width=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;color:#475569;padding:20px;">
                Sin documentos base para este tipo
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("#### 📋 Registros de la obra")
        if reg_docs:
            grupos = defaultdict(list)
            for r in reg_docs:
                grupos[r["subtipo"]].append(r)

            for subtipo, archivos in grupos.items():
                if subtipo != "general":
                    st.markdown(f"""<p style="color:#64748b;font-size:0.8rem;
                        text-transform:uppercase;letter-spacing:0.08em;
                        margin:12px 0 6px 0;">📁 {subtipo}</p>""",
                        unsafe_allow_html=True)
                for i, a in enumerate(archivos):
                    f         = obtener_fecha(a["nombre"])
                    est       = estado_fecha(f)
                    badge_cls = {"vencido":"badge-danger","proximo":"badge-warn","vigente":"badge-ok"}.get(est,"")
                    badge_lbl = {"vencido":"VENCIDO","proximo":"PRÓXIMO","vigente":"VIGENTE"}.get(est,"")
                    badge_html = f'<span class="badge {badge_cls}">{badge_lbl}</span>' if badge_cls else ""
                    st.markdown(f"""<div class="card" style="padding:10px 14px;margin-bottom:6px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="color:#cbd5e1;font-size:0.82rem;">📄 {a['nombre']}</span>
                            {badge_html}
                        </div>
                    </div>""", unsafe_allow_html=True)
                    st.link_button("📥 Descargar", a["url"],
                                   key=f"reg_{subtipo}_{i}", use_container_width=True)
        else:
            st.markdown("""<div class="card" style="text-align:center;color:#475569;padding:20px;">
                Sin registros cargados para este tipo
            </div>""", unsafe_allow_html=True)

    # Control
    estado, faltantes = evaluar_control(tipo_sel, base_docs, reg_docs)
    badge_map = {
        "completo": ("badge-ok",      "✅ COMPLETO"),
        "parcial":  ("badge-partial", "⚠️ PARCIAL"),
        "critico":  ("badge-danger",  "🚨 CRÍTICO"),
    }
    cls, lbl = badge_map.get(estado, ("badge-partial", estado.upper()))
    falt_html = ""
    if faltantes:
        items = "".join(f'<li style="color:#fca5a5;font-size:0.85rem;margin:4px 0">{f}</li>'
                        for f in faltantes)
        falt_html = f'<ul style="margin:10px 0 0 18px;padding:0">{items}</ul>'

    st.markdown(f"""<div class="card" style="margin-top:24px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
            <span style="color:#94a3b8;font-weight:600;font-size:0.9rem;">🚨 Estado de control</span>
            <span class="badge {cls}">{lbl}</span>
        </div>
        {falt_html}
    </div>""", unsafe_allow_html=True)

# =========================
# CARGAR DOCUMENTO
# =========================
elif seccion == "📤 Cargar documento":
    st.markdown("### 📤 Cargar documento")

    st.markdown("""<div class="card" style="margin-bottom:20px;border-color:#1e40af;">
        <p style="color:#93c5fd;margin:0;font-size:0.85rem;">
            📌 Solo se aceptan <strong>PDF</strong>.
            Incluí la fecha de vencimiento en el nombre como <code>nombre_DD-MM-YYYY.pdf</code> si aplica.
        </p>
    </div>""", unsafe_allow_html=True)

    archivo = st.file_uploader("Seleccioná el PDF", type=["pdf"])

    if archivo:
        col1, col2 = st.columns(2)
        with col1:
            tipo_carga = st.selectbox("Tipo de documento", tipos, key="tipo_carga")
        with col2:
            # Subcarpetas dentro de la obra/tipo (si las hay)
            subs_data = github_api(f"ventana/{empresa}/{obra}/{tipo_carga}")
            subs = [i["name"] for i in subs_data if isinstance(subs_data, list) and i["type"] == "dir"]
            subtipo_sel = st.selectbox("Subtipo", ["— sin subtipo —"] + subs, key="subtipo_carga")

        ruta = f"ventana/{empresa}/{obra}/{tipo_carga}"
        if subtipo_sel != "— sin subtipo —":
            ruta += f"/{subtipo_sel}"

        st.markdown(f"""<div class="card" style="margin:12px 0;">
            <div class="card-title">Destino en repositorio</div>
            <div style="color:#93c5fd;font-size:0.85rem;font-family:monospace;">
                {ruta}/{archivo.name}
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button("⬆️ Subir documento", use_container_width=True):
            with st.spinner("Subiendo..."):
                ok = subir_a_github(ruta, archivo.name, archivo.getbuffer())
            if ok:
                st.success("✅ Documento subido correctamente")
                st.cache_data.clear()
            else:
                st.error("❌ Error al subir. Verificá el token y los permisos del repositorio.")
