import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from jira import JIRA
import pandas as pd
from dotenv import load_dotenv

load_dotenv()


class JiraConnection:
    """Client per interagire con le API di Jira - Auto-discovery di tutti i worklog"""

    def __init__(self):
        """Inizializza la connessione a Jira"""
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'jira' in st.secrets:
                self.jira_url = st.secrets['jira']['url']
                self.jira_email = st.secrets['jira']['email']
                self.jira_token = st.secrets['jira']['api_token']
                self.team_members = list(st.secrets['jira'].get('team_members', []))
                self.non_dev_keywords = list(st.secrets['jira'].get('non_dev_keywords', []))
                self.testing_keywords = list(st.secrets['jira'].get('testing_keywords', []))
            else:
                self._load_from_env()
        except (ImportError, KeyError):
            self._load_from_env()

        if not all([self.jira_url, self.jira_email, self.jira_token]):
            raise ValueError("Credenziali Jira mancanti")

        if not self.team_members:
            raise ValueError("Lista team_members obbligatoria")

        self.client = JIRA(
            server=self.jira_url,
            basic_auth=(self.jira_email, self.jira_token)
        )

    def _load_from_env(self):
        """Carica dalle variabili d'ambiente"""
        self.jira_url = os.getenv('JIRA_URL')
        self.jira_email = os.getenv('JIRA_EMAIL')
        self.jira_token = os.getenv('JIRA_API_TOKEN')

        team_str = os.getenv('JIRA_TEAM_MEMBERS', '')
        self.team_members = [m.strip() for m in team_str.split(',') if m.strip()]

        non_dev_str = os.getenv('JIRA_NON_DEV_KEYWORDS', 'ferie,holiday,leave,pto,vacation')
        self.non_dev_keywords = [k.strip().lower() for k in non_dev_str.split(',') if k.strip()]

        testing_str = os.getenv('JIRA_TESTING_KEYWORDS', 'review,analysis,investigation')
        self.testing_keywords = [k.strip().lower() for k in testing_str.split(',') if k.strip()]

    def get_team_members(self) -> List[str]:
        """Ritorna la lista dei membri del team"""
        return self.team_members

    def get_all_worklogs_for_month(self, year: int, month: int) -> pd.DataFrame:
        """
        Scarica TUTTI i worklog di TUTTI i membri del team per il mese specificato
        Auto-discovery di tutti i progetti
        """
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(year, month + 1, 1) - timedelta(days=1)

        all_worklogs = []

        # Per ogni membro del team
        for member in self.team_members:
            print(f"Scaricamento worklog per {member}...")

            # Query JQL per tutti i worklog dell'utente nel periodo
            # Non specifichiamo il progetto - prendiamo TUTTO
            jql = f'worklogAuthor = "{member}" AND worklogDate >= "{start_date.strftime("%Y-%m-%d")}" AND worklogDate <= "{end_date.strftime("%Y-%m-%d")}"'

            try:
                issues = self.client.search_issues(jql, maxResults=1000, expand='changelog')

                for issue in issues:
                    try:
                        worklogs = self.client.worklogs(issue)

                        for worklog in worklogs:
                            # Verifica che il worklog sia dell'autore e nel periodo
                            if worklog.author.displayName == member:
                                worklog_date = datetime.strptime(worklog.started[:10], "%Y-%m-%d")

                                if worklog_date.year == year and worklog_date.month == month:
                                    # Estrai info progetto dall'issue key
                                    project_key = issue.key.split('-')[0]

                                    # Categorizza automaticamente
                                    category = self._auto_categorize(
                                        issue.fields.summary,
                                        issue.fields.issuetype.name,
                                        worklog.comment if hasattr(worklog, 'comment') else '',
                                        project_key
                                    )

                                    all_worklogs.append({
                                        'issue_key': issue.key,
                                        'project_key': project_key,
                                        'summary': issue.fields.summary,
                                        'issue_type': issue.fields.issuetype.name,
                                        'category': category,
                                        'author': member,
                                        'date': worklog_date,
                                        'time_spent_hours': worklog.timeSpentSeconds / 3600,
                                        'comment': worklog.comment if hasattr(worklog, 'comment') else ''
                                    })
                    except Exception as e:
                        print(f"Errore worklog per {issue.key}: {str(e)}")
                        continue

            except Exception as e:
                print(f"Errore ricerca per {member}: {str(e)}")
                continue

        return pd.DataFrame(all_worklogs)

    def _auto_categorize(self, summary: str, issue_type: str, comment: str, project_key: str) -> str:
        """
        Categorizzazione automatica basata su keywords
        """
        # Converti tutto in lowercase per matching
        summary_lower = summary.lower()
        issue_type_lower = issue_type.lower()
        comment_lower = comment.lower() if comment else ''
        project_lower = project_key.lower()

        # Combina tutti i testi per il matching
        full_text = f"{summary_lower} {comment_lower} {project_lower}"

        # Check Non-Development keywords
        for keyword in self.non_dev_keywords:
            if keyword.lower() in full_text:
                return 'Non-Development Activities'

        # Check Testing keywords
        for keyword in self.testing_keywords:
            if keyword.lower() in full_text:
                return 'Testing Activities'

        # Default: Development Activities
        return 'Development Activities'

    def get_unique_projects(self, worklog_df: pd.DataFrame) -> List[str]:
        """Estrae la lista unica di progetti dai worklog"""
        if worklog_df.empty:
            return []
        return sorted(worklog_df['project_key'].unique().tolist())

    def test_connection(self) -> bool:
        """Testa la connessione"""
        try:
            self.client.myself()
            return True
        except Exception as e:
            print(f"Errore: {str(e)}")
            return False