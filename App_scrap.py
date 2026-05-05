import os
from datetime import datetime
from datetime import date
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
from supabase import create_client
import streamlit as st


st.markdown(""" 
<style>
.menu-card button {
    height: 140px !important;
    font-size: 26px !important;
    font-weight: bold !important;
    border-radius: 18px !important;
    background-color: #0B2C4A !important;
    color: white !important;
    border: none !important;
}

.menu-card button:hover {
    background-color: #E36B2C !important;
}
</style>

<style>
/* ===== BACKGROUND GENERAL ===== */
.stApp {
    background-color: #061A2C;
}

/* ===== HEADER ===== */
.header-bar {
    background-color: #0B2C4A;
    padding: 10px 20px;
    border-radius: 8px;
}

.header-title {
    color: #0F2A44;
    font-weight: bold;
    text-align: center;
}

/* ===== BOTÓN REGRESAR ===== */
button[kind="secondary"] {
    background-color: #E36B2C !important;
    color: white !important;
    border-radius: 8px;
    font-weight: bold;
}

/* ===== BOTONES PRINCIPALES ===== */
.stButton > button {
    background-color: #E36B2C;
    color: white;
    border-radius: 10px;
    font-weight: bold;
    height: 48px;
}

.stButton > button:hover {
    background-color: #cf5f25;
    color: white;
}

/* ===== INPUTS y SELECTBOX ===== */
input, textarea {
    border-radius: 8px !important;
}

div[data-baseweb="select"] > div {
    border-radius: 8px;
    background-color: #0B2C4A10;
    border: 1px solid #0B2C4A;
}

/* Texto dentro del selectbox */
div[data-baseweb="select"] span {
    color: #0F2A44 !important;
    font-weight: 600;
}

/* ===== LABELS ===== */
label {
    color: #E36B2C !important;
    font-weight: bold;
}

/* ===== DIVIDER ===== */
hr {
    border-top: 2px solid #E36B2C;
}
</style>
            

<style>
.card {
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    color: white;
    font-size: 16px;
}

.card-blue {
    background-color: #0B2C4A;
}

.card-orange {
    background-color: #E36B2C;
}

.card-title {
    font-weight: bold;
    font-size: 18px;
}

.card-row {
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
}
</style> 
<style>
.footer {
    position: fixed;
    bottom: 8px;
    width: 100%;
    text-align: center;
    color: #0B2C4A;
    font-size: 13px;
    opacity: 0.75;
}
</style>


""", unsafe_allow_html=True)

# ================= SUPABASE =================
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= CONFIG =================
st.set_page_config(page_title="Control de Scrap", layout="wide")

# ================= SESSION =================
def init_state():
    defaults = {
        "pantalla": "menu",
        "modo_scan": False,
        "causa_qr": "",
        "maquina_sel": "-- Seleccione --",
        "parte_sel": "-- Seleccione --",
        "plan_sel": "-- Seleccione --",
        "otro_texto": "",
        "libras": "",
        "firma_sel": "-- Seleccione --",
        "fecha": datetime.now().date(),
        "abrir_teclado": False,
        "limpiar_form": False,
        "maquina_por_qr": False,
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ================= HELPERS =================
def leer_tabla(tabla):
    try:
        res = supabase.table(tabla).select("*").execute()
        if not res.data:
            return pd.DataFrame()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Error en {tabla}: {e}")
        return pd.DataFrame()

def insertar_tabla(tabla, data):
    try:
        supabase.table(tabla).insert(data).execute()
    except Exception as e:
        st.error(f"Error insertando en {tabla}: {e}")

# ================= HEADER =================
def render_header(titulo):
    col1, col2, col3 = st.columns([1, 6, 2])

    with col1:
        if st.button("⬅ Regresar"):
            st.session_state.pantalla = "menu"
            st.rerun()

    with col2:
        st.markdown(
            f"<h2 class='header-title'>{titulo}</h2>",
            unsafe_allow_html=True

        )

    with col3:
        st.image(
            "https://hdscbglzatctcjzecean.supabase.co/storage/v1/object/public/logo_versigent/logo_versigent.png",
            width=140
        )



# ================= MENU =================
def menu():
    st.markdown("<h2 style='color:#0B2C4A;'>Menú Principal</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    with col1:
        st.markdown("<div class='menu-card'>", unsafe_allow_html=True)
        if st.button("📷\nEscaneo", use_container_width=True):
            st.session_state.pantalla = "escaneo"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='menu-card'>", unsafe_allow_html=True)
        if st.button("➕\nNuevo", use_container_width=True):
            st.session_state.pantalla = "nuevo"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col3:
        st.markdown("<div class='menu-card'>", unsafe_allow_html=True)
        if st.button("📊\nHistorial", use_container_width=True):
            st.session_state.pantalla = "historial"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col4:
        st.markdown("<div class='menu-card'>", unsafe_allow_html=True)
        if st.button("📈\nGráficos", use_container_width=True):
            st.session_state.pantalla = "graficos"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ================= ESCANEO =================
def escaneo():
    render_header("Escaneo de Scrap")

    # ===== LIMPIEZA CONTROLADA =====
    if st.session_state.limpiar_form:
        st.session_state.causa_qr = ""
        st.session_state.maquina_sel = "-- Seleccione --"
        st.session_state.parte_sel = "-- Seleccione --"
        st.session_state.plan_sel = "-- Seleccione --"
        st.session_state.otro_texto = ""
        st.session_state.libras = ""
        st.session_state.firma_sel = "-- Seleccione --"
        st.session_state.fecha = date.today()
        st.session_state.maquina_por_qr = False
        st.session_state.limpiar_form = False

    # ================= ESCANEAR QR =================
    if st.button("🔍 Escanear", use_container_width=True):
        st.session_state.modo_scan = True

    if st.session_state.modo_scan:
        qr = st.text_input(
            "",
            key="qr_input",
            placeholder="Escanee el QR…  (ej. 45 - rechazo)",
            label_visibility="collapsed"
        )

        if qr:
            texto = qr.strip()

            if "-" not in texto:
                st.error("QR inválido. Formato esperado: NUM_MAQUINA - CAUSA")
                return

            parte_maquina, parte_causa = texto.split("-", 1)

            st.session_state.maquina_sel = parte_maquina.strip()
            st.session_state.causa_qr = parte_causa.strip()
            st.session_state.maquina_por_qr = True

            st.session_state.modo_scan = False
            st.rerun()

    # ================= CAUSA =================
    st.text_input("Causa", st.session_state.causa_qr, disabled=True)
    st.divider()

    # ================= CARGA DE TABLAS =================
    df_maquinas = leer_tabla("maquinas")
    df_partes = leer_tabla("numeros_parte")
    df_planes = leer_tabla("planes_accion")
    df_maquinistas = leer_tabla("maquinistas")

    # ================= LISTA DE MAQUINAS (OBLIGATORIA) =================
    maquinas = (
        df_maquinas["nombre_maquina"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    maquinas = ["-- Seleccione --"] + sorted(maquinas)

    # ================= FILA 1 =================
    col1, col2 = st.columns(2)

    with col1:
        valor_maquina = (
            st.session_state.maquina_sel
            if st.session_state.maquina_sel != "-- Seleccione --"
            else ""
        )
        st.text_input(
            "Máquina",
            value=valor_maquina,
            placeholder="Escanee QR para asignar máquina",
            disabled=True
        )
    with col2:
        partes = ["-- Seleccione --"]
        if st.session_state.maquina_sel != "-- Seleccione --":
            maquina_num = int(st.session_state.maquina_sel)
            partes += df_partes[
                df_partes["maquina"] == maquina_num
            ]["numero_parte"].dropna().tolist()

        st.selectbox("Número de parte", partes, key="parte_sel")

    # ================= FILA 2 =================
    col3, col4 = st.columns(2)

    with col3:
        planes = ["-- Seleccione --"] + df_planes["plan"].dropna().tolist()
        st.selectbox("Plan de acción", planes, key="plan_sel")

        st.text_input(
            "Colocar otro",
            key="otro_texto",
            disabled=st.session_state.plan_sel.upper() != "OTRO"
        )

    with col4:
        st.text_input("Libras", key="libras")

    # ================= FILA 3 =================
    col5, col6 = st.columns(2)

    with col5:
        firmas = ["-- Seleccione --"]
        if st.session_state.maquina_sel != "-- Seleccione --":
            maquina_num = int(st.session_state.maquina_sel)
            firmas += df_maquinistas[
                df_maquinistas["maquina"] == maquina_num
            ]["nombre"].dropna().tolist()


        st.selectbox("Maquinista", firmas, key="firma_sel")

    with col6:
        st.date_input("Fecha", key="fecha")

    st.divider()

    # ================= GUARDAR =================
    if st.button("Guardar", use_container_width=True):

        if st.session_state.plan_sel.upper() == "OTRO":
            otra_causa = st.session_state.otro_texto.strip()
            if not otra_causa:
                st.error("❌ Debe capturar el plan de acción en 'Colocar otro'")
                return
            plan_accion = "otro"
        else:
            plan_accion = st.session_state.plan_sel
            otra_causa = None

        if (
            st.session_state.causa_qr == ""
            or st.session_state.maquina_sel == "-- Seleccione --"
            or st.session_state.parte_sel == "-- Seleccione --"
            or st.session_state.firma_sel == "-- Seleccione --"
            or st.session_state.libras == ""
        ):
            st.error("❌ Faltan datos obligatorios")
            return

        insertar_tabla("scrap_registrado", {
            "fecha": str(st.session_state.fecha),
            "maquina": st.session_state.maquina_sel,
            "parte": st.session_state.parte_sel,
            "causa": st.session_state.causa_qr,
            "plan_accion": plan_accion,
            "otra_causa": otra_causa,
            "libras": float(st.session_state.libras),
            "firma": st.session_state.firma_sel,
        })

        st.success("✅ Scrap guardado correctamente")
        st.session_state.limpiar_form = True
        st.rerun()


# ================= NUEVO =================
def nuevo():
    render_header("Nuevo")

    # -------- MAQUINA --------
    with st.expander("Máquina"):
        nombre = st.text_input("Nombre máquina")
        if st.button("Guardar máquina"):
            insertar_tabla("maquinas", {"nombre_maquina": nombre})
            st.success("OK")

    # -------- CAUSA --------
    with st.expander("Causa"):
        causa = st.text_input("Nueva causa")
        if st.button("Guardar causa"):
            insertar_tabla("causas", {"causa": causa})
            st.success("OK")

    # -------- PLAN --------
    with st.expander("Plan"):
        plan = st.text_input("Nuevo plan")
        if st.button("Guardar plan"):
            insertar_tabla("planes_accion", {"plan": plan})
            st.success("OK")

    # -------- PARTE --------
    with st.expander("Número de parte"):
        df_maquinas = leer_tabla("maquinas")
        maquinas = df_maquinas.get("nombre_maquina", pd.Series()).tolist()

        maq = st.selectbox("Máquina", maquinas)
        parte = st.text_input("Número")

        if st.button("Guardar parte"):
            insertar_tabla("numeros_parte", {
                "numero_parte": parte,
                "maquina": maq
            })
            st.success("OK")

    # -------- MAQUINISTA --------
    with st.expander("Maquinista"):
        df_maquinas = leer_tabla("maquinas")
        maquinas = df_maquinas.get("nombre_maquina", pd.Series()).tolist()

        maq = st.selectbox("Máquina", maquinas, key="maq2")
        nombre = st.text_input("Nombre")

        if st.button("Guardar maquinista"):
            insertar_tabla("maquinistas", {
                "nombre": nombre,
                "maquina": maq
            })
            st.success("OK")

# ================= HISTORIAL =================

def historial():
    render_header("Historial")

    # ================= FILTROS =================
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([2, 2, 2, 1.5, 2])

    with col_f1:
        fecha_rango = st.date_input(
            "Calendario",
            value=(date.today(), date.today()),
            key="filtro_fechas"
        )


    with col_f2:
        df_partes = leer_tabla("numeros_parte")
        partes = ["Todos"] + sorted(df_partes["numero_parte"].dropna().unique().tolist())
        filtro_parte = st.selectbox("Num parte", partes, key="filtro_parte")

    with col_f3:
        df_maquinas = leer_tabla("maquinas")
        maquinas = ["Todas"] + sorted(df_maquinas["nombre_maquina"].dropna().unique().tolist())
        filtro_maquina = st.selectbox("Maquina", maquinas, key="filtro_maquina")

    with col_f4:
        aplicar = st.button("Filtrar")

    with col_f5:
        limpiar = st.button("Limpiar filtros")

    df = leer_tabla("scrap_registrado")

    if df.empty:
        st.info("Sin registros")
        return
    df["fecha"] = pd.to_datetime(df["fecha"])

    if aplicar:

        # ---- FECHAS ----
        if fecha_rango and fecha_rango[0] and fecha_rango[1]:
            df["fecha"] = pd.to_datetime(df["fecha"])
            df = df[
                (df["fecha"].dt.date >= fecha_rango[0]) &
                (df["fecha"].dt.date <= fecha_rango[1])
            ]

        # ---- NUM PARTE ----
        if filtro_parte != "Todos":
            df = df[df["parte"] == filtro_parte]

        # ---- MAQUINA ----
        if filtro_maquina != "Todas":
            df = df[df["maquina"] == filtro_maquina]

    
    if limpiar:
        st.rerun()


    # ===== RENDERIZAR TARJETAS =====
    for i, row in df.iterrows():

        # Alternar colores
        card_class = "card-blue" if i % 2 == 0 else "card-orange"

        # Plan mostrado
        if row.get("plan_accion", "").lower() == "otro" and pd.notna(row.get("otra_causa")):
            plan_mostrar = f"OTRO - {row['otra_causa']}"
        else:
            plan_mostrar = row.get("plan_accion", "")

        st.markdown(
            f"""
            <div class="card {card_class}">
                <div class="card-row">
                    <div>
                        <div class="card-title">Máquina:{row.get("maquina", "")}</div>
                        <div><b>Plan de accion:</b> {plan_mostrar}</div>
                    </div>
                    <div>
                        <div class="card-title"># Parte:{row.get("parte", "")}</div>
                        <div><b>Lb:</b> {row.get("libras", "")}</div>
                    </div>
                    <div>
                        <div class="card-title"><b>Causa: {row.get("causa", "")}</div></div><b>Fecha:</b> {row.get("fecha", "")}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 🔹 ORDENAR COLUMNAS PARA EL EXCEL
    columnas_ordenadas = [
        "fecha",
        "maquina",
        "parte",
        "causa",
        "plan_accion",   # primero plan de acción
        "otra_causa",    #  luego detalle OTRO
        "libras",
        "firma"
    ]

    # Mantener solo las columnas que existan
    columnas_ordenadas = [c for c in columnas_ordenadas if c in df.columns]
    df = df[columnas_ordenadas]

    # CAMBIAR NOMBRE SOLO PARA EXCEL
    df = df.rename(columns={
        "otra_causa": "otro_plan"
    })

    # Descargar Excel
    output = io.BytesIO()
    df.to_excel(output, index=False)
    output.seek(0)

    st.download_button(
        "📥 Descargar Excel",
        data=output,
        file_name="historial_scrap.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ================= GRAFICOS =================

def graficos():
    render_header("Graficos")

    # ================= FILTROS =================
    col_cal, col_all, _ = st.columns([2, 2, 6])

    with col_cal:
        rango_fechas = st.date_input(
            "Calendario",
            value=(date.today(), date.today()),
            key="grafico_fechas"
        )

    with col_all:
        ver_todo = st.checkbox("Ver todo", value=True)

    # ================= LEER DATOS =================
    df = leer_tabla("scrap_registrado")

    if df.empty:
        st.info("Sin datos para mostrar")
        return

    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")

    # ================= FILTRO POR FECHA =================
    if not ver_todo and rango_fechas and rango_fechas[0] and rango_fechas[1]:
        fecha_inicio, fecha_fin = rango_fechas
        df = df[
            (df["fecha"].dt.date >= fecha_inicio) &
            (df["fecha"].dt.date <= fecha_fin)
        ]

    # ================= LAYOUT =================
    col1, col2 = st.columns(2)
    col3, col4 = st.columns(2)

    # ================= # PARTE =================
    with col1:
        st.subheader("#parte")

        data = (
            df.groupby("parte")
            .size()
            .sort_values(ascending=False)
            .head(6)
        )

        fig, ax = plt.subplots()
        bars = ax.bar(data.index, data.values, color="#6BB23E")

        ax.set_title("#parte")
        ax.set_xlabel("Número de Parte")
        ax.set_ylabel("Cantidad")

        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                int(bar.get_height()),
                ha="center",
                va="bottom"
            )

        st.pyplot(fig)

    # ================= MÁQUINA =================
    with col2:
        st.subheader("Máquina")

        data = (
            df.groupby("maquina")
            .size()
            .sort_values(ascending=False)
        )

        fig, ax = plt.subplots()
        bars = ax.barh(data.index, data.values, color="#1E6F1C")

        ax.set_title("Máquina")
        ax.set_xlabel("Cantidad")
        ax.set_ylabel("Máquina")

        for bar in bars:
            ax.text(
                bar.get_width(),
                bar.get_y() + bar.get_height() / 2,
                int(bar.get_width()),
                va="center"
            )

        st.pyplot(fig)

    # ================= TIPO DE CAUSA =================

# ================= TIPO DE CAUSA (BARRAS) =================
    with col3:
        st.subheader("Tipo de causa")
    
        # Normalizar texto de causa
        causas = (
            df["causa"]
            .astype(str)
            .str.upper()
            .str.strip()
            .value_counts()
        )
    
        # Top causas + otros
        top_n = 5
        data = causas.head(top_n)
        otros = causas.iloc[top_n:].sum()
    
        if otros > 0:
            data["OTROS"] = otros
    
        fig, ax = plt.subplots()
        bars = ax.bar(data.index, data.values, color="#1E6F1C")
    
        ax.set_title("Tipo de causa")
        ax.set_xlabel("Causa")
        ax.set_ylabel("Cantidad")
    
        # Rotar etiquetas del eje X
        plt.xticks(rotation=30, ha="right")
    
        # Valores encima de barras
        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                int(bar.get_height()),
                ha="center",
                va="bottom"
            )
    
        st.pyplot(fig)


    # ================= LB POR PARTE =================
    with col4:
        st.subheader("Lb por parte")

        data = (
            df.groupby("parte")["libras"]
            .sum()
            .sort_values(ascending=False)
            .head(6)
        )

        fig, ax = plt.subplots()
        bars = ax.bar(data.index, data.values, color="#6BB23E")

        ax.set_title("Lb por parte")
        ax.set_xlabel("Número de Parte")
        ax.set_ylabel("Libras")

        for bar in bars:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                int(bar.get_height()),
                ha="center",
                va="bottom"
            )

        st.pyplot(fig)

st.markdown(
    """
    <div class="footer">
        Desarrollado por <b>Ing. Jennifer Valdes IT OpEx</b> · Versigent
    </div>
    """,
    unsafe_allow_html=True
)


if "pantalla" not in st.session_state:
    st.session_state.pantalla = "menu"

# ================= ROUTER =================
if st.session_state.pantalla == "menu":
    menu()
elif st.session_state.pantalla == "escaneo":
    escaneo()
elif st.session_state.pantalla == "nuevo":
    nuevo()
elif st.session_state.pantalla == "historial":
    historial()
elif st.session_state.pantalla == "graficos":
    graficos()
