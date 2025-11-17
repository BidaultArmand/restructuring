"""
Système d'agents spécialisés pour la génération de diagnostics professionnels sur E-Center.
Chaque agent est expert dans un domaine spécifique et peut utiliser différentes sources d'information.
"""

import os
import json
import time
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv
from openai import OpenAI
from duckduckgo_search import DDGS
from rag_query import build_context, retrieve, get_tabular_info
import tiktoken

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("⚠️ OPENAI_API_KEY non définie dans .env")

client = OpenAI(api_key=OPENAI_API_KEY)
MODEL = "gpt-4o-mini"  # Modèle OpenAI optimal pour le rapport qualité/coût
MAX_CONTEXT_TOKENS = 100000  # Limite de sécurité pour le contexte (laisse de la marge pour la réponse)

# Initialiser l'encodeur de tokens
try:
    encoding = tiktoken.encoding_for_model(MODEL)
except KeyError:
    encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    """Compte le nombre de tokens dans un texte."""
    return len(encoding.encode(text))


def truncate_context(context: str, max_tokens: int = MAX_CONTEXT_TOKENS) -> str:
    """Tronque le contexte pour ne pas dépasser max_tokens."""
    tokens = encoding.encode(context)
    if len(tokens) <= max_tokens:
        return context

    # Tronquer et ajouter un message
    truncated_tokens = tokens[:max_tokens]
    truncated_text = encoding.decode(truncated_tokens)
    return truncated_text + "\n\n[... Contexte tronqué pour respecter la limite de tokens ...]"


class BaseAgent:
    """Classe de base pour tous les agents spécialisés."""

    def __init__(self, domain: str, description: str, use_web_search: bool = False):
        self.domain = domain
        self.description = description
        self.use_web_search = use_web_search

    def get_rag_context(self, query: str) -> str:
        """Récupère le contexte depuis le RAG."""
        return build_context(query)

    def web_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """Effectue une recherche web avec DuckDuckGo."""
        if not self.use_web_search:
            return []

        try:
            # Délai pour éviter le rate limiting
            time.sleep(2)

            ddgs = DDGS()
            results = []
            search_results = ddgs.text(query, max_results=max_results)

            for r in search_results:
                results.append({
                    "title": r.get("title", ""),
                    "body": r.get("body", ""),
                    "link": r.get("href", "")
                })

            print(f"✅ Recherche web effectuée: {len(results)} résultats trouvés")
            return results

        except Exception as e:
            print(f"⚠️ Recherche web échouée (ignorée): {str(e)[:100]}")
            # Ne pas bloquer si la recherche web échoue
            return []

    def call_openai(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        """Appelle l'API OpenAI avec gestion d'erreurs."""
        try:
            # Compter les tokens du prompt complet
            total_prompt = system_prompt + user_prompt
            prompt_tokens = count_tokens(total_prompt)
            print(f"📝 Prompt total: {prompt_tokens:,} tokens")

            if prompt_tokens > 120000:  # Limite de sécurité
                raise ValueError(f"Le prompt ({prompt_tokens:,} tokens) dépasse la limite de sécurité (120,000 tokens)")

            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
            )

            result = response.choices[0].message.content
            result_tokens = count_tokens(result)
            print(f"✅ Réponse générée: {result_tokens:,} tokens")

            return result

        except Exception as e:
            error_msg = str(e)
            if "context_length_exceeded" in error_msg:
                return f"""**⚠️ Erreur: Contexte trop long**

Le contexte documentaire est trop volumineux pour être traité en une seule fois.

**Solutions:**
1. Posez une question plus spécifique pour réduire le contexte
2. Utilisez l'assistant juridique pour des questions ciblées
3. Contactez l'administrateur pour ajuster les paramètres

**Détails techniques:** {error_msg[:200]}..."""
            else:
                return f"""**⚠️ Erreur lors de la génération du diagnostic**

Une erreur s'est produite lors de la communication avec l'API OpenAI.

**Détails:** {error_msg[:300]}

Veuillez réessayer ou contactez l'administrateur."""

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        """Génère un diagnostic basé sur le contexte."""
        raise NotImplementedError("Chaque agent doit implémenter sa propre méthode de diagnostic")

    def run(self, custom_query: Optional[str] = None) -> str:
        """Exécute l'agent pour générer un diagnostic."""
        # Construction du contexte RAG
        query = custom_query or f"Informations sur {self.domain} de E-Center"
        print(f"🔍 Récupération du contexte RAG pour: {self.domain}")
        rag_context = self.get_rag_context(query)

        # Compter les tokens du contexte RAG
        rag_tokens = count_tokens(rag_context)
        print(f"📊 Contexte RAG: {rag_tokens:,} tokens")

        # Tronquer si nécessaire
        if rag_tokens > MAX_CONTEXT_TOKENS:
            print(f"⚠️ Contexte trop long, troncature à {MAX_CONTEXT_TOKENS:,} tokens")
            rag_context = truncate_context(rag_context, MAX_CONTEXT_TOKENS)
            rag_tokens = count_tokens(rag_context)
            print(f"✂️ Contexte tronqué: {rag_tokens:,} tokens")

        # Recherche web si activée
        web_context = ""
        if self.use_web_search:
            print(f"🌐 Recherche web pour: {self.domain}")
            web_results = self.web_search(f"E-Center {self.domain} France")
            if web_results:
                web_context = "\n\n=== INFORMATIONS WEB (sources externes) ===\n"
                for i, result in enumerate(web_results, 1):
                    web_context += f"\n{i}. {result['title']}\n{result['body'][:500]}...\n"
                web_tokens = count_tokens(web_context)
                print(f"🌐 Contexte web: {web_tokens:,} tokens")

        # Génération du diagnostic
        print(f"🤖 Génération du diagnostic {self.domain}...")
        return self.generate_diagnostic(rag_context, web_context)


class MarcheAgent(BaseAgent):
    """Agent spécialisé dans l'analyse du marché actuel."""

    def __init__(self):
        super().__init__(
            domain="Marché actuel",
            description="Analyse le marché actuel, les tendances, la taille du marché et les opportunités",
            use_web_search=True
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un analyste de marché expert en restructuration d'entreprise."

        user_prompt = f"""Génère un diagnostic professionnel et détaillé sur le marché actuel de E-Center.

CONTEXTE INTERNE (Documents E-Center):
{context}

{web_context}

STRUCTURE DU DIAGNOSTIC:
1. **Vue d'ensemble du marché**
   - Secteur d'activité principal
   - Taille et évolution du marché

2. **Tendances du marché**
   - Tendances actuelles
   - Évolutions réglementaires ou technologiques

3. **Positionnement sur le marché**
   - Part de marché estimée
   - Segments de clientèle ciblés

4. **Opportunités et menaces**
   - Opportunités de croissance identifiées
   - Risques et menaces du marché

5. **Recommandations stratégiques**
   - Actions prioritaires pour capitaliser sur les opportunités
   - Mesures de mitigation des risques

Fournis une analyse approfondie, factuelle et professionnelle. Utilise des données chiffrées quand disponibles."""

        return self.call_openai(system_prompt, user_prompt)


class ProduitAgent(BaseAgent):
    """Agent spécialisé dans l'analyse des produits/services."""

    def __init__(self):
        super().__init__(
            domain="Produit",
            description="Analyse les produits et services, leur valeur ajoutée et leur performance",
            use_web_search=False
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un expert en stratégie produit et innovation."

        user_prompt = f"""Génère un diagnostic professionnel sur les produits et services de E-Center.

CONTEXTE (Documents E-Center):
{context}

STRUCTURE DU DIAGNOSTIC:
1. **Catalogue de produits/services**
   - Liste des principaux produits/services offerts
   - Caractéristiques distinctives

2. **Proposition de valeur**
   - Valeur ajoutée pour les clients
   - Différenciation par rapport au marché

3. **Performance des produits**
   - Produits les plus rentables (si données disponibles)
   - Produits en difficulté

4. **Innovation et développement**
   - Nouveaux produits ou évolutions récentes
   - Pipeline d'innovation

5. **Points forts et faiblesses**
   - Atouts du portefeuille produits
   - Lacunes ou opportunités d'amélioration

6. **Recommandations**
   - Axes d'optimisation du portefeuille
   - Investissements prioritaires

Sois précis, factuel et professionnel dans ton analyse."""

        return self.call_openai(system_prompt, user_prompt)


class ConcurrenceAgent(BaseAgent):
    """Agent spécialisé dans l'analyse concurrentielle."""

    def __init__(self):
        super().__init__(
            domain="Concurrence",
            description="Analyse les concurrents, leur positionnement et les avantages compétitifs",
            use_web_search=True
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un expert en stratégie concurrentielle et intelligence économique."

        user_prompt = f"""Tu es un analyste concurrentiel expert. Génère un diagnostic professionnel sur l'environnement concurrentiel de E-Center.

CONTEXTE INTERNE (Documents E-Center):
{context}

{web_context}

STRUCTURE DU DIAGNOSTIC:
1. **Cartographie des concurrents**
   - Concurrents directs identifiés
   - Concurrents indirects et substituts

2. **Analyse comparative**
   - Forces et faiblesses relatives de E-Center
   - Positionnement prix/qualité

3. **Avantages compétitifs**
   - Différenciateurs clés de E-Center
   - Barrières à l'entrée du secteur

4. **Stratégies concurrentielles observées**
   - Tactiques des principaux concurrents
   - Évolutions récentes du paysage concurrentiel

5. **Menaces et opportunités**
   - Risques concurrentiels majeurs
   - Opportunités de différenciation

6. **Recommandations stratégiques**
   - Actions pour renforcer la position concurrentielle
   - Domaines d'investissement prioritaires

Fournis une analyse détaillée, objective et professionnelle."""

        return self.call_openai(system_prompt, user_prompt)


class HistoireAgent(BaseAgent):
    """Agent spécialisé dans l'analyse historique de l'entreprise."""

    def __init__(self):
        super().__init__(
            domain="Histoire",
            description="Retrace l'historique de l'entreprise, ses événements clés et son évolution",
            use_web_search=False
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un expert en analyse historique d'entreprise et restructuration."

        user_prompt = f"""Tu es un analyste d'entreprise expert. Génère un diagnostic historique professionnel de E-Center.

CONTEXTE (Documents E-Center):
{context}

STRUCTURE DU DIAGNOSTIC:
1. **Chronologie de l'entreprise**
   - Date de création et fondateurs
   - Événements majeurs et jalons
   - Évolution de l'activité

2. **Phases de développement**
   - Périodes de croissance
   - Périodes de difficultés
   - Tournants stratégiques

3. **Procédures judiciaires**
   - Historique des procédures (sauvegarde, redressement, etc.)
   - Contexte et causes
   - Résolutions et plans mis en œuvre

4. **Évolution de la gouvernance**
   - Changements de direction
   - Modifications de structure

5. **Leçons apprises**
   - Facteurs de succès passés
   - Erreurs à éviter

6. **Perspectives**
   - Impact de l'histoire sur la situation actuelle
   - Éléments historiques à valoriser pour l'avenir

Construis une analyse chronologique détaillée et professionnelle."""

        return self.call_openai(system_prompt, user_prompt)


class ProcessAgent(BaseAgent):
    """Agent spécialisé dans l'analyse des processus opérationnels."""

    def __init__(self):
        super().__init__(
            domain="Process",
            description="Analyse les processus opérationnels, l'organisation et l'efficience",
            use_web_search=False
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un expert en excellence opérationnelle et optimisation de processus."

        user_prompt = f"""Tu es un expert en excellence opérationnelle. Génère un diagnostic professionnel sur les processus de E-Center.

CONTEXTE (Documents E-Center):
{context}

STRUCTURE DU DIAGNOSTIC:
1. **Cartographie des processus**
   - Processus clés identifiés
   - Chaîne de valeur principale

2. **Organisation opérationnelle**
   - Structure organisationnelle
   - Ressources humaines et compétences

3. **Efficience opérationnelle**
   - Points forts du système opérationnel
   - Goulots d'étranglement identifiés
   - Indicateurs de performance (si disponibles)

4. **Gestion de la qualité**
   - Systèmes de contrôle qualité
   - Certifications ou normes appliquées

5. **Systèmes d'information**
   - Outils et technologies utilisés
   - Niveau de digitalisation

6. **Recommandations d'amélioration**
   - Optimisations prioritaires
   - Investissements en processus recommandés
   - Quick wins identifiés

Fournis une analyse opérationnelle détaillée et professionnelle."""

        return self.call_openai(system_prompt, user_prompt)


class ChiffreAgent(BaseAgent):
    """Agent spécialisé dans l'analyse financière."""

    def __init__(self):
        super().__init__(
            domain="Chiffre",
            description="Analyse les données financières, la rentabilité et la santé financière",
            use_web_search=False
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un expert en analyse financière et restructuration d'entreprise."

        user_prompt = f"""Tu es un analyste financier expert. Génère un diagnostic financier professionnel de E-Center.

CONTEXTE (Documents E-Center incluant comptes annuels et données financières):
{context}

STRUCTURE DU DIAGNOSTIC:
1. **Analyse du chiffre d'affaires**
   - Évolution du CA sur plusieurs exercices
   - Répartition par activité/produit si disponible
   - Saisonnalité éventuelle

2. **Analyse de la rentabilité**
   - Résultat d'exploitation
   - Résultat net
   - Marges (brute, opérationnelle, nette)
   - Évolution de la rentabilité

3. **Structure financière**
   - Actif (immobilisations, BFR, trésorerie)
   - Passif (capitaux propres, dettes)
   - Ratios de solvabilité

4. **Flux de trésorerie**
   - Capacité d'autofinancement
   - Flux de trésorerie opérationnels
   - Situation de trésorerie

5. **Analyse des risques financiers**
   - Niveau d'endettement
   - Dépendance aux créanciers
   - Risques de liquidité

6. **Recommandations financières**
   - Actions pour améliorer la rentabilité
   - Optimisation de la structure financière
   - Mesures de sécurisation de la trésorerie

Utilise TOUS les chiffres disponibles dans le contexte. Présente des tableaux si pertinent. Sois précis et professionnel."""

        return self.call_openai(system_prompt, user_prompt)


class JuridiqueAgent(BaseAgent):
    """Agent spécialisé dans l'analyse juridique."""

    def __init__(self):
        super().__init__(
            domain="Juridique",
            description="Analyse les aspects juridiques, réglementaires et les procédures en cours",
            use_web_search=True
        )

    def generate_diagnostic(self, context: str, web_context: str = "") -> str:
        system_prompt = "Tu es un expert en droit des entreprises en difficulté et restructuration."

        user_prompt = f"""Tu es un juriste expert en droit des entreprises en difficulté. Génère un diagnostic juridique professionnel de E-Center.

CONTEXTE INTERNE (Documents juridiques E-Center):
{context}

{web_context}

STRUCTURE DU DIAGNOSTIC:
1. **Statut juridique**
   - Forme juridique de l'entreprise
   - Capital social et actionnariat
   - Siège social et établissements

2. **Procédures collectives**
   - Historique des procédures (sauvegarde, redressement, etc.)
   - Détails des jugements
   - Plans de sauvegarde ou de continuation
   - État d'avancement actuel

3. **Obligations légales et réglementaires**
   - Conformité réglementaire
   - Obligations déclaratives
   - Certifications requises

4. **Contrats et engagements**
   - Principaux contrats en cours
   - Engagements vis-à-vis des créanciers
   - Garanties données

5. **Risques juridiques**
   - Litiges en cours ou potentiels
   - Non-conformités identifiées
   - Risques réglementaires

6. **Recommandations juridiques**
   - Actions de mise en conformité
   - Sécurisation juridique prioritaire
   - Optimisation de la structure juridique

Fournis une analyse juridique détaillée, rigoureuse et professionnelle."""

        return self.call_openai(system_prompt, user_prompt)


class DiagnosticRouter:
    """Routeur intelligent pour diriger les questions vers le bon agent."""

    def __init__(self):
        self.agents = {
            "marche": MarcheAgent(),
            "produit": ProduitAgent(),
            "concurrence": ConcurrenceAgent(),
            "histoire": HistoireAgent(),
            "process": ProcessAgent(),
            "chiffre": ChiffreAgent(),
            "juridique": JuridiqueAgent()
        }

        self.keywords = {
            "marche": ["marché", "secteur", "industrie", "tendance", "opportunité", "menace", "croissance"],
            "produit": ["produit", "service", "offre", "catalogue", "innovation", "valeur"],
            "concurrence": ["concurrent", "concurrence", "compétitif", "position", "différenciation"],
            "histoire": ["histoire", "historique", "création", "fondation", "évolution", "chronologie"],
            "process": ["processus", "opération", "organisation", "efficacité", "production", "workflow"],
            "chiffre": ["chiffre", "financier", "ca", "résultat", "rentabilité", "trésorerie", "dette", "bilan"],
            "juridique": ["juridique", "légal", "procédure", "jugement", "sauvegarde", "redressement", "contrat"]
        }

    def identify_domain(self, query: str) -> str:
        """Identifie le domaine de la question basé sur les mots-clés."""
        query_lower = query.lower()

        # Compteur de correspondances pour chaque domaine
        scores = {domain: 0 for domain in self.agents.keys()}

        for domain, keywords in self.keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    scores[domain] += 1

        # Retourne le domaine avec le meilleur score
        best_domain = max(scores.items(), key=lambda x: x[1])

        if best_domain[1] > 0:
            return best_domain[0]
        else:
            # Par défaut, utiliser l'agent général (marché)
            return "marche"

    def route_query(self, query: str) -> Tuple[str, str]:
        """Route une question vers l'agent approprié et retourne le diagnostic."""
        domain = self.identify_domain(query)
        agent = self.agents[domain]

        print(f"🎯 Question routée vers l'agent: {agent.domain}")
        response = agent.run(custom_query=query)

        return agent.domain, response

    def generate_all_diagnostics(self) -> Dict[str, str]:
        """Génère tous les diagnostics pour tous les domaines."""
        diagnostics = {}

        for domain, agent in self.agents.items():
            print(f"\n🔄 Génération du diagnostic: {agent.domain}")
            diagnostics[domain] = agent.run()

        return diagnostics


# === FONCTIONS UTILITAIRES ===

def generate_full_report() -> Dict[str, str]:
    """Génère un rapport complet avec tous les diagnostics."""
    router = DiagnosticRouter()
    return router.generate_all_diagnostics()


def answer_question(query: str) -> Tuple[str, str]:
    """Répond à une question en utilisant l'agent spécialisé approprié."""
    router = DiagnosticRouter()
    return router.route_query(query)


# === TEST ===
if __name__ == "__main__":
    # Test du routage
    test_queries = [
        "Quel est le marché de E-Center ?",
        "Quels sont les produits proposés ?",
        "Qui sont les concurrents ?",
        "Quelle est l'histoire de l'entreprise ?",
        "Comment sont organisés les processus ?",
        "Quelle est la situation financière ?",
        "Quelle est la situation juridique ?"
    ]

    router = DiagnosticRouter()

    print("=== TEST DU ROUTEUR ===\n")
    for query in test_queries:
        domain = router.identify_domain(query)
        print(f"Question: {query}")
        print(f"→ Routé vers: {domain}\n")
