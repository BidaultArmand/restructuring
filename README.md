# 🏢 E-Center - Système de Diagnostics Professionnels

Application de restructuration d'entreprise avec système RAG et agents spécialisés pour E-Center.

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Utilisation](#-utilisation)
- [Les 7 Agents Spécialisés](#-les-7-agents-spécialisés)
- [Structure du Projet](#-structure-du-projet)

## ✨ Fonctionnalités

### 1. Assistant Juridique RAG
- Chat interactif avec contexte documentaire
- Recherche sémantique dans les documents E-Center
- Réponses basées sur DeepSeek avec contexte enrichi

### 2. Diagnostics Professionnels (NOUVEAU)
- **7 agents spécialisés** couvrant tous les aspects de l'entreprise
- Génération de diagnostics complets et professionnels
- Routage intelligent des questions vers l'agent approprié
- Recherche web automatique pour certains diagnostics

### 3. Dashboard Financier
- Visualisation intelligente des données financières
- Graphiques interactifs (barres, camemberts, lignes)
- Analyse par IA des tableaux pertinents

## 🏗 Architecture

```
┌─────────────────────────────────────────────────┐
│           Interface Streamlit                    │
├─────────────────────────────────────────────────┤
│                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────┐│
│  │  Assistant   │  │ Diagnostics  │  │Dashboard││
│  │  Juridique   │  │Professionnels│  │Financier││
│  └──────┬───────┘  └──────┬───────┘  └────┬───┘│
│         │                  │                │    │
├─────────┼──────────────────┼────────────────┼───┤
│         │                  │                │    │
│    ┌────▼────┐      ┌──────▼──────┐    ┌───▼──┐│
│    │   RAG   │      │   Agents    │    │ Agent││
│    │  Query  │      │ Spécialisés │    │  LLM ││
│    └────┬────┘      └──────┬──────┘    └──────┘│
│         │                   │                    │
│    ┌────▼────────────────┐ │                    │
│    │  FAISS Vector DB    │ │                    │
│    │  (Embeddings)       │ │                    │
│    └─────────────────────┘ │                    │
│                             │                    │
│    ┌────────────────────┐  │                    │
│    │   Documents PDF    │◄─┘                    │
│    │   raw_data/        │                       │
│    └────────────────────┘                       │
│                                                  │
│    ┌────────────────────┐                       │
│    │   Web Search       │                       │
│    │  (DuckDuckGo)      │                       │
│    └────────────────────┘                       │
└──────────────────────────────────────────────────┘
```

## 🚀 Installation

### Prérequis
- Python 3.9+
- pip

### Étapes d'installation

1. **Cloner le repository**
```bash
git clone <repo-url>
cd restructuring
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

### 1. Configurer les clés API

Créer un fichier `.env` à la racine du projet :

```bash
cp .env.example .env
```

Éditer le fichier `.env` et ajouter vos clés API :

```env
# DeepSeek API Configuration (pour l'assistant RAG)
DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# OpenAI API Configuration (pour les diagnostics)
OPENAI_API_KEY=sk-your-openai-api-key
```

### 2. Configurer le mot de passe Streamlit

Créer un fichier `.streamlit/secrets.toml` :

```toml
password = "votre_mot_de_passe"
DEEPSEEK_API_KEY = "sk-your-deepseek-api-key"
```

### 3. Préparer les données

Les documents PDF doivent être dans le dossier `raw_data/`. Le système RAG utilisera automatiquement les embeddings pré-générés.

## 💻 Utilisation

### Lancer l'application

```bash
streamlit run app.py
```

L'application sera accessible sur `http://localhost:8501`

### Les 3 Pages de l'Application

#### 1. 🧠 Assistant Juridique
- Interface de chat interactive
- Pose des questions sur les documents E-Center
- Réponses contextuelles basées sur le RAG

#### 2. 📋 Diagnostics Professionnels

##### Onglet 1: Tous les diagnostics
- Génère les 7 diagnostics en une seule fois
- Affichage avec expanders pour chaque diagnostic
- Téléchargement du rapport complet en Markdown

##### Onglet 2: Diagnostic spécifique
- Sélectionne un domaine de diagnostic
- Génère uniquement ce diagnostic
- Téléchargement individuel

##### Onglet 3: Question ciblée
- Pose une question libre
- Routage automatique vers l'agent approprié
- Affichage de l'agent utilisé
- Téléchargement de la réponse

#### 3. 📊 Dashboard Financier
- Pose une question sur les données financières
- Visualisation intelligente des graphiques pertinents
- Types de graphiques: barres, camemberts, lignes

## 🤖 Les 7 Agents Spécialisés

### 1. 🌐 Agent Marché
- **Domaine**: Marché actuel
- **Recherche Web**: ✅ Activée
- **Analyse**:
  - Vue d'ensemble du marché
  - Tendances actuelles
  - Positionnement
  - Opportunités et menaces
  - Recommandations stratégiques

### 2. 🎁 Agent Produit
- **Domaine**: Produits et services
- **Recherche Web**: ❌
- **Analyse**:
  - Catalogue produits/services
  - Proposition de valeur
  - Performance des produits
  - Innovation
  - Points forts et faiblesses
  - Recommandations

### 3. ⚔️ Agent Concurrence
- **Domaine**: Environnement concurrentiel
- **Recherche Web**: ✅ Activée
- **Analyse**:
  - Cartographie des concurrents
  - Analyse comparative
  - Avantages compétitifs
  - Stratégies concurrentielles
  - Menaces et opportunités
  - Recommandations stratégiques

### 4. 📜 Agent Histoire
- **Domaine**: Historique de l'entreprise
- **Recherche Web**: ❌
- **Analyse**:
  - Chronologie complète
  - Phases de développement
  - Procédures judiciaires
  - Évolution de la gouvernance
  - Leçons apprises
  - Perspectives

### 5. ⚙️ Agent Process
- **Domaine**: Processus opérationnels
- **Recherche Web**: ❌
- **Analyse**:
  - Cartographie des processus
  - Organisation opérationnelle
  - Efficience opérationnelle
  - Gestion de la qualité
  - Systèmes d'information
  - Recommandations d'amélioration

### 6. 💰 Agent Chiffre
- **Domaine**: Analyse financière
- **Recherche Web**: ❌
- **Analyse**:
  - Analyse du CA
  - Analyse de la rentabilité
  - Structure financière
  - Flux de trésorerie
  - Risques financiers
  - Recommandations financières

### 7. ⚖️ Agent Juridique
- **Domaine**: Aspects juridiques
- **Recherche Web**: ✅ Activée
- **Analyse**:
  - Statut juridique
  - Procédures collectives
  - Obligations légales
  - Contrats et engagements
  - Risques juridiques
  - Recommandations juridiques

## 📁 Structure du Projet

```
restructuring/
├── app.py                      # Application Streamlit principale
├── diagnostic_agents.py        # Système d'agents spécialisés (NOUVEAU)
├── rag_query.py               # Logique RAG et requêtes
├── chunking.py                # Découpage des documents
├── pdf_extract.py             # Extraction de texte PDF
├── llm_structure.py           # Structures LLM
├── requirements.txt           # Dépendances Python
├── .env                       # Configuration (à créer)
├── .env.example               # Exemple de configuration
│
├── raw_data/                  # Documents PDF sources
│   ├── E-CENTER - Comptes annuels 2024.pdf
│   ├── E-CENTER - Jugement d'ouverture.pdf
│   ├── Rapport E-center sauvegarde.pdf
│   └── ...
│
├── data/                      # Données traitées
│   ├── texts/                 # Textes extraits
│   └── all_tables.json        # Tableaux extraits
│
├── index_debug.faiss          # Index FAISS (embeddings)
├── chunks_debug.json          # Chunks de documents
│
└── .streamlit/                # Configuration Streamlit
    ├── config.toml
    └── secrets.toml           # Secrets (à créer)
```

## 🎯 Exemples d'Utilisation

### Générer tous les diagnostics

1. Aller sur la page "📋 Diagnostics professionnels"
2. Onglet "📊 Tous les diagnostics"
3. Cliquer sur "🚀 Générer tous les diagnostics"
4. Attendre quelques minutes (7 diagnostics à générer)
5. Télécharger le rapport complet ou consulter par diagnostic

### Poser une question ciblée

**Exemples de questions**:
- "Quelle est la situation financière actuelle de E-Center ?" → Agent Chiffre
- "Qui sont les principaux concurrents ?" → Agent Concurrence
- "Quelle est l'histoire de l'entreprise ?" → Agent Histoire
- "Quels sont les produits proposés ?" → Agent Produit
- "Quelle est la situation juridique ?" → Agent Juridique
- "Quels sont les processus clés ?" → Agent Process
- "Quel est le marché de E-Center ?" → Agent Marché

Le système routera automatiquement vers l'agent approprié !

## 🔧 Dépannage

### Erreur: "OPENAI_API_KEY non définie"
- Vérifier que le fichier `.env` existe
- Vérifier que `OPENAI_API_KEY` est bien défini dans `.env`

### Erreur: "Index FAISS introuvable"
- Vérifier que `index_debug.faiss` existe à la racine
- Relancer le processus de génération d'embeddings si nécessaire

### Erreur lors de la recherche web
- Vérifier la connexion internet
- DuckDuckGo peut limiter les requêtes, attendre quelques minutes

## 🚧 Développement Futur

- [ ] Export PDF des diagnostics
- [ ] Historique des diagnostics générés
- [ ] Comparaison temporelle des diagnostics
- [ ] Agents supplémentaires (RH, Marketing, etc.)
- [ ] Intégration d'autres sources de données
- [ ] API REST pour les diagnostics

## 📝 Licence

Projet privé - Mission Restructuring X-HEC

## 👥 Contact

Pour toute question ou support, contactez l'équipe de restructuring.
