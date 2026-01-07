# -*- coding: utf-8 -*-
"""
Trabajo final de Streamlit
Autor: Marta de Mingo
Fecha: 2025
Descripción: App Streamlit completa lista para Cloud con CSV divididos
"""
import streamlit as st
import pandas as pd
import plotly.express as px

# ========================================================
# CONFIGURACIÓN GENERAL
# ========================================================
st.set_page_config(
    page_title="Ventas Globales",
    page_icon="📊",
    layout="wide"
)

# ========================================================
# FUNCIÓN PARA CARGAR LOS DATOS
# ========================================================
@st.cache_data
def cargar_datos():
    # Lista de archivos CSV ya divididos y subidos al repositorio
    archivos = [
        "data/parte_1.csv",
        "data/parte_2.csv",
        # Añade más partes si es necesario
    ]

    df_list = []
    for archivo in archivos:
        df_temp = pd.read_csv(
            archivo,
            sep=",",
            engine="python",
            skipinitialspace=True
        )
        df_list.append(df_temp)

    df = pd.concat(df_list, ignore_index=True)

    # Normalizar nombres de columnas
    df.columns = df.columns.str.strip().str.lower()
    if "unnamed: 0" in df.columns:
        df = df.drop(columns=["unnamed: 0"])

    # Convertir fecha
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")

    # Rellenar onpromotion
    df["onpromotion"] = df["onpromotion"].fillna(0).astype(int)

    # Columnas auxiliares
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["week"] = df["date"].dt.isocalendar().week
    df["day_of_week"] = df["date"].dt.day_name()

    return df

# ========================================================
# CARGAR DATOS
# ========================================================
df = cargar_datos()

# ========================================================
# PESTAÑA 1 — VISIÓN GLOBAL
# ========================================================
def pestaña_1(df):
    st.title("📊 Visión Global de Ventas")
    st.subheader("📌 Indicadores generales")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Tiendas totales", df["store_nbr"].nunique())
    col2.metric("Tipos de productos", df["family"].nunique())
    col3.metric("Estados", df["state"].nunique())
    col4.metric("Años incluidos", df["year"].nunique())
    meses = df["date"].dt.to_period("M").sort_values().unique()
    col5.metric("Mes inicio", str(meses.min()))
    col6.metric("Mes fin", str(meses.max()))

    # Top 10 productos
    st.subheader("🥇 Top 10 productos más vendidos")
    top10_prod = df.groupby("family")["sales"].sum().sort_values(ascending=False).head(10).reset_index()
    fig1 = px.bar(top10_prod, x="sales", y="family", orientation="h", title="Top 10 Familias más vendidas")
    st.plotly_chart(fig1, use_container_width=True)

    # Ventas por tienda
    st.subheader("🏬 Distribución de ventas por tienda")
    ventas_tienda = df.groupby("store_nbr")["sales"].sum().reset_index().sort_values("sales", ascending=False)
    fig2 = px.bar(ventas_tienda, x="store_nbr", y="sales", title="Ventas por tienda")
    st.plotly_chart(fig2, use_container_width=True)

    # Ventas en promoción
    st.subheader("🏷️ Top 10 tiendas con ventas en productos en promoción")
    df_promo = df[df["onpromotion"] > 0]
    top10_tiendas_promo = df_promo.groupby("store_nbr")["sales"].sum().nlargest(10).reset_index().sort_values("sales")
    top10_tiendas_promo["rank"] = range(1, len(top10_tiendas_promo) + 1)
    fig3 = px.bar(top10_tiendas_promo, x="sales", y="rank", orientation="h", title="Top 10 tiendas con ventas en promoción")
    fig3.update_yaxes(ticktext=top10_tiendas_promo["store_nbr"], tickvals=top10_tiendas_promo["rank"])
    st.plotly_chart(fig3, use_container_width=True)

    # Estacionalidad
    st.subheader("📅 Estacionalidad de las ventas")
    ventas_dias = df.groupby("day_of_week")["sales"].mean().reindex(
        ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    ).reset_index()
    fig4 = px.bar(ventas_dias, x="day_of_week", y="sales", title="Ventas promedio por día")
    st.plotly_chart(fig4, use_container_width=True)

    ventas_week = df.groupby("week")["sales"].mean().reset_index()
    fig5 = px.line(ventas_week, x="week", y="sales", markers=True, title="Ventas promedio por semana del año")
    st.plotly_chart(fig5, use_container_width=True)

    ventas_month = df.groupby("month")["sales"].mean().reset_index()
    fig6 = px.bar(ventas_month, x="month", y="sales", title="Ventas promedio por mes")
    st.plotly_chart(fig6, use_container_width=True)

# ========================================================
# PESTAÑA 2 — ANÁLISIS POR TIENDA
# ========================================================
def pestaña_2(df):
    st.title("🏬 Análisis por Tienda")
    tiendas = sorted(df["store_nbr"].unique())
    tienda_sel = st.selectbox("Selecciona una tienda:", tiendas)
    df_tienda = df[df["store_nbr"] == tienda_sel]
    st.markdown(f"### Resultados para la tienda **{tienda_sel}**")

    col1, col2 = st.columns(2)
    col1.metric("📦 Total de productos vendidos", df_tienda["family"].count())
    col2.metric("🏷️ Productos vendidos en promoción", df_tienda[df_tienda["onpromotion"] > 0]["family"].count())
    st.markdown("---")

    st.subheader("📈 Ventas totales por año")
    ventas_año = df_tienda.groupby("year")["sales"].sum().sort_index().reset_index()
    fig1 = px.bar(ventas_año, x="year", y="sales")
    st.plotly_chart(fig1, use_container_width=True)

# ========================================================
# PESTAÑA 3 — ANÁLISIS POR ESTADO
# ========================================================
def pestaña_3(df):
    st.title("🗺️ Análisis por Estado")
    estados = sorted(df["state"].unique())
    estado_sel = st.selectbox("Selecciona un estado:", estados)
    df_estado = df[df["state"] == estado_sel]
    st.markdown(f"### Resultados para el estado **{estado_sel}**")

    st.subheader("💳 Transacciones por año")
    transacciones_año = df_estado.groupby("year")["transactions"].sum().reset_index()
    fig1 = px.line(transacciones_año, x="year", y="transactions", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🏬 Ranking de tiendas con más ventas")
    ranking_tiendas = df_estado.groupby("store_nbr")["sales"].sum().sort_values(ascending=False).reset_index()
    ranking_tiendas["rank"] = range(1, len(ranking_tiendas) + 1)
    fig2 = px.bar(ranking_tiendas, x="rank", y="sales")
    fig2.update_xaxes(tickvals=ranking_tiendas["rank"], ticktext=ranking_tiendas["store_nbr"], title="Tienda")
    fig2.update_yaxes(title="Ventas")
    st.plotly_chart(fig2, use_container_width=True)

    prod_top = df_estado.groupby("family")["sales"].sum().reset_index().sort_values("sales", ascending=False).iloc[0]
    st.metric("Producto más vendido", prod_top["family"])
    fig3 = px.bar(df_estado.groupby("family")["sales"].sum().reset_index(), x="family", y="sales", title="Ventas por producto")
    st.plotly_chart(fig3, use_container_width=True)

# ========================================================
# PESTAÑA 4 — INSIGHTS PARA EL CEO
# ========================================================
def pestaña_4(df):
    st.title("🚀 Insights Clave para Dirección")
    st.markdown("Panel ejecutivo orientado a la toma de decisiones estratégicas del CEO y del Director de Ventas.")

    # Ventas por ciudad
    st.subheader("🌆 Ventas por ciudad")
    ventas_ciudad = df.groupby("city")["sales"].sum().reset_index()
    fig_city = px.treemap(ventas_ciudad, path=["city"], values="sales")
    st.plotly_chart(fig_city, use_container_width=True)
    st.markdown("---")

    # Estados con mayor y menor volumen
    st.subheader("🗺️ Estados con mayor y menor volumen de ventas")
    ventas_estado = df.groupby("state")["sales"].sum().sort_values(ascending=False).reset_index()
    top5 = ventas_estado.head(5).copy()
    low5 = ventas_estado.tail(5).copy()
    reemplazos = {"Santo Domingo de los Tsachilas": "Santo Domingo<br>de los Tsáchilas"}
    top5["state_label"] = top5["state"].replace(reemplazos)
    low5["state_label"] = low5["state"].replace(reemplazos)
    y_max = ventas_estado["sales"].max()
    col1, col2 = st.columns(2)
    fig_top = px.bar(top5, x="state_label", y="sales", title="Estados con mayor volumen de ventas")
    fig_top.update_layout(yaxis_range=[0, y_max])
    fig_low = px.bar(low5, x="state_label", y="sales", title="Estados con menor volumen de ventas")
    fig_low.update_layout(yaxis_range=[0, y_max])
    col1.plotly_chart(fig_top, use_container_width=True)
    col2.plotly_chart(fig_low, use_container_width=True)
    st.markdown("---")

    # Concentración 80/20
    st.subheader("🏬 Concentración de ventas por tiendas (Principio 80/20)")
    ventas_tienda = df.groupby("store_nbr")["sales"].sum().sort_values(ascending=False).reset_index()
    ventas_tienda["ventas_acumuladas"] = ventas_tienda["sales"].cumsum()
    ventas_tienda["porcentaje_acumulado"] = ventas_tienda["ventas_acumuladas"] / ventas_tienda["sales"].sum() * 100
    fig_pareto = px.line(ventas_tienda, x=ventas_tienda.index + 1, y="porcentaje_acumulado", markers=True,
                         labels={"x": "Número de tiendas", "porcentaje_acumulado": "% de ventas acumuladas"},
                         title="¿Cuántas tiendas generan el 80% de las ventas?")
    fig_pareto.add_hline(y=80, line_dash="dash", line_color="red",
                          annotation_text="80% de las ventas", annotation_position="bottom right")
    st.plotly_chart(fig_pareto, use_container_width=True)
    st.markdown("---")

    # Impacto de promociones
    st.subheader("🏷️ Impacto de las promociones en las ventas")
    promo_df = df.assign(tipo_venta=df["onpromotion"].apply(lambda x: "En promoción" if x > 0 else "Sin promoción"))
    ventas_promo = promo_df.groupby("tipo_venta")["sales"].mean().reset_index()
    fig_promo = px.bar(ventas_promo, x="tipo_venta", y="sales", title="Ventas medias con y sin promoción")
    st.plotly_chart(fig_promo, use_container_width=True)
    st.markdown("---")

    # Crecimiento interanual
    st.subheader("📈 Evolución y crecimiento interanual de ventas")
    ventas_year = df.groupby("year")["sales"].sum().reset_index().sort_values("year")
    ventas_year["crecimiento_%"] = ventas_year["sales"].pct_change() * 100
    col1, col2 = st.columns(2)
    fig_sales = px.line(ventas_year, x="year", y="sales", markers=True, title="Ventas totales por año")
    fig_growth = px.bar(ventas_year.dropna(), x="year", y="crecimiento_%", title="Crecimiento interanual (%)")
    col1.plotly_chart(fig_sales, use_container_width=True)
    col2.plotly_chart(fig_growth, use_container_width=True)

# ========================================================
# CREAR LAS PESTAÑAS
# ========================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visión Global",
    "🏬 Por Tienda",
    "🗺️ Por Estado",
    "🚀 CEO Insights"
])

with tab1:
    pestaña_1(df)

with tab2:
    pestaña_2(df)

with tab3:
    pestaña_3(df)

with tab4:
    pestaña_4(df)
