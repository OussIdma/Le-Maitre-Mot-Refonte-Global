# Proposition Technique : Mode Premium Thématique

## 🎯 Objectif

Permettre aux élèves de recevoir des exercices mathématiques dans des **contextes thématiques personnalisés** (Naruto, Dragon Ball Z, football, Harry Potter, etc.) pour augmenter l'engagement et la motivation.

---

## 🏗️ Architecture Proposée

### 1. Extension du Système de Styles Existant

Le système actuel (`style_manager.py`) dispose déjà de 10 styles de formulation :
- concis, scolaire, académique, narratif, guide, défi, oral, étapes, inductif, qr

**Proposition** : Ajouter une dimension **"thème"** orthogonale aux styles.

```python
class Theme(Enum):
    """Thèmes narratifs pour mode Premium"""
    STANDARD = "standard"
    
    # Mangas / Animés
    NARUTO = "naruto"
    DRAGON_BALL = "dragon_ball"
    ONE_PIECE = "one_piece"
    
    # Sports
    FOOTBALL = "football"
    BASKETBALL = "basketball"
    
    # Fantastique
    HARRY_POTTER = "harry_potter"
    STAR_WARS = "star_wars"
    
    # Jeux vidéo
    MINECRAFT = "minecraft"
    FORTNITE = "fortnite"
```

---

### 2. Enrichissement des Gabarits

#### Structure actuelle d'un gabarit :
```json
{
  "chapitre": "Théorème de Pythagore",
  "type_exercice": "trouver_valeur",
  "gabarits": [
    {
      "style": "narratif",
      "templates": [
        "Sophie travaille sur un triangle rectangle..."
      ]
    }
  ]
}
```

#### Structure enrichie avec thèmes :
```json
{
  "chapitre": "Théorème de Pythagore",
  "type_exercice": "trouver_valeur",
  "gabarits": [
    {
      "style": "narratif",
      "theme": "standard",
      "templates": [
        "Sophie travaille sur un triangle rectangle..."
      ]
    },
    {
      "style": "narratif",
      "theme": "naruto",
      "templates": [
        "Naruto doit calculer la distance pour lancer son jutsu. Il voit un triangle rectangle formé par le chemin de Kakashi. {cote1} = {long1} m, {cote2} = {long2} m. Aide Naruto à trouver {coteACalculer} avant que l'ennemi attaque !"
      ]
    },
    {
      "style": "narratif",
      "theme": "football",
      "templates": [
        "Mbappé veut calculer la distance de tir parfaite. Sur le terrain, il forme un triangle rectangle avec le but et le défenseur. {cote1} = {long1} m, {cote2} = {long2} m. Quelle est la distance {coteACalculer} pour marquer ?"
      ]
    }
  ]
}
```

---

### 3. Modifications du Code

#### 3.1 Mise à jour de `style_manager.py`

**Ajout de la classe Theme** :
```python
class Theme(Enum):
    STANDARD = "standard"
    NARUTO = "naruto"
    DRAGON_BALL = "dragon_ball"
    FOOTBALL = "football"
    # ... etc

class StyleManager:
    def build_cache_key(
        self, 
        chapitre: str, 
        type_exercice: str, 
        difficulte: str, 
        style: StyleFormulation,
        theme: Theme = Theme.STANDARD  # NOUVEAU paramètre
    ) -> str:
        """Génère clé de cache incluant le thème"""
        return f"{chapitre}__{type_exercice}__{difficulte}__{style.value}__{theme.value}"
```

#### 3.2 Mise à jour de `gabarit_loader.py`

**Méthode de sélection avec thème** :
```python
def get_random_gabarit(
    self, 
    chapitre: str, 
    type_exercice: str, 
    style: StyleFormulation,
    theme: Theme = Theme.STANDARD  # NOUVEAU paramètre
) -> Optional[str]:
    """
    Sélectionne un gabarit en fonction du style ET du thème.
    
    Fallback : Si pas de gabarit pour le thème demandé, utilise STANDARD.
    """
    # Chercher d'abord avec le thème
    template = self._find_template(chapitre, type_exercice, style, theme)
    
    # Fallback vers thème standard si non trouvé
    if not template and theme != Theme.STANDARD:
        logger.info(f"Thème {theme.value} non trouvé, fallback vers standard")
        template = self._find_template(chapitre, type_exercice, style, Theme.STANDARD)
    
    return template
```

#### 3.3 Mise à jour de `math_text_service.py`

**Intégration du thème dans la génération** :
```python
def _try_generate_from_gabarit(
    self, 
    spec: MathExerciseSpec,
    theme: Theme = Theme.STANDARD  # NOUVEAU paramètre
) -> Optional[MathTextGeneration]:
    """Génère avec thème si disponible"""
    
    style = style_manager.get_random_style()
    
    # Charger gabarit avec thème
    template = gabarit_loader.get_random_gabarit(
        chapitre=spec.chapitre,
        type_exercice=pedagogical_type,
        style=style,
        theme=theme  # Passage du thème
    )
    
    # ... reste du code
```

---

### 4. API et Interface Utilisateur

#### 4.1 Extension du modèle de requête

**Ajout du paramètre `theme` à la requête** :
```python
class GenerateRequest(BaseModel):
    matiere: str
    niveau: str
    chapitre: str
    type_doc: str
    difficulte: str
    nb_exercices: int
    versions: List[str]
    theme: Optional[str] = "standard"  # NOUVEAU paramètre
```

#### 4.2 Exemple de requête utilisateur

```bash
POST /api/generate
{
  "matiere": "Mathématiques",
  "niveau": "4e",
  "chapitre": "Théorème de Pythagore",
  "type_doc": "exercices",
  "difficulte": "moyen",
  "nb_exercices": 10,
  "versions": ["A"],
  "theme": "naruto"  # 🎯 Mode Premium activé
}
```

---

### 5. Gestion des Droits d'Accès (Premium)

#### 5.1 Système de Permissions

```python
class PremiumFeatureManager:
    """Gère l'accès aux fonctionnalités Premium"""
    
    PREMIUM_THEMES = {
        Theme.NARUTO, Theme.DRAGON_BALL, Theme.ONE_PIECE,
        Theme.FOOTBALL, Theme.BASKETBALL,
        Theme.HARRY_POTTER, Theme.STAR_WARS,
        Theme.MINECRAFT, Theme.FORTNITE
    }
    
    def user_can_access_theme(self, user_id: str, theme: Theme) -> bool:
        """Vérifie si l'utilisateur a accès au thème demandé"""
        if theme == Theme.STANDARD:
            return True  # Toujours accessible
        
        if theme in self.PREMIUM_THEMES:
            return self.check_user_subscription(user_id, "premium")
        
        return False
```

#### 5.2 Vérification dans l'API

```python
@app.post("/api/generate")
async def generate_document(request: GenerateRequest):
    # Vérifier droits premium
    theme = Theme(request.theme)
    
    if not premium_manager.user_can_access_theme(request.guest_id, theme):
        raise HTTPException(
            status_code=403,
            detail=f"Thème '{theme.value}' réservé aux abonnés Premium"
        )
    
    # Génération avec thème
    # ...
```

---

### 6. Stratégie de Déploiement

#### Phase 1 : MVP (2-3 thèmes pilotes)
- **Naruto** (très populaire chez les jeunes)
- **Football** (universel)
- **Minecraft** (gaming populaire)

Créer **10 gabarits par thème** pour les chapitres prioritaires :
- Symétrie axiale/centrale
- Pythagore
- Proportionnalité

#### Phase 2 : Extension
- Ajouter 5 thèmes supplémentaires
- Étendre aux autres chapitres
- **20 gabarits par thème et par chapitre**

#### Phase 3 : Génération IA de Thèmes
- Utiliser l'IA pour générer automatiquement des variantes thématiques
- Créer un prompt spécifique : "Réécris cet énoncé dans le thème Naruto"
- Cacher les résultats pour réutilisation

---

### 7. Exemple de Gabarits Thématiques

#### Pythagore - Thème Naruto
```json
{
  "style": "narratif",
  "theme": "naruto",
  "templates": [
    "Naruto s'entraîne avec Kakashi. Ils forment un triangle rectangle sur le terrain. Kakashi est à {long1} m de Naruto, et Sasuke est à {long2} m de Kakashi. Quelle distance sépare Naruto de Sasuke ?",
    
    "Pour son prochain jutsu, Naruto doit calculer une distance. Le triangle formé par lui, Sakura et le parchemin est rectangle en Sakura. {cote1} = {long1} m, {cote2} = {long2} m. Trouve {coteACalculer} !",
    
    "Mission urgente ! Naruto doit rejoindre le village. Il utilise le théorème de Pythagore pour trouver le chemin le plus court. Triangle rectangle : {cote1} = {long1} m, {cote2} = {long2} m. Calcule {coteACalculer} avant que l'ennemi arrive !"
  ]
}
```

#### Proportionnalité - Thème Football
```json
{
  "style": "narratif",
  "theme": "football",
  "templates": [
    "En {val1} matchs, Mbappé marque {res1} buts. En {val2} matchs, il marque {res2} buts. S'il joue {val3} matchs, combien de buts marquera-t-il ?",
    
    "Le PSG achète {val1} ballons pour {res1} euros et {val2} maillots pour {res2} euros. Combien coûteront {val3} ballons ?",
    
    "Pendant l'entraînement, les joueurs font {res1} passes en {val1} minutes et {res2} passes en {val2} minutes. En {val3} minutes, combien de passes feront-ils ?"
  ]
}
```

---

### 8. Avantages du Système

✅ **Compatible avec l'architecture actuelle** : Simple extension, pas de refonte
✅ **Scalable** : Facile d'ajouter de nouveaux thèmes
✅ **Performant** : Utilise le même système de cache
✅ **Fallback automatique** : Si thème non disponible → standard
✅ **Monétisable** : Thèmes premium = source de revenu
✅ **Engagement accru** : Élèves plus motivés par contextes ludiques

---

### 9. Estimation de Développement

| Phase | Tâche | Durée estimée |
|-------|-------|---------------|
| **Phase 1** | Modifier architecture (style_manager, gabarit_loader) | 2h |
| **Phase 1** | Créer 3 thèmes × 10 gabarits × 3 chapitres = 90 gabarits | 4h |
| **Phase 1** | Intégrer vérification Premium dans API | 1h |
| **Phase 1** | Tests E2E | 1h |
| **Phase 2** | 5 thèmes supplémentaires × 20 gabarits × 5 chapitres | 10h |
| **Phase 3** | Génération automatique IA de variantes thématiques | 3h |

**Total Phase 1 (MVP)** : ~8h
**Total complet** : ~21h

---

### 10. Exemples de Prompts pour Génération IA (Phase 3)

Pour créer automatiquement des variantes thématiques :

```python
THEME_PROMPT_TEMPLATES = {
    Theme.NARUTO: """
    Réécris l'énoncé mathématique suivant dans l'univers de Naruto.
    Utilise les personnages (Naruto, Sasuke, Sakura, Kakashi) et le contexte ninja.
    Conserve TOUS les placeholders {entre accolades}.
    
    Énoncé original : {enonce_original}
    
    Énoncé Naruto :
    """,
    
    Theme.FOOTBALL: """
    Transforme cet énoncé mathématique en contexte football.
    Utilise des joueurs, terrains, buts, passes, matchs.
    Conserve TOUS les placeholders {entre accolades}.
    
    Énoncé original : {enonce_original}
    
    Énoncé Football :
    """
}
```

---

## 🎓 Conclusion

Le **Mode Premium Thématique** est une extension naturelle et performante du système actuel. Il réutilise toute l'architecture existante (gabarits, cache, styles) en ajoutant simplement une dimension "thème".

**Recommandation** : Commencer par un MVP avec 3 thèmes pour valider l'engagement utilisateur, puis étendre progressivement.
