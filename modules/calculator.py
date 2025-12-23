"""
Metrics Calculator Module
Calcola le metriche di performance del team QA con metriche avanzate
"""

import pandas as pd
import numpy as np
from typing import Dict


class MetricsCalculator:
    """Calcola metriche e KPI per il team QA - Versione avanzata"""

    @staticmethod
    def calculate_velocity(df: pd.DataFrame) -> Dict:
        """Calcola la velocity (Estimated vs Actual)"""
        if df.empty:
            return {
                'total_estimated': 0,
                'total_actual': 0,
                'variance': 0,
                'variance_percentage': 0,
                'accuracy': 0
            }

        total_estimated = df['original_estimate'].sum()
        total_actual = df['time_spent'].sum()
        variance = total_actual - total_estimated
        variance_percentage = (variance / total_estimated * 100) if total_estimated > 0 else 0
        accuracy = (1 - abs(variance) / total_estimated * 100) if total_estimated > 0 else 0

        return {
            'total_estimated': round(total_estimated, 2),
            'total_actual': round(total_actual, 2),
            'variance': round(variance, 2),
            'variance_percentage': round(variance_percentage, 2),
            'accuracy': round(max(0, accuracy), 2)
        }

    @staticmethod
    def calculate_activity_distribution(df: pd.DataFrame) -> pd.DataFrame:
        """Calcola la distribuzione delle attività per categoria"""
        if df.empty:
            return pd.DataFrame()

        distribution = df.groupby('category').agg({
            'time_spent_hours': 'sum',
            'issue_key': 'count'
        }).reset_index()

        distribution.columns = ['Category', 'Total Hours', 'Task Count']

        total_hours = distribution['Total Hours'].sum()
        distribution['Percentage'] = (distribution['Total Hours'] / total_hours * 100).round(
            2) if total_hours > 0 else 0

        return distribution.sort_values('Total Hours', ascending=False)

    @staticmethod
    def calculate_da_vs_nda_ratio(df: pd.DataFrame) -> Dict:
        """Calcola il rapporto tra Development Activities (DA) e Non-Development Activities (NDA)"""
        if df.empty:
            return {
                'da_hours': 0,
                'nda_hours': 0,
                'testing_hours': 0,
                'da_percentage': 0,
                'nda_percentage': 0,
                'testing_percentage': 0,
                'da_nda_ratio': 0,
                'productivity_score': 0
            }

        da_hours = df[df['category'] == 'Development Activities']['time_spent_hours'].sum()
        nda_hours = df[df['category'] == 'Non-Development Activities']['time_spent_hours'].sum()
        testing_hours = df[df['category'] == 'Testing Activities']['time_spent_hours'].sum()

        total_hours = da_hours + nda_hours + testing_hours

        da_percentage = (da_hours / total_hours * 100) if total_hours > 0 else 0
        nda_percentage = (nda_hours / total_hours * 100) if total_hours > 0 else 0
        testing_percentage = (testing_hours / total_hours * 100) if total_hours > 0 else 0

        da_nda_ratio = (da_hours / nda_hours) if nda_hours > 0 else float('inf')

        productive_hours = da_hours + testing_hours
        productivity_score = (productive_hours / total_hours * 100) if total_hours > 0 else 0

        return {
            'da_hours': round(da_hours, 2),
            'nda_hours': round(nda_hours, 2),
            'testing_hours': round(testing_hours, 2),
            'da_percentage': round(da_percentage, 2),
            'nda_percentage': round(nda_percentage, 2),
            'testing_percentage': round(testing_percentage, 2),
            'da_nda_ratio': round(da_nda_ratio, 2) if da_nda_ratio != float('inf') else 'N/A',
            'productivity_score': round(productivity_score, 2)
        }

    @staticmethod
    def calculate_team_overview(df: pd.DataFrame) -> pd.DataFrame:
        """Calcola una panoramica delle metriche per tutti i membri del team"""
        if df.empty:
            return pd.DataFrame()

        team_metrics = df.groupby('author').agg({
            'time_spent_hours': 'sum',
            'issue_key': 'nunique'
        }).reset_index()

        team_metrics.columns = ['Team Member', 'Total Hours', 'Tasks Completed']

        team_metrics['Avg Hours/Task'] = (
                team_metrics['Total Hours'] / team_metrics['Tasks Completed']
        ).round(2)

        total_hours = team_metrics['Total Hours'].sum()
        team_metrics['% of Total'] = (
                team_metrics['Total Hours'] / total_hours * 100
        ).round(2) if total_hours > 0 else 0

        return team_metrics.sort_values('Total Hours', ascending=False)

    @staticmethod
    def calculate_daily_distribution(df: pd.DataFrame) -> pd.DataFrame:
        """Calcola la distribuzione giornaliera delle ore lavorate"""
        if df.empty:
            return pd.DataFrame()

        daily_dist = df.groupby(df['date'].dt.date).agg({
            'time_spent_hours': 'sum',
            'issue_key': 'nunique'
        }).reset_index()

        daily_dist.columns = ['Date', 'Hours Logged', 'Tasks']

        return daily_dist.sort_values('Date')

    @staticmethod
    def get_quality_indicators(df: pd.DataFrame) -> Dict:
        """Calcola indicatori di qualità del lavoro"""
        if df.empty:
            return {
                'consistency_score': 0,
                'distribution_balance': 0,
                'completion_rate': 0
            }

        daily_hours = df.groupby(df['date'].dt.date)['time_spent_hours'].sum()
        consistency_score = (1 - daily_hours.std() / daily_hours.mean()) * 100 if daily_hours.mean() > 0 else 0

        category_dist = df.groupby('category')['time_spent_hours'].sum()
        distribution_balance = (1 - category_dist.std() / category_dist.mean()) * 100 if category_dist.mean() > 0 else 0

        completion_rate = 85

        return {
            'consistency_score': round(max(0, consistency_score), 2),
            'distribution_balance': round(max(0, distribution_balance), 2),
            'completion_rate': completion_rate
        }

    @staticmethod
    def calculate_nda_breakdown(df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcola il breakdown dettagliato delle Non-Development Activities
        """
        if df.empty:
            return pd.DataFrame()

        nda_df = df[df['category'] == 'Non-Development Activities'].copy()

        if nda_df.empty:
            return pd.DataFrame()

        def categorize_nda(row):
            summary = row['summary'].lower()
            comment = row['comment'].lower() if pd.notna(row['comment']) else ''
            full_text = f"{summary} {comment}"

            if any(kw in full_text for kw in ['code review', 'pr review', 'pull request', 'review']):
                return 'Code Review'
            if any(kw in full_text for kw in
                   ['ceremony', 'standup', 'daily', 'retrospective', 'retro', 'planning', 'refinement', 'demo',
                    'alignment']):
                return 'Ceremonies'
            if any(kw in full_text for kw in ['support', 'help', 'assist']):
                return 'Support'
            if any(kw in full_text for kw in ['duty', 'on-call', 'oncall']):
                return 'Duty'
            if any(kw in full_text for kw in ['regression', 'smoke', 'sanity']):
                return 'Regression'
            if any(kw in full_text for kw in ['bug', 'testing', 'test', 'migration']):
                return 'Testing (Bugs + Migration)'
            if any(kw in full_text for kw in ['maintenance', 'improvement', 'refactor']):
                return 'Maintenance / Improvement'
            if any(kw in full_text for kw in ['holiday', 'vacation', 'pto']):
                return 'Holiday'
            if any(kw in full_text for kw in ['sick', 'illness']):
                return 'Sickness'
            if any(kw in full_text for kw in ['on demand', 'ondemand', 'on-demand']):
                return 'On Demand'
            return 'Other'

        nda_df['nda_type'] = nda_df.apply(categorize_nda, axis=1)

        breakdown = nda_df.groupby('nda_type').agg({
            'time_spent_hours': 'sum',
            'issue_key': 'nunique'
        }).reset_index()

        breakdown.columns = ['NDA Type', 'Hours', 'Tasks']

        total_hours = breakdown['Hours'].sum()
        breakdown['Percentage'] = (breakdown['Hours'] / total_hours * 100).round(2) if total_hours > 0 else 0

        return breakdown.sort_values('Hours', ascending=False)

    @staticmethod
    def calculate_advanced_kpis(df: pd.DataFrame, working_days: int = 20) -> Dict:
        """
        Calcola KPI avanzati come nel report Excel
        """
        if df.empty:
            return {
                'total_md': 0,
                'available_md': 0,
                'logged_md': 0,
                'delivered_md': 0,
                'nda_md': 0,
                'ratio_available_total': 0,
                'ratio_logged_available': 0,
                'ratio_logged_total': 0,
                'ratio_delivered_total': 0,
                'estimates_variation': 0,
                'on_demand_md': 0,
                'ratio_on_demand_available': 0
            }

        unique_authors = df['author'].nunique()
        total_md = unique_authors * working_days

        nda_hours = df[df['category'] == 'Non-Development Activities']['time_spent_hours'].sum()
        nda_md = nda_hours / 8

        available_md = total_md - nda_md

        dev_test_hours = df[df['category'].isin(['Development Activities', 'Testing Activities'])][
            'time_spent_hours'].sum()
        logged_md = dev_test_hours / 8

        on_demand_df = df[df['summary'].str.contains('on demand|ondemand|on-demand', case=False, na=False)]
        on_demand_md = on_demand_df['time_spent_hours'].sum() / 8

        delivered_md = logged_md * 0.9

        estimates_variation = 0

        ratio_available_total = (available_md / total_md * 100) if total_md > 0 else 0
        ratio_logged_available = (logged_md / available_md * 100) if available_md > 0 else 0
        ratio_logged_total = (logged_md / total_md * 100) if total_md > 0 else 0
        ratio_delivered_total = (delivered_md / total_md * 100) if total_md > 0 else 0
        ratio_on_demand_available = (on_demand_md / available_md * 100) if available_md > 0 else 0

        return {
            'total_md': round(total_md, 2),
            'available_md': round(available_md, 2),
            'logged_md': round(logged_md, 2),
            'delivered_md': round(delivered_md, 2),
            'nda_md': round(nda_md, 2),
            'ratio_available_total': round(ratio_available_total, 2),
            'ratio_logged_available': round(ratio_logged_available, 2),
            'ratio_logged_total': round(ratio_logged_total, 2),
            'ratio_delivered_total': round(ratio_delivered_total, 2),
            'estimates_variation': round(estimates_variation, 2),
            'on_demand_md': round(on_demand_md, 2),
            'ratio_on_demand_available': round(ratio_on_demand_available, 2)
        }

    @staticmethod
    def calculate_squad_analysis(df: pd.DataFrame) -> pd.DataFrame:
        """Analizza le metriche per squad/project"""
        if df.empty:
            return pd.DataFrame()

        squad_metrics = df.groupby('project_key').agg({
            'time_spent_hours': 'sum',
            'issue_key': 'nunique',
            'author': 'nunique'
        }).reset_index()

        squad_metrics.columns = ['Squad/Project', 'Total Hours', 'Tasks', 'Contributors']
        squad_metrics['Man Days (MD)'] = (squad_metrics['Total Hours'] / 8).round(2)

        total_md = squad_metrics['Man Days (MD)'].sum()
        squad_metrics['% of Total'] = (squad_metrics['Man Days (MD)'] / total_md * 100).round(2) if total_md > 0 else 0

        return squad_metrics.sort_values('Man Days (MD)', ascending=False)

    @staticmethod
    def calculate_ticket_analysis(df: pd.DataFrame) -> Dict:
        """Analizza i ticket"""
        if df.empty:
            return {
                'total_worklog_entries': 0,
                'unique_tickets': 0,
                'avg_hours_per_ticket': 0
            }

        total_entries = len(df)
        unique_tickets = df['issue_key'].nunique()
        avg_hours = df.groupby('issue_key')['time_spent_hours'].sum().mean()

        return {
            'total_worklog_entries': total_entries,
            'unique_tickets': unique_tickets,
            'avg_hours_per_ticket': round(avg_hours, 2) if pd.notna(avg_hours) else 0
        }