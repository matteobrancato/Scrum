# 🎯 Scrum - Jira QA Team Analytics Dashboard v2.0

Dashboard avanzata per l'analisi delle attività del team QA con auto-discovery dei progetti e metriche complete basate sul report Excel.

## 🌟 Funzionalità Principali

### ✨ Auto-Discovery
- **Nessuna configurazione progetti necessaria** - Il sistema scarica automaticamente TUTTI i worklog dei team members
- **Discovery automatica progetti** - Trova automaticamente tutti i progetti su cui il team ha lavorato
- **Categorizzazione intelligente** - Usa keywords per categorizzare automaticamente le attività

### 📊 Metriche Complete

#### KPI Overview
- **Total Man Days (MD)** - Contributors × Giorni lavorativi
- **Available MD** - Tempo disponibile per dev (Total - NDA)
- **Logged MD** - Tempo effettivamente loggato per dev/testing
- **Delivered MD** - Tempo delivered basato su velocity

#### Ratios Avanzati (come Excel report)
- **A. Ratio Available/Total** - % tempo disponibile per dev
- **B. Ratio Logged/Available** - % tempo loggato su disponibile
- **C. Ratio Logged/Total** - % tempo loggato su totale
- **D. Ratio Delivered/Total** - % tempo delivered su totale
- **F. Ratio On Demand/Available** - % on demand su disponibile
- **DA:NDA Ratio** - Rapporto Development vs Non-Development

#### NDA Breakdown Dettagliato (11 categorie)
- Code Review
- Ceremonies (standup, retro, planning, demo)
- Support (Dev/BA/QA/SM)
- Duty (on-call, monitoring)
- Regression (smoke, sanity tests)
- Testing (Bugs + Migration)
- Maintenance / Improvement
- Holiday
- Sickness
- On Demand
- Other

#### Squad/Project Analysis
- Man Days per squad/progetto
- Hours, Tasks, Contributors per squad
- % of Total per squad

#### Core Metrics
- Activity Distribution (Development, Testing, Non-Development)
- Team Overview con confronto membri
- Daily Trends
- Quality Indicators

## 🚀 Quick Start

### 1. Setup
```bash