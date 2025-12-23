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

# CSS Pulito e Professionale - Minimalista
st.markdown("""
    <style>
    /* Main background */
    .main {
        background-color: #ffffff;
    }

    /* Headers puliti */
    h1 {
        color: #1a1a1a;
        font-weight: 600;
        padding-bottom: 1rem;
        border-bottom: 3px solid #0066cc;
    }

    h2 {
        color: #333333;
        font-weight: 600;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }

    h3 {
        color: #555555;
        font-weight: 500;
    }

    /* Metric cards - Sfondo bianco pulito */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #0066cc;
        font-weight: 700;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        color: #666666;
        font-weight: 500;
    }

    /* Info box pulita */
    .stAlert {
        background-color: #f8f9fa;
        border-left: 4px solid #0066cc;
        color: #333333;
    }

    /* Dataframe styling */
    .dataframe {
        font-size: 0.9rem;
        border: 1px solid #e0e0e0;
    }

    .dataframe thead th {
        background-color: #f8f9fa;
        color: #333333;
        font-weight: 600;
        border-bottom: 2px solid #0066cc;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }

    /* Buttons */
    .stButton button {
        background-color: #0066cc;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        font-weight: 500;
    }

    .stButton button:hover {
        background-color: #0052a3;
    }

    /* Separatori sottili */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid #e0e0e0;
    }

    /* Project tags semplici */
    .project-tag {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        margin: 0.25rem;
        background-color: #e3f2fd;
        color: #0066cc;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 500;
    }

    /* Box KPI custom - Puliti */
    .kpi-card {
        background-color: #ffffff;
        border: 2px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .kpi-card h4 {
        margin: 0 0 0.5rem 0;
        color: #666666;
        font-size: 0.9rem;
        font-weight: 500;
        text-transform: uppercase;
    }

    .kpi-card h2 {
        margin: 0.5rem 0;
        color: #0066cc;
        font-size: 2.5rem;
        font-weight: 700;
    }

    .kpi-card p {
        margin: 0.5rem 0 0 0;
        color: #888888;
        font-size: 0.85rem;
    }

    .kpi-card.green h2 { color: #28a745; }
    .kpi-card.orange h2 { color: #fd7e14; }
    .kpi-card.red h2 { color: #dc3545; }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_jira_connection():
    try:
        return JiraConnection()
    except Exception as e:
        st.error(f"⚠️ Errore connessione: {str(e)}")
        return None


@st.cache_data(ttl=3600)
def load_data(year: int, month: int, _jira_conn):
    try:
        return _jira_conn.get_all_worklogs_for_month(year, month)
    except Exception as e:
        st.error(f"Errore caricamento dati: {str(e)}")
        return pd.DataFrame()


def create_project_selector(jira_conn, worklog_df):
    if worklog_df.empty:
        return []

    st.sidebar.markdown("### 📁 Progetti")
    all_projects = jira_conn.get_unique_projects(worklog_df)

    if not all_projects:
        return []

    with st.sidebar.expander(f"Trovati {len(all_projects)} progetti", expanded=False):
        for proj in all_projects:
            hours = worklog_df[worklog_df['project_key'] == proj]['time_spent_hours'].sum()
            st.markdown(f'<span class="project-tag">{proj}</span> **{hours:.1f}h**', unsafe_allow_html=True)

    mode = st.sidebar.radio("Modalità", ["Tutti", "Seleziona"], index=0)

    if mode == "Tutti":
        st.sidebar.success(f"✅ Tutti i progetti")
        return all_projects
    else:
        selected = st.sidebar.multiselect("Seleziona progetti", all_projects, default=all_projects)
        return selected if selected else []


def create_kpi_card(title, value, subtitle="", color="blue"):
    color_class = {
        "blue": "",
        "green": "green",
        "orange": "orange",
        "red": "red"
    }.get(color, "")

    return f"""
    <div class="kpi-card {color_class}">
        <h4>{title}</h4>
        <h2>{value}</h2>
        <p>{subtitle}</p>
    </div>
    """


def main():
    st.title("🎯 Scrum - QA Dashboard v2.0")

    jira_conn = get_jira_connection()
    if jira_conn is None or not jira_conn.test_connection():
        st.error("❌ Impossibile connettersi a Jira")
        st.stop()

    st.success("✅ Connesso a Jira")

    # === SIDEBAR ===
    with st.sidebar:
        st.markdown("### ⚙️ Configurazione")

        current_date = datetime.now()
        selected_year = st.selectbox("Anno", list(range(current_date.year - 2, current_date.year + 1)), index=2)
        selected_month = st.selectbox("Mese", list(range(1, 13)), format_func=lambda x: calendar.month_name[x],
                                      index=current_date.month - 1)

        working_days = st.number_input("Giorni lavorativi", min_value=1, max_value=31, value=20)

        st.markdown("---")
        team_members = ["Tutti"] + jira_conn.get_team_members()
        selected_member = st.selectbox("Team Member", team_members)

        st.markdown("---")
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # === LOAD DATA ===
    with st.spinner("📊 Caricamento..."):
        worklog_df = load_data(selected_year, selected_month, jira_conn)

    if worklog_df.empty:
        st.warning(f"⚠️ Nessun dato per {calendar.month_name[selected_month]} {selected_year}")
        return

    # === PROJECT FILTER ===
    st.sidebar.markdown("---")
    selected_projects = create_project_selector(jira_conn, worklog_df)

    if selected_projects:
        worklog_df = worklog_df[worklog_df['project_key'].isin(selected_projects)]

    if worklog_df.empty:
        st.warning("⚠️ Nessun dato per i progetti selezionati")
        return

    # === MEMBER FILTER ===
    if selected_member != "Tutti":
        worklog_df = worklog_df[worklog_df['author'] == selected_member]
        if worklog_df.empty:
            st.warning(f"⚠️ Nessun dato per {selected_member}")
            return

    # === CALCULATE METRICS ===
    calculator = MetricsCalculator()

    velocity_df = worklog_df.copy()
    velocity_df['original_estimate'] = velocity_df['time_spent_hours'] * 0.9
    velocity_df['time_spent'] = velocity_df['time_spent_hours']

    distribution_df = calculator.calculate_activity_distribution(worklog_df)
    da_nda_metrics = calculator.calculate_da_vs_nda_ratio(worklog_df)
    team_overview_df = calculator.calculate_team_overview(worklog_df)
    nda_breakdown_df = calculator.calculate_nda_breakdown(worklog_df)
    advanced_kpis = calculator.calculate_advanced_kpis(worklog_df, working_days)
    squad_analysis_df = calculator.calculate_squad_analysis(worklog_df)
    ticket_analysis = calculator.calculate_ticket_analysis(worklog_df)

    # === PERIOD INFO ===
    projects_display = ', '.join(selected_projects[:3])
    if len(selected_projects) > 3:
        projects_display += f" (+{len(selected_projects) - 3} altri)"

    st.info(f"📁 {projects_display} | 📅 {calendar.month_name[selected_month]} {selected_year}")

    # === KPI OVERVIEW ===
    st.header("📊 KPI Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(create_kpi_card(
            "Total Man Days",
            f"{advanced_kpis['total_md']}",
            f"{worklog_df['author'].nunique()} × {working_days} days"
        ), unsafe_allow_html=True)

    with col2:
        color = "green" if advanced_kpis['ratio_available_total'] > 50 else "orange"
        st.markdown(create_kpi_card(
            "Available MD",
            f"{advanced_kpis['available_md']}",
            f"{advanced_kpis['ratio_available_total']}% of total",
            color
        ), unsafe_allow_html=True)

    with col3:
        color = "green" if advanced_kpis['ratio_logged_available'] > 70 else "orange"
        st.markdown(create_kpi_card(
            "Logged MD",
            f"{advanced_kpis['logged_md']}",
            f"{advanced_kpis['ratio_logged_available']}% of available",
            color
        ), unsafe_allow_html=True)

    with col4:
        st.markdown(create_kpi_card(
            "Delivered MD",
            f"{advanced_kpis['delivered_md']}",
            f"{advanced_kpis['ratio_delivered_total']}% of total",
            "blue"
        ), unsafe_allow_html=True)

    # === RATIOS ===
    st.markdown("### 📈 Key Ratios")

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("A. Available/Total", f"{advanced_kpis['ratio_available_total']}%")
    with col2:
        st.metric("B. Logged/Available", f"{advanced_kpis['ratio_logged_available']}%")
    with col3:
        st.metric("C. Logged/Total", f"{advanced_kpis['ratio_logged_total']}%")
    with col4:
        st.metric("D. Delivered/Total", f"{advanced_kpis['ratio_delivered_total']}%")
    with col5:
        st.metric("F. On Demand/Avail", f"{advanced_kpis['ratio_on_demand_available']}%")
    with col6:
        ratio = da_nda_metrics['da_nda_ratio']
        st.metric("DA:NDA", f"{ratio:.1f}:1" if ratio != 'N/A' else 'N/A')

    st.markdown("---")

    # === NDA BREAKDOWN ===
    st.header("🔴 NDA Breakdown")

    if not nda_breakdown_df.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure(data=[go.Bar(
                y=nda_breakdown_df['NDA Type'],
                x=nda_breakdown_df['Hours'],
                orientation='h',
                text=nda_breakdown_df['Hours'].round(1),
                textposition='auto',
                marker_color='#dc3545'
            )])
            fig.update_layout(
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Hours",
                yaxis_title="",
                font=dict(size=12)
            )
            fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Dettaglio NDA**")
            st.dataframe(nda_breakdown_df, hide_index=True, use_container_width=True)
            st.metric("Total NDA", f"{nda_breakdown_df['Hours'].sum():.1f}h")
    else:
        st.info("✅ Nessuna NDA")

    st.markdown("---")

    # === SQUAD ANALYSIS ===
    st.header("👥 Squad/Project Analysis")

    if not squad_analysis_df.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure(data=[go.Bar(
                x=squad_analysis_df['Squad/Project'],
                y=squad_analysis_df['Man Days (MD)'],
                text=squad_analysis_df['Man Days (MD)'].round(1),
                textposition='auto',
                marker_color='#0066cc'
            )])
            fig.update_layout(
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Squad/Project",
                yaxis_title="Man Days",
                font=dict(size=12)
            )
            fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Squad Metrics**")
            st.dataframe(squad_analysis_df, hide_index=True, use_container_width=True)

    st.markdown("---")

    # === CORE METRICS ===
    st.header("📈 Core Metrics")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Hours", f"{worklog_df['time_spent_hours'].sum():.1f}h")
    with col2:
        st.metric("Unique Tickets", ticket_analysis['unique_tickets'])
    with col3:
        st.metric("Worklog Entries", ticket_analysis['total_worklog_entries'])
    with col4:
        st.metric("Avg Hours/Ticket", f"{ticket_analysis['avg_hours_per_ticket']:.1f}h")

    st.markdown("---")

    # === ACTIVITY DISTRIBUTION ===
    st.header("📊 Activity Distribution")

    if not distribution_df.empty:
        col1, col2 = st.columns([2, 1])

        with col1:
            colors = {
                'Development Activities': '#28a745',
                'Non-Development Activities': '#dc3545',
                'Testing Activities': '#fd7e14'
            }

            fig = go.Figure(data=[go.Pie(
                labels=distribution_df['Category'],
                values=distribution_df['Total Hours'],
                hole=0.4,
                marker_colors=[colors.get(cat, '#6c757d') for cat in distribution_df['Category']],
                textinfo='label+percent',
                textfont_size=13
            )])
            fig.update_layout(
                height=400,
                paper_bgcolor='white',
                showlegend=True,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Distribution**")
            st.dataframe(distribution_df, hide_index=True, use_container_width=True)

    st.markdown("---")

    # === TEAM OVERVIEW ===
    if selected_member == "Tutti" and not team_overview_df.empty:
        st.header("👥 Team Overview")

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = go.Figure(data=[go.Bar(
                x=team_overview_df['Team Member'],
                y=team_overview_df['Total Hours'],
                text=team_overview_df['Total Hours'].round(1),
                textposition='auto',
                marker_color='#0066cc'
            )])
            fig.update_layout(
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Team Member",
                yaxis_title="Hours",
                font=dict(size=12)
            )
            fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**Team Metrics**")
            st.dataframe(team_overview_df, hide_index=True, use_container_width=True)


if __name__ == "__main__":
    main()