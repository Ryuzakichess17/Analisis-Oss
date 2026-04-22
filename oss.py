import streamlit as st
import pandas as pd
import glob
import os

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Dashboard OSS", layout="wide")

# =========================
# ESTILO TARJETAS
# =========================
st.markdown("""
<style>
.metric-card {
    background-color: #1f2937;
    padding: 20px;
    border-radius: 12px;
    text-align: center;
    color: white;
}
.metric-title {
    font-size: 14px;
    color: #9ca3af;
}
.metric-value {
    font-size: 28px;
    font-weight: bold;
}
.metric-delta {
    font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# CARGA DATA
# =========================
@st.cache_data
def load_data():
    files = glob.glob(os.path.join("data", "*.xlsx"))
    df = pd.read_excel(
        files[0],
        dtype={"LOGIN": str, "LEADER": str}
    )
    return df

df = load_data()

# =========================
# LIMPIEZA
# =========================
df["REQUESTDATE"] = pd.to_datetime(df["REQUESTDATE"], dayfirst=True, errors="coerce")
df["DIA"] = df["REQUESTDATE"].dt.day

df = df[df["DIA"].isin([4,5,6,11,12,13])]

# 🔥 LIMPIEZA NIVELES (CLAVE)
df["NIVELES"] = (
    df["NIVELES"]
    .astype(str)
    .str.extract(r"(\d+)")
    .astype(float)
)

# =========================
# PRECIOS
# =========================
precios = {
    "Power 39.90": {4:25,5:25,6:25,11:25,12:25,13:25},
    "Power Ilim 69.90": {4:0,5:0,6:0,11:15,12:15,13:15},
    "Power 29.90": {4:0,5:0,6:0,11:15,12:15,13:15},
    "Power 59.90": {4:25,5:25,6:25,11:25,12:25,13:25},
    "Power 49.90": {4:25,5:25,6:25,11:25,12:25,13:25}
}

def get_precio(row):
    if row["NIVELES"] == 7:
        return 0
    return precios.get(row["TARIFFPLANNAME"], {}).get(row["DIA"], 0)

df["MONTO"] = df.apply(get_precio, axis=1)

# =========================
# FILTROS
# =========================
st.sidebar.title("Filtros")

dep = st.sidebar.multiselect("Departamento", sorted(df["DEPARTMENT"].dropna().unique()))
niv = st.sidebar.multiselect("Nivel", sorted(df["NIVELES"].dropna().unique()))
clus = st.sidebar.multiselect("Cluster", sorted(df["CLUSTER"].dropna().unique()))

df_f = df.copy()

if dep:
    df_f = df_f[df_f["DEPARTMENT"].isin(dep)]
if niv:
    df_f = df_f[df_f["NIVELES"].isin(niv)]
if clus:
    df_f = df_f[df_f["CLUSTER"].isin(clus)]

# =========================
# TITULO
# =========================
st.title("📊 Dashboard - OSS")

# =========================
# KPIs
# =========================
antes = df_f[df_f["DIA"].isin([4,5,6])]["TXNID"].count()
despues = df_f[df_f["DIA"].isin([11,12,13])]["TXNID"].count()

var = ((despues - antes) / antes * 100) if antes > 0 else 0
monto = df_f["MONTO"].sum()

col1, col2, col3 = st.columns(3)

col1.markdown(f"""
<div class="metric-card">
<div class="metric-title">Ventas 4-6</div>
<div class="metric-value">{antes}</div>
</div>
""", unsafe_allow_html=True)

color_var = "#00ff99" if var >= 0 else "#ff4d4d"

col2.markdown(f"""
<div class="metric-card">
<div class="metric-title">Ventas 11-13</div>
<div class="metric-value">{despues}</div>
<div class="metric-delta" style="color:{color_var};">{var:.2f}%</div>
</div>
""", unsafe_allow_html=True)

col3.markdown(f"""
<div class="metric-card">
<div class="metric-title">Ingresos</div>
<div class="metric-value">S/ {monto:,.0f}</div>
</div>
""", unsafe_allow_html=True)

# =========================
# FUNC COLOR
# =========================
def color(val):
    if val > 0:
        return "color: #00ff99"
    elif val < 0:
        return "color: #ff4d4d"
    return ""

# =========================
# TABLA PLANES
# =========================
st.subheader("📊 Variación por Plan")

tabla = pd.pivot_table(
    df_f,
    values="TXNID",
    index="TARIFFPLANNAME",
    columns="DIA",
    aggfunc="count",
    fill_value=0
)

orden = [4,5,6,11,12,13]
tabla = tabla.reindex(columns=orden)

tabla["Δ TOTAL"] = (tabla[11]-tabla[4]) + (tabla[12]-tabla[5]) + (tabla[13]-tabla[6])

tabla.columns = tabla.columns.astype(str)

st.dataframe(tabla.style.map(color, subset=["Δ TOTAL"]))

# =========================
# TABLA DEPARTAMENTO
# =========================
st.subheader("🏢 Variación por Departamento")

dep_tabla = pd.pivot_table(
    df_f,
    values="TXNID",
    index="DEPARTMENT",
    columns="DIA",
    aggfunc="count",
    fill_value=0
)

dep_tabla = dep_tabla.reindex(columns=orden)

dep_tabla["Δ TOTAL"] = (dep_tabla[11]-dep_tabla[4]) + (dep_tabla[12]-dep_tabla[5]) + (dep_tabla[13]-dep_tabla[6])

dep_tabla.columns = dep_tabla.columns.astype(str)

st.dataframe(dep_tabla.style.map(color, subset=["Δ TOTAL"]))

# =========================
# TABLA NIVELES
# =========================
st.subheader("📊 Variación por Nivel")

niv_tabla = pd.pivot_table(
    df_f,
    values="TXNID",
    index="NIVELES",
    columns="DIA",
    aggfunc="count",
    fill_value=0
)

niv_tabla = niv_tabla.reindex(columns=orden)

niv_tabla["Δ TOTAL"] = (niv_tabla[11]-niv_tabla[4]) + (niv_tabla[12]-niv_tabla[5]) + (niv_tabla[13]-niv_tabla[6])

niv_tabla.columns = niv_tabla.columns.astype(str)

st.dataframe(niv_tabla.style.map(color, subset=["Δ TOTAL"]))

# =========================
# GRAFICO
# =========================
st.subheader("📈 Planes por Departamento")

graf = df_f.groupby(["DEPARTMENT","TARIFFPLANNAME"])["TXNID"].count().unstack().fillna(0)

st.bar_chart(graf)

# =========================
# COSTO VS VENTA
# =========================
st.subheader("💰 Costo vs Ventas (Eficiencia)")

resumen = df_f.groupby("DIA").agg(
    VENTAS=("TXNID", "count"),
    COSTO_TOTAL=("MONTO", "sum")
).reset_index()

resumen["COSTO_PROMEDIO"] = resumen["COSTO_TOTAL"] / resumen["VENTAS"]

orden = [4,5,6,11,12,13]
resumen = resumen.set_index("DIA").reindex(orden)

st.markdown("### 📅 Resumen por día")
st.dataframe(resumen)

def get_val(dia, col):
    return resumen.loc[dia, col] if dia in resumen.index else 0

comparaciones = pd.DataFrame({
    "PAR": ["4 vs 11", "5 vs 12", "6 vs 13"],
    "Δ VENTAS": [
        get_val(11,"VENTAS") - get_val(4,"VENTAS"),
        get_val(12,"VENTAS") - get_val(5,"VENTAS"),
        get_val(13,"VENTAS") - get_val(6,"VENTAS"),
    ],
    "Δ COSTO PROM": [
        get_val(11,"COSTO_PROMEDIO") - get_val(4,"COSTO_PROMEDIO"),
        get_val(12,"COSTO_PROMEDIO") - get_val(5,"COSTO_PROMEDIO"),
        get_val(13,"COSTO_PROMEDIO") - get_val(6,"COSTO_PROMEDIO"),
    ]
})

def insight(row):
    if row["Δ COSTO PROM"] > 0 and row["Δ VENTAS"] > 0:
        return "✔ Más costo → Más ventas"
    elif row["Δ COSTO PROM"] > 0 and row["Δ VENTAS"] < 0:
        return "⚠ Más costo → Menos ventas"
    elif row["Δ COSTO PROM"] < 0 and row["Δ VENTAS"] > 0:
        return "🔥 Menos costo → Más ventas"
    else:
        return "❌ Menos costo → Menos ventas"

comparaciones["INSIGHT"] = comparaciones.apply(insight, axis=1)

st.markdown("### 📊 Variación e impacto")
st.dataframe(comparaciones.style.map(color, subset=["Δ VENTAS","Δ COSTO PROM"]))