# HyStatsio Bot - Advanced Market Analysis Platform

Un bot Telegram avancé pour l'analyse des marchés sur Hyperliquid, avec une architecture modulaire et des fonctionnalités d'analyse sophistiquées.

## 🏗️ Architecture Modulaire

Le bot est structuré en modules spécialisés pour chaque type d'analyse :

### 📊 Funding Rate Dashboard (`funding.py`)
- **Fonctionnalités :**
  - Extraction des données de financement
  - Calcul des meilleurs taux sur 24h
  - Recherche d'actifs spécifiques
  - Gestion des alertes (changement positif/négatif)
- **Méthodes principales :**
  - `get_top_funding_rates()` - Top 5 des taux de financement
  - `find_asset()` - Recherche d'un actif spécifique
  - `set_alert()` - Configuration d'alertes
  - `check_alerts()` - Vérification des alertes déclenchées

### 💥 Scanner de Liquidations (`liquidations.py`)
- **Fonctionnalités :**
  - Détection des liquidations importantes récentes
  - Filtrage par taille
  - Détection de cascades de liquidations
- **Méthodes principales :**
  - `get_recent_liquidations()` - Liquidations récentes
  - `analyze_liquidation_cascade()` - Analyse des cascades
  - `filter_liquidations_by_size()` - Filtrage par taille

### 💰 Analyseur d'Open Interest (`open_interest.py`)
- **Fonctionnalités :**
  - Suivi de l'évolution des OI
  - Détection des hausses/baisses brusques
  - Génération d'alertes automatiques
- **Méthodes principales :**
  - `analyze_oi_changes()` - Analyse des changements OI
  - `detect_oi_spikes()` - Détection des spikes
  - `get_oi_trends()` - Tendances OI par actif

### 📈 Spike de Volume (`volume_spike.py`)
- **Fonctionnalités :**
  - Analyse de l'évolution du volume historique
  - Détection de changements soudains
  - Alertes automatiques pour gros volumes
- **Méthodes principales :**
  - `analyze_volume_spikes()` - Analyse des spikes de volume
  - `detect_volume_patterns()` - Détection de patterns
  - `get_asset_volume_history()` - Historique par actif

### 📊 Divergence Volume/Prix (`volume_price_divergence.py`)
- **Fonctionnalités :**
  - Détection de volume en hausse sans mouvement prix
  - Détection inverse (prix sans volume)
  - Génération d'alertes pertinentes
- **Méthodes principales :**
  - `detect_volume_price_divergence()` - Détection des divergences
  - `analyze_divergence_patterns()` - Analyse des patterns
  - `get_asset_divergence_history()` - Historique des divergences

## 🎯 Orchestrateur (`analyzers.py`)

L'orchestrateur coordonne tous les modules d'analyse :
- `AnalyzerOrchestrator` - Classe principale
- Gestion centralisée des callbacks
- Interface unifiée pour tous les modules
- Vérification centralisée des alertes

## 🚀 Installation et Configuration

### Prérequis
- Python 3.8+
- Token Telegram Bot
- Accès à l'API Hyperliquid

### Installation
```bash
# Cloner le repository
git clone <repository-url>
cd HyStatsio_bot

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env
# Éditer .env avec votre token Telegram
```

### Configuration
Créer un fichier `.env` :
```env
TELEGRAM_TOKEN=your_telegram_bot_token_here
```

## 🎮 Utilisation

### Commandes principales
- `/start` - Menu principal avec boutons
- `/help` - Aide détaillée
- `/funding` - Analyse des taux de financement
- `/liquidations` - Scanner de liquidations
- `/oi` - Analyse d'Open Interest
- `/volume` - Analyse de volume
- `/divergence` - Détection de divergences

### Fonctionnalités interactives
- **Boutons inline** pour navigation rapide
- **Recherche d'actifs** spécifiques
- **Configuration d'alertes** personnalisées
- **Messages de chargement** pendant l'analyse

## 🔧 Structure des Fichiers

```
HyStatsio_bot/
├── main.py                      # Point d'entrée principal
├── commands.py                  # Gestionnaire de commandes
├── analyzers.py                 # Orchestrateur des modules
├── hyperliquid_api.py           # API Hyperliquid
├── funding.py                   # Module taux de financement
├── liquidations.py              # Module liquidations
├── open_interest.py             # Module Open Interest
├── volume_spike.py              # Module spikes de volume
├── volume_price_divergence.py   # Module divergences
├── requirements.txt             # Dépendances Python
├── .env                         # Variables d'environnement
└── README.md                    # Documentation
```

## 📊 Fonctionnalités d'Analyse

### Pandas Integration
Tous les modules utilisent pandas pour :
- Analyse efficace des données
- Calculs statistiques avancés
- Filtrage et tri des résultats
- Détection de patterns

### Système d'Alertes
- Alertes personnalisées par utilisateur
- Vérification automatique des seuils
- Notifications en temps réel
- Gestion des alertes multiples

### Interface Utilisateur
- Messages formatés avec emojis
- Claviers inline pour navigation
- Messages de chargement
- Gestion d'erreurs robuste

## 🔄 Workflow d'Analyse

1. **Récupération des données** via l'API Hyperliquid
2. **Traitement avec pandas** pour analyse statistique
3. **Détection de patterns** et anomalies
4. **Formatage des résultats** pour affichage
5. **Gestion des alertes** si seuils dépassés

## 🚀 Démarrage

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer le bot
python main.py
```

## 📈 Évolutions Futures

- [ ] Intégration de données historiques complètes
- [ ] Analyse technique avancée
- [ ] Notifications push personnalisées
- [ ] Interface web d'administration
- [ ] Support multi-exchanges
- [ ] Backtesting des stratégies

## 🤝 Contribution

Les contributions sont les bienvenues ! Veuillez :
1. Fork le projet
2. Créer une branche feature
3. Commiter vos changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails. 