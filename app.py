# -*- coding: utf-8 -*-
"""
Trabajo final de Streamlit
Autor: Marta de Mingo
Fecha: 2025
Descripción: Dashboard de ventas con datos cargados desde OneDrive
"""

# ============================================
#  IMPORTS
# ============================================
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from io import BytesIO


# ============================================
# CONFIGURACIÓN GENERAL
# ============================================
st.set_page_config(
    page_title="Ventas Globales",
    page_icon="📊",
    layout="wide"
)


# ============================================
# FUNCIÓN PARA CARGAR LOS DATOS DESDE ONEDRIVE
# ============================================

import gdown
import pandas as pd
import streamlit as st

@st.cache_data
def cargar_datos():
    # Enlaces gdown
    url_parte_1 = "https://drive.google.com/uc?id=15mT4W0wzB0z-RAINsaCOQTSysB5uOe9x"
    url_parte_2 = "https://drive.google.com/uc?id=1xNusnLXVuRnZj_znJhvvvuwAe9lbMvar"

    # Descarga los archivos si no existen localmente
    archivo1 = "parte_1.csv"
    archivo2 = "parte_2.csv"

    gdown.download(url_parte_1, archivo1, quiet=False)
    gdown.download(url_parte_2, archivo2, quiet=False)

    # Leer CSV
    df1 = pd.read_csv(archivo1, sep=";", engine="python")
    df2 = pd.read_csv(archivo2, sep=";", engine="python")

    # Normalizar nombres de columnas
    df1.columns = df1.columns.str.strip().str.lower()
    df2.columns = df2.columns.str.strip().str.lower()

    # Concatenar
    df = pd.concat([df1, df2], ignore_index=True)

    if "unnamed: 0" in df.columns:
        df = df.drop(columns=["unnamed: 0"])

    # Convertir fechas
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values("date")
    df["onpromotion"] = df["onpromotion"].fillna(0).astype(int)

    return df






df = cargar_datos()


# ============================================
# PESTAÑA 1 — VISIÓN GLOBAL
# ============================================
def pestaña_1(df):

    st.title("📊 Visión Global de Ventas")

    st.subheader("📌 Indicadores generales")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Tiendas totales", df["store_nbr"].nunique())
    col2.metric("Tipos de productos", df["family"].nunique())
    col3.metric("Estados", df["state"].nunique())
    col4.metric("Años incluidos", df["year"].nunique())

    meses = df["date"].dt.to_period("M")

    col5.metric("Mes inicio", str(meses.min()))
    col6.metric("Mes fin", str(meses.max()))

    st.subheader("🥇 Top 10 productos más vendidos")

    top10_prod = (
        df.groupby("family")["sales"]
        .sum()
        .sort_values()
        .head(10)
        .reset_index()
    )

    fig1 = px.bar(
        top10_prod,
        x="sales",
        y="family",
        orientation="h",
        title="Top 10 Familias más vendidas",
    )
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🏬 Distribución de ventas por tienda")

    ventas_tienda = (
        df.groupby("store_nbr")["sales"]
        .sum()
        .reset_index()
        .sort_values("sales", ascending=False)
    )

    fig2 = px.bar(
        ventas_tienda,
        x="store_nbr",
        y="sales",
        title="Ventas por tienda",
    )
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("🏷️ Top 10 tiendas con ventas en promoción")

    df_promo = df[df["onpromotion"] > 0]

    top10_tiendas_promo = (
        df_promo.groupby("store_nbr")["sales"]
        .sum()
        .nlargest(10)
        .reset_index()
        .sort_values("sales")
    )

    top10_tiendas_promo["rank"] = range(1, len(top10_tiendas_promo) + 1)

    fig3 = px.bar(
        top10_tiendas_promo,
        x="sales",
        y="rank",
        orientation="h",
        title="Top 10 tiendas con ventas en promoción",
    )

    fig3.update_yaxes(
        ticktext=top10_tiendas_promo["store_nbr"],
        tickvals=top10_tiendas_promo["rank"]
    )

    st.plotly_chart(fig3, use_container_width=True)

    st.subheader("📅 Estacionalidad de las ventas")

    ventas_dias = (
        df.groupby("day_of_week")["sales"]
        .mean()
        .reindex([
            "Monday", "Tuesday", "Wednesday",
            "Thursday", "Friday", "Saturday", "Sunday"
        ])
        .reset_index()
    )

    fig4 = px.bar(
        ventas_dias,
        x="day_of_week",
        y="sales",
        title="Ventas promedio por día"
    )
    st.plotly_chart(fig4, use_container_width=True)

    ventas_week = df.groupby("week")["sales"].mean().reset_index()

    fig5 = px.line(
        ventas_week,
        x="week",
        y="sales",
        markers=True,
        title="Ventas promedio por semana del año"
    )
    st.plotly_chart(fig5, use_container_width=True)

    ventas_month = df.groupby("month")["sales"].mean().reset_index()

    fig6 = px.bar(
        ventas_month,
        x="month",
        y="sales",
        title="Ventas promedio por mes"
    )
    st.plotly_chart(fig6, use_container_width=True)


# ============================================
# PESTAÑA 2 — ANÁLISIS POR TIENDA
# ============================================
def pestaña_2(df):

    st.title("🏬 Análisis por Tienda")

    tienda_sel = st.selectbox(
        "Selecciona una tienda:",
        sorted(df["store_nbr"].unique())
    )

    df_tienda = df[df["store_nbr"] == tienda_sel]

    col1, col2 = st.columns(2)

    col1.metric(
        "📦 Total de productos vendidos",
        df_tienda["family"].count()
    )

    col2.metric(
        "🏷️ Productos vendidos en promoción",
        df_tienda[df_tienda["onpromotion"] > 0]["family"].count()
    )

    st.subheader("📈 Ventas totales por año")

    ventas_año = (
        df_tienda.groupby("year")["sales"]
        .sum()
        .reset_index()
    )

    fig1 = px.bar(ventas_año, x="year", y="sales")
    st.plotly_chart(fig1, use_container_width=True)


# ============================================
# PESTAÑA 3 — ANÁLISIS POR ESTADO
# ============================================
def pestaña_3(df):

    st.title("🗺️ Análisis por Estado")

    estado_sel = st.selectbox(
        "Selecciona un estado:",
        sorted(df["state"].unique())
    )

    df_estado = df[df["state"] == estado_sel]

    st.subheader("💳 Transacciones por año")

    transacciones_año = (
        df_estado.groupby("year")["transactions"]
        .sum()
        .reset_index()
    )

    fig1 = px.line(transacciones_año, x="year", y="transactions", markers=True)
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("🏬 Ranking de tiendas con más ventas")

    ranking_tiendas = (
        df_estado.groupby("store_nbr")["sales"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    ranking_tiendas["rank"] = range(1, len(ranking_tiendas) + 1)

    fig2 = px.bar(
        ranking_tiendas,
        x="rank",
        y="sales",
    )

    fig2.update_xaxes(
        tickvals=ranking_tiendas["rank"],
        ticktext=ranking_tiendas["store_nbr"],
        title="Tienda"
    )

    st.plotly_chart(fig2, use_container_width=True)


# ============================================
# PESTAÑA 4 — INSIGHTS PARA EL CEO
# ============================================
def pestaña_4(df):

    st.title("🚀 Insights Clave para Dirección")

    st.subheader("🌆 Ventas por ciudad")

    ventas_ciudad = df.groupby("city")["sales"].sum().reset_index()

    fig_city = px.treemap(
        ventas_ciudad,
        path=["city"],
        values="sales"
    )
    st.plotly_chart(fig_city, use_container_width=True)

    st.subheader("🏷️ Impacto de las promociones")

    promo_df = df.assign(
        tipo_venta=df["onpromotion"].apply(
            lambda x: "En promoción" if x > 0 else "Sin promoción"
        )
    )

    ventas_promo = promo_df.groupby("tipo_venta")["sales"].mean().reset_index()

    fig_promo = px.bar(
        ventas_promo,
        x="tipo_venta",
        y="sales"
    )
    st.plotly_chart(fig_promo, use_container_width=True)


# ============================================
# CREACIÓN DE PESTAÑAS
# ============================================
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
