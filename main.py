"""
Scrum - Jira QA Team Dashboard v2.0
Dashboard avanzata con metriche complete
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import calendar
from modules.connection import JiraConnection
from modules.calculator import MetricsCalculator

st.set_page_config(
    page_title="Scrum QA Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS
st.markdown("""
    <style>
    .main-header {font-size: 2.5rem; font-weight: bold; color: #1f77b4;}
    .metric-card {background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #1f77b4;}
    .kpi-box {background-color: #e8f4f8; padding: 0.8rem; border-radius: 0.5rem; margin: 0.5rem 0;}
    .project-tag {display: inline-block; padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.875rem; background-color: #d4edda; color: #155724; margin: 0.25rem;}
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_jira_connection():
    try:
        return JiraConnection()
    except Exception as e:
        st.error(f"⚠️ Errore: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def load_data(year: int, month: int, _jira_conn):
    try:
        return _jira_conn.get_all_worklogs_for_month(year, month)
    except Exception as e:
        st.error(f"Errore: {str(e)}")
        return pd.DataFrame()


def create_project_selector(jira_conn, worklog_df):
    if worklog_df.empty:
        return []

    st.sidebar.subheader("📁 Progetti")
    all_projects = jira_conn.get_unique_projects(worklog_df)

    if not all_projects:
        return []

    with st.sidebar.expander(f"ℹ️ Trovati {len(all_projects)} progetti", expanded=False):
        for proj in all_projects:
            hours = worklog_df[worklog_df['project_key'] == proj]['time_spent_hours'].sum()
            st.markdown(f'<span class="project-tag">{proj}</span> {hours:.1f}h', unsafe_allow_html=True)

    mode = st.sidebar.radio("Modalità", ["Tutti", "Seleziona"], index=0)

    if mode == "Tutti":
        st.sidebar.success(f"✅ {len(all_projects)} progetti")
        return all_projects
    else:
        selected = st.sidebar.multiselect("Progetti", all_projects, default=all_projects)
        return selected if selected else []


def create_nda_breakdown_chart(nda_breakdown_df):
    if nda_breakdown_df.empty:
        return None

    fig = go.Figure(data=[go.Bar(
        y=nda_breakdown_df['NDA Type'],
        x=nda_breakdown_df['Hours'],
        orientation='h',
        text=nda_breakdown_df['Hours'].round(2),
        textposition='auto',
        marker_color='#e74c3c'
    )])

    fig.update_layout(
        title='NDA Breakdown by Type',
        xaxis_title='Hours',
        yaxis_title='NDA Type',
        height=400
    )

    return fig


def create_kpi_card(title, value, subtitle=""):
    return f"""
    <div class="kpi-box">
        <h4 style="margin:0; color:#1f77b4;">{title}</h4>
        <h2 style="margin:0.25rem 0;">{value}</h2>
        <p style="margin:0; font-size:0.875rem; color:#666;">{subtitle}</p>
    </div>
    """


def main():
    st.markdown('<h1 class="main-header">🎯 Scrum - QA Dashboard v2.0</h1>', unsafe_allow_html=True)
    st.markdown("---")

    jira_conn = get_jira_connection()
    if jira_conn is None or not jira_conn.test_connection():
        st.error("❌ Connessione fallita")
        st.stop()

    st.success("✅ Connesso!")

    with st.sidebar:
        st.header("⚙️ Configurazione")

        current_date = datetime.now()
        selected_year = st.selectbox("Anno", list(range(current_date.year - 2, current_date.year + 1)), index=2)
        selected_month = st.selectbox("Mese", list(range(1, 13)), format_func=lambda x: calendar.month_name[x],
                                      index=current_date.month - 1)

        # Working days selector
        working_days = st.number_input("Giorni lavorativi", min_value=1, max_value=31, value=20,
                                       help="Giorni lavorativi nel mese per calcolo MD")

        st.markdown("---")
        team_members = ["Tutti"] + jira_conn.get_team_members()
        selected_member = st.selectbox("Team Member", team_members)

        st.markdown("---")
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with st.spinner("📊 Caricamento..."):
        worklog_df = load_data(selected_year, selected_month, jira_conn)

    if worklog_df.empty:
        st.warning(f"⚠️ Nessun dato per {calendar.month_name[selected_month]} {selected_year}")
        return

    st.sidebar.markdown("---")
    selected_projects = create_project_selector(jira_conn, worklog_df)

    if selected_projects:
        worklog_df = worklog_df[worklog_df['project_key'].isin(selected_projects)]

    if worklog_df.empty:
        st.warning("⚠️ Nessun dato per i progetti selezionati")
        return

    if selected_member != "Tutti":
        worklog_df = worklog_df[worklog_df['author'] == selected_member]
        if worklog_df.empty:
            st.warning(f"⚠️ Nessun dato per {selected_member}")
            return

    # Calcola TUTTE le metriche
    calculator = MetricsCalculator()

    velocity_df = worklog_df.copy()
    velocity_df['original_estimate'] = velocity_df['time_spent_hours'] * 0.9
    velocity_df['time_spent'] = velocity_df['time_spent_hours']

    velocity_metrics = calculator.calculate_velocity(velocity_df)
    distribution_df = calculator.calculate_activity_distribution(worklog_df)
    da_nda_metrics = calculator.calculate_da_vs_nda_ratio(worklog_df)
    team_overview_df = calculator.calculate_team_overview(worklog_df)
    daily_dist_df = calculator.calculate_daily_distribution(worklog_df)
    quality_indicators = calculator.get_quality_indicators(worklog_df)

    # NUOVE METRICHE
    nda_breakdown_df = calculator.calculate_nda_breakdown(worklog_df)
    advanced_kpis = calculator.calculate_advanced_kpis(worklog_df, working_days)
    squad_analysis_df = calculator.calculate_squad_analysis(worklog_df)
    ticket_analysis = calculator.calculate_ticket_analysis(worklog_df)

    st.info(f"📁 Progetti: {', '.join(selected_projects)} | 📅 {calendar.month_name[selected_month]} {selected_year}")

    # === SEZIONE KPI AVANZATI ===
    st.header("📊 KPI Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_kpi_card(
            "Total Man Days",
            f"{advanced_kpis['total_md']} MD",
            f"{worklog_df['author'].nunique()} contributors × {working_days} days"
        ), unsafe_allow_html=True)

    with col2:
        st.markdown(create_kpi_card(
            "Available MD",
            f"{advanced_kpis['available_md']} MD",
            f"{advanced_kpis['ratio_available_total']}% of total"
        ), unsafe_allow_html=True)

    with col3:
        st.markdown(create_kpi_card(
            "Logged MD",
            f"{advanced_kpis['logged_md']} MD",
            f"{advanced_kpis['ratio_logged_available']}% of available"
        ), unsafe_allow_html=True)

    with col4:
        st.markdown(create_kpi_card(
            "Delivered MD",
            f"{advanced_kpis['delivered_md']} MD",
            f"{advanced_kpis['ratio_delivered_total']}% of total"
        ), unsafe_allow_html=True)

    # Ratios
    st.subheader("📈 Ratios")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("A. Available/Total", f"{advanced_kpis['ratio_available_total']}%",
                  help="% tempo disponibile per dev (escl. NDA)")

    with col2:
        st.metric("B. Logged/Available", f"{advanced_kpis['ratio_logged_available']}%",
                  help="% tempo loggato su disponibile")

    with col3:
        st.metric("C. Logged/Total", f"{advanced_kpis['ratio_logged_total']}%",
                  help="% tempo loggato su totale")

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric("D. Delivered/Total", f"{advanced_kpis['ratio_delivered_total']}%",
                  help="% tempo delivered su totale")

    with col5:
        st.metric("F. On Demand/Available", f"{advanced_kpis['ratio_on_demand_available']}%",
                  help="% on demand su disponibile")

    with col6:
        ratio = da_nda_metrics['da_nda_ratio']
        st.metric("DA:NDA Ratio", f"{ratio:.2f}:1" if ratio != 'N/A' else 'N/A')

    st.markdown("---")

    # === NDA BREAKDOWN DETTAGLIATO ===
    st.header("🔴 NDA Breakdown Dettagliato")

    if not nda_breakdown_df.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = create_nda_breakdown_chart(nda_breakdown_df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("NDA Details")
            st.dataframe(nda_breakdown_df, use_container_width=True, hide_index=True)

            st.metric("Total NDA Hours", f"{nda_breakdown_df['Hours'].sum():.2f}h")
            st.metric("Total NDA MD", f"{advanced_kpis['nda_md']} MD")
    else:
        st.info("Nessuna attività NDA trovata")

    st.markdown("---")

    # === SQUAD/PROJECT ANALYSIS ===
    st.header("👥 Squad/Project Analysis")

    if not squad_analysis_df.empty:
        col1, col2 = st.columns([3, 2])

        with col1:
            fig = go.Figure(data=[go.Bar(
                x=squad_analysis_df['Squad/Project'],
                y=squad_analysis_df['Man Days (MD)'],
                text=squad_analysis_df['Man Days (MD)'],
                textposition='auto',
                marker_color='#3498db'
            )])
            fig.update_layout(title='Man Days by Squad/Project', height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Squad Metrics")
            st.dataframe(squad_analysis_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # === METRICHE BASE (già esistenti) ===
    st.header("📈 Core Metrics")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Hours", f"{worklog_df['time_spent_hours'].sum():.1f}h")
    with col2:
        st.metric("Unique Tickets", ticket_analysis['unique_tickets'])
    with col3:
        st.metric("Worklog Entries", ticket_analysis['total_worklog_entries'])
    with col4:
        st.metric("Avg Hours/Ticket", f"{ticket_analysis['avg_hours_per_ticket']:.2f}h")

    st.markdown("---")

    # Activity Distribution (già esistente)
    st.header("📊 Activity Distribution")
    col1, col2 = st.columns(2)

    with col1:
        if not distribution_df.empty:
            colors = {'Development Activities': '#2ecc71', 'Non-Development Activities': '#e74c3c',
                      'Testing Activities': '#f39c12'}
            fig = go.Figure(data=[go.Pie(
                labels=distribution_df['Category'],
                values=distribution_df['Total Hours'],
                hole=0.4,
                marker_colors=[colors.get(cat, '#95a5a6') for cat in distribution_df['Category']]
            )])
            fig.update_layout(title='Activity Distribution', height=450)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if not distribution_df.empty:
            st.dataframe(distribution_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Team Overview
    if selected_member == "Tutti" and not team_overview_df.empty:
        st.header("👥 Team Overview")
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure(data=[go.Bar(
                x=team_overview_df['Team Member'],
                y=team_overview_df['Total Hours'],
                text=team_overview_df['Total Hours'],
                textposition='auto',
                marker_color='#3498db'
            )])
            fig.update_layout(title='Team Comparison', height=400)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.dataframe(team_overview_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Quality Indicators
    st.header("💎 Quality Indicators")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Consistency", f"{quality_indicators['consistency_score']:.1f}%")
    with col2:
        st.metric("Balance", f"{quality_indicators['distribution_balance']:.1f}%")
    with col3:
        st.metric("Completion", f"{quality_indicators['completion_rate']:.1f}%")


if __name__ == "__main__":
    main()