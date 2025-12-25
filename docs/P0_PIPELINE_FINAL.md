# SCHÉMA PIPELINE FINAL — P0 SIMPLIFICATION

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────┐
│         POST /api/v1/exercises/generate                     │
│                                                              │
│  Input: code_officiel, difficulty, offer, seed              │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ Détection pipeline              │
        │ (curriculum.pipeline)            │
        └─────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌───────────────┐
│ TEMPLATE      │                  │ SPEC          │
│ (Dynamique    │                  │ (Statique     │
│  uniquement)  │                  │  uniquement)  │
└───────────────┘                  └───────────────┘
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌───────────────┐
│ Cherche       │                  │ Cherche       │
│ DYNAMIC      │                  │ STATIC        │
│ uniquement   │                  │ uniquement    │
└───────────────┘                  └───────────────┘
        │                                   │
        ▼                                   ▼
    Erreur 422                          Erreur 422
    si échec                            si échec
```

## Pipeline AUTO (par défaut si pipeline non défini)

```
┌─────────────────────────────────────────────────────────────┐
│ Pipeline AUTO (DYNAMIC → STATIC fallback)                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ generate_exercise_with_fallback()│
        └─────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌───────────────┐
│ 1. Essaie     │                  │ 2. Fallback   │
│ DYNAMIC       │                  │ STATIC        │
│               │                  │               │
│ - Cherche     │                  │ - Cherche     │
│   is_dynamic  │                  │   is_dynamic  │
│   = true      │                  │   = false    │
│               │                  │               │
│ - Génère avec │                  │ - Retourne   │
│   Factory     │                  │   exercice    │
│               │                  │   figé        │
└───────────────┘                  └───────────────┘
        │                                   │
        ▼                                   ▼
    ✅ Succès                          ✅ Succès
    Log: dynamic_generated             Log: static_fallback_used
                          │
                          ▼
                    ❌ Échec
                    Erreur 422
```

## Pipeline MIXED (simplifié)

```
┌─────────────────────────────────────────────────────────────┐
│ Pipeline MIXED                                              │
│ (Utilise generate_exercise_with_fallback)                   │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────┐
        │ generate_exercise_with_fallback()│
        │ (même logique que AUTO)          │
        └─────────────────────────────────┘
```

## Logs de debug (dev only)

### Succès DYNAMIC
```
[P0] ✅ Exercice DYNAMIQUE généré: chapter=6E_GM07, id=1, generator=THALES_V1
event=dynamic_generated, outcome=success
```

### Fallback STATIC
```
[P0] ✅ Exercice STATIQUE (fallback): chapter=6E_GM07, id=2
event=static_fallback_used, outcome=success, fallback_reason=dynamic_unavailable
```

### Échec DYNAMIC (avant fallback)
```
[P0] Erreur génération DYNAMIC pour 6E_GM07: No dynamic exercises. Fallback STATIC.
event=dynamic_failed, outcome=fallback, reason=exception
```

## Types d'exercices (2 seulement)

### Type 1 : DYNAMIC
```json
{
  "is_dynamic": true,
  "generator_key": "THALES_V1",
  "enonce_template_html": "<p>Calculer {{a}} + {{b}}</p>",
  "solution_template_html": "<p>{{a}} + {{b}} = {{resultat}}</p>",
  "variables": {...}
}
```

### Type 2 : STATIC
```json
{
  "is_dynamic": false,
  "generator_key": null,
  "enonce_html": "<p>Calculer 5 + 3</p>",
  "solution_html": "<p>5 + 3 = 8</p>"
}
```

## Règles strictes

1. **DB = source unique** : Plus de chargement depuis Python
2. **2 types seulement** : DYNAMIC ou STATIC
3. **Fallback explicite** : DYNAMIC → STATIC (un seul fallback)
4. **Logs clairs** : `dynamic_generated` ou `static_fallback_used`




