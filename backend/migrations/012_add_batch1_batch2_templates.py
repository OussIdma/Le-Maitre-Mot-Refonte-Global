"""
Migration 012 : Ajouter les templates pour les générateurs Gold Batch 1 & 2
===========================================================================

Batch 1:
- NOMBRES_ENTIERS_V1
- DROITE_GRADUEE_V1
- CRITERES_DIVISIBILITE_V1
- MULTIPLES_DIVISEURS_V1
- PERIMETRE_V1

Batch 2:
- FRACTION_REPRESENTATION_V1
- FRACTIONS_EGALES_V1
- FRACTION_COMPARAISON_V1

Chaque générateur reçoit un template par défaut utilisant les variables
retournées par le générateur (enonce, reponse_finale, consigne, etc.)
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Templates génériques utilisant les variables communes des générateurs
TEMPLATES = {
    "NOMBRES_ENTIERS_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
</div>"""
    },

    "DROITE_GRADUEE_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
</div>"""
    },

    "CRITERES_DIVISIBILITE_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
<p class="explication">{{explication}}</p>
</div>"""
    },

    "MULTIPLES_DIVISEURS_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
</div>"""
    },

    "PERIMETRE_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Formule :</strong> {{formule}}</p>
<p><strong>Calcul :</strong> {{calcul}}</p>
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
</div>"""
    },

    "FRACTION_REPRESENTATION_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
</div>"""
    },

    "FRACTIONS_EGALES_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
<p class="explication">{{explication}}</p>
</div>"""
    },

    "FRACTION_COMPARAISON_V1": {
        "enonce": """<div class="exercise">
<p class="enonce">{{enonce}}</p>
<p class="consigne"><em>{{consigne}}</em></p>
</div>""",
        "solution": """<div class="solution">
<p><strong>Réponse :</strong> {{reponse_finale}}</p>
</div>"""
    },
}


async def run_migration():
    """Ajoute les templates pour les générateurs Batch 1 & 2."""

    mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongo:27017")
    client = AsyncIOMotorClient(mongo_uri)
    db_name = os.getenv("DB_NAME", "le_maitre_mot_db")
    db = client[db_name]

    # Collection pour les templates
    templates_collection = db.generator_templates

    now = datetime.utcnow()
    inserted_count = 0
    skipped_count = 0

    for generator_key, templates in TEMPLATES.items():
        # Vérifier si un template existe déjà
        existing = await templates_collection.find_one({
            "generator_key": generator_key,
            "variant_id": "default"
        })

        if existing:
            print(f"⚠️  Template existant pour {generator_key}, ignoré")
            skipped_count += 1
            continue

        template_doc = {
            "generator_key": generator_key,
            "variant_id": "default",
            "grade": None,  # Tous niveaux
            "difficulty": None,  # Toutes difficultés
            "enonce_template_html": templates["enonce"],
            "solution_template_html": templates["solution"],
            "allowed_html_vars": [],
            "created_at": now,
            "updated_at": now,
            "created_by": "migration_012"
        }

        try:
            await templates_collection.insert_one(template_doc)
            inserted_count += 1
            print(f"✅ Template créé pour {generator_key}")
        except Exception as e:
            print(f"❌ Erreur pour {generator_key}: {e}")

    print(f"\n📊 Résumé migration 012:")
    print(f"   {inserted_count} templates créés")
    print(f"   {skipped_count} templates ignorés (existants)")

    client.close()


if __name__ == "__main__":
    asyncio.run(run_migration())
