"""
Migration 006 : Créer plusieurs exercices dynamiques pour SIMPLIFICATION_FRACTIONS_V2
======================================================================================

Objectif :
- Créer 2-3 exercices dynamiques pour le chapitre 6e_AA_TEST avec difficulté "difficile"
- Chaque exercice avec 3 template_variants A/B/C (Direct/Guidé/Diagnostic)
- Fixer variant_id dans variables pour sélection déterministe

Structure :
- Exercice 1 : Fractions difficiles (PGCD complexes)
- Exercice 2 : Fractions difficiles avec dénominateurs élevés
- Exercice 3 : Fractions difficiles avec PGCD multiples

Chaque exercice :
- generator_key: SIMPLIFICATION_FRACTIONS_V2
- difficulty: difficile
- offer: pro (premium)
- template_variants: 3 variants A/B/C avec variant_id explicite
- variables: variant_id fixé selon le variant (A, B, ou C)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

# Templates depuis simplification_fractions_v2.py
ENONCE_TEMPLATE_A = "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>"
SOLUTION_TEMPLATE_A = """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""

ENONCE_TEMPLATE_B = """<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>
{{hint_display}}"""
SOLUTION_TEMPLATE_B = """<ol>
  <li><strong>Méthode :</strong> {{method_explanation}}</li>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>"""

ENONCE_TEMPLATE_C = """<p><strong>Analyse cette simplification :</strong></p>
<p>Fraction initiale : <strong>{{fraction}}</strong></p>
<p>Simplification proposée : <strong>{{wrong_simplification}}</strong></p>
<p><em>Cette simplification est-elle correcte ?</em></p>"""
SOLUTION_TEMPLATE_C = """<ol>
  <li><strong>Vérification :</strong> {{check_equivalence_str}}</li>
  <li><strong>Conclusion :</strong> {{diagnostic_explanation}}</li>
  <li><strong>Simplification correcte :</strong> {{fraction_reduite}}</li>
</ol>"""


async def create_exercises():
    """Crée plusieurs exercices dynamiques pour SIMPLIFICATION_FRACTIONS_V2."""
    
    # Connexion MongoDB
    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db_name = os.getenv("DB_NAME", "le_maitre_mot_db")
    db = client[db_name]
    collection = db.admin_exercises
    
    chapter_code = "6E_AA_TEST"
    generator_key = "SIMPLIFICATION_FRACTIONS_V2"
    
    # Vérifier si des exercices existent déjà
    existing = await collection.count_documents({
        "chapter_code": chapter_code,
        "generator_key": generator_key,
        "difficulty": "difficile"
    })
    
    if existing > 0:
        print(f"⚠️  {existing} exercice(s) existant(s) pour {chapter_code} / {generator_key} / difficile")
        print("   Migration non exécutée pour éviter les doublons.")
        print("   Supprimez les exercices existants manuellement si nécessaire.")
        return
    
    exercises_to_create = [
        {
            "id": "simplif_fractions_v2_difficile_1",
            "chapter_code": chapter_code,
            "generator_key": generator_key,
            "is_dynamic": True,
            "difficulty": "difficile",
            "offer": "pro",
            "family": "SIMPLIFICATION_FRACTIONS",
            "exercise_type": "FRACTIONS",
            "needs_svg": True,
            "variables": {
                "variant_id": "A",  # Direct
                "pedagogy_mode": "standard",
                "hint_level": 0,
                "include_feedback": False,
                "difficulty": "difficile",
                "max_denominator": 40,
                "force_reducible": True,
                "allow_negative": False,
                "allow_improper": False,
                "show_svg": True,
                "representation": "number_line"
            },
            "template_variants": [
                {
                    "id": "A",
                    "variant_id": "A",
                    "label": "Direct",
                    "enonce_template_html": ENONCE_TEMPLATE_A,
                    "solution_template_html": SOLUTION_TEMPLATE_A,
                    "weight": 1
                },
                {
                    "id": "B",
                    "variant_id": "B",
                    "label": "Guidé",
                    "enonce_template_html": ENONCE_TEMPLATE_B,
                    "solution_template_html": SOLUTION_TEMPLATE_B,
                    "weight": 1
                },
                {
                    "id": "C",
                    "variant_id": "C",
                    "label": "Diagnostic",
                    "enonce_template_html": ENONCE_TEMPLATE_C,
                    "solution_template_html": SOLUTION_TEMPLATE_C,
                    "weight": 1
                }
            ],
            "enonce_template_html": ENONCE_TEMPLATE_A,  # Legacy compat
            "solution_template_html": SOLUTION_TEMPLATE_A,  # Legacy compat
        },
        {
            "id": "simplif_fractions_v2_difficile_2",
            "chapter_code": chapter_code,
            "generator_key": generator_key,
            "is_dynamic": True,
            "difficulty": "difficile",
            "offer": "pro",
            "family": "SIMPLIFICATION_FRACTIONS",
            "exercise_type": "FRACTIONS",
            "needs_svg": True,
            "variables": {
                "variant_id": "A",  # Direct
                "pedagogy_mode": "standard",
                "hint_level": 0,
                "include_feedback": False,
                "difficulty": "difficile",
                "max_denominator": 40,
                "force_reducible": True,
                "allow_negative": False,
                "allow_improper": False,
                "show_svg": True,
                "representation": "number_line"
            },
            "template_variants": [
                {
                    "id": "A",
                    "variant_id": "A",
                    "label": "Direct",
                    "enonce_template_html": ENONCE_TEMPLATE_A,
                    "solution_template_html": SOLUTION_TEMPLATE_A,
                    "weight": 1
                },
                {
                    "id": "B",
                    "variant_id": "B",
                    "label": "Guidé",
                    "enonce_template_html": ENONCE_TEMPLATE_B,
                    "solution_template_html": SOLUTION_TEMPLATE_B,
                    "weight": 1
                },
                {
                    "id": "C",
                    "variant_id": "C",
                    "label": "Diagnostic",
                    "enonce_template_html": ENONCE_TEMPLATE_C,
                    "solution_template_html": SOLUTION_TEMPLATE_C,
                    "weight": 1
                }
            ],
            "enonce_template_html": ENONCE_TEMPLATE_A,
            "solution_template_html": SOLUTION_TEMPLATE_A,
        },
        {
            "id": "simplif_fractions_v2_difficile_3",
            "chapter_code": chapter_code,
            "generator_key": generator_key,
            "is_dynamic": True,
            "difficulty": "difficile",
            "offer": "pro",
            "family": "SIMPLIFICATION_FRACTIONS",
            "exercise_type": "FRACTIONS",
            "needs_svg": True,
            "variables": {
                "variant_id": "A",  # Direct
                "pedagogy_mode": "standard",
                "hint_level": 0,
                "include_feedback": False,
                "difficulty": "difficile",
                "max_denominator": 40,
                "force_reducible": True,
                "allow_negative": False,
                "allow_improper": False,
                "show_svg": True,
                "representation": "number_line"
            },
            "template_variants": [
                {
                    "id": "A",
                    "variant_id": "A",
                    "label": "Direct",
                    "enonce_template_html": ENONCE_TEMPLATE_A,
                    "solution_template_html": SOLUTION_TEMPLATE_A,
                    "weight": 1
                },
                {
                    "id": "B",
                    "variant_id": "B",
                    "label": "Guidé",
                    "enonce_template_html": ENONCE_TEMPLATE_B,
                    "solution_template_html": SOLUTION_TEMPLATE_B,
                    "weight": 1
                },
                {
                    "id": "C",
                    "variant_id": "C",
                    "label": "Diagnostic",
                    "enonce_template_html": ENONCE_TEMPLATE_C,
                    "solution_template_html": SOLUTION_TEMPLATE_C,
                    "weight": 1
                }
            ],
            "enonce_template_html": ENONCE_TEMPLATE_A,
            "solution_template_html": SOLUTION_TEMPLATE_A,
        }
    ]
    
    # Insérer les exercices
    inserted_count = 0
    for exercise in exercises_to_create:
        try:
            result = await collection.insert_one(exercise)
            inserted_count += 1
            print(f"✅ Exercice créé : {exercise['id']} (variant_id={exercise['variables']['variant_id']})")
        except Exception as e:
            print(f"❌ Erreur lors de la création de {exercise['id']}: {e}")
    
    print(f"\n📊 Résumé : {inserted_count}/{len(exercises_to_create)} exercices créés")
    print(f"   Chapitre : {chapter_code}")
    print(f"   Générateur : {generator_key}")
    print(f"   Difficulté : difficile")
    print(f"   Chaque exercice a 3 template_variants (A/B/C)")
    
    client.close()


if __name__ == "__main__":
    asyncio.run(create_exercises())

