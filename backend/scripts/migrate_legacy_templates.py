"""
Script de migration des templates hardcodés legacy vers MongoDB

Migre les templates de:
- RAISONNEMENT_MULTIPLICATIF_V1
- CALCUL_NOMBRES_V1
- SIMPLIFICATION_FRACTIONS_V2

Source: frontend/src/components/admin/ChapterExercisesAdminPage.js (getDynamicTemplates)
Destination: MongoDB collection generator_templates via API

Usage:
    python backend/scripts/migrate_legacy_templates.py [--dry-run] [--backend-url http://localhost:8000]
"""
import argparse
import requests
import sys
from typing import Dict, List

# Templates legacy extraits de ChapterExercisesAdminPage.js
LEGACY_TEMPLATES = {
    "RAISONNEMENT_MULTIPLICATIF_V1": {
        "variant_id": "A",
        "grade": None,
        "difficulty": None,
        "enonce_template_html": """<div class="exercise-enonce">
  <p><strong>{{consigne}}</strong></p>
  <p>{{enonce}}</p>
  {{{tableau_html}}}
</div>""",
        "solution_template_html": """<div class="exercise-solution">
  <h4 style="color: #2563eb; margin-bottom: 1rem;">Méthode : {{methode}}</h4>
  <div class="calculs" style="background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <pre style="white-space: pre-line; font-family: inherit; margin: 0;">{{calculs_intermediaires}}</pre>
  </div>
  <div class="solution-text" style="margin-bottom: 1rem;">
    <p>{{solution}}</p>
  </div>
  <div class="reponse-finale" style="background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;">
    <p style="margin: 0;"><strong>Réponse finale :</strong> {{reponse_finale}}</p>
  </div>
</div>""",
        "allowed_html_vars": ["tableau_html"]
    },
    "CALCUL_NOMBRES_V1": {
        "variant_id": "A",
        "grade": None,
        "difficulty": None,
        "enonce_template_html": """<div class="exercise-enonce">
  <p><strong>{{consigne}}</strong></p>
  <div class="enonce-content" style="font-size: 1.125rem; margin-top: 0.5rem;">{{enonce}}</div>
</div>""",
        "solution_template_html": """<div class="exercise-solution">
  <h4 style="color: #2563eb; margin-bottom: 1rem;">Correction</h4>
  <div class="calculs" style="background: #f1f5f9; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
    <pre style="white-space: pre-line; font-family: inherit; margin: 0;">{{calculs_intermediaires}}</pre>
  </div>
  <div class="solution-text" style="margin-bottom: 1rem;">
    <p>{{solution}}</p>
  </div>
  <div class="reponse-finale" style="background: #dcfce7; padding: 0.75rem; border-left: 4px solid #22c55e; border-radius: 0.25rem;">
    <p style="margin: 0;"><strong>Résultat :</strong> {{reponse_finale}}</p>
  </div>
</div>""",
        "allowed_html_vars": []
    },
    "SIMPLIFICATION_FRACTIONS_V2": {
        "variant_id": "A",
        "grade": None,
        "difficulty": None,
        "enonce_template_html": "<p><strong>Simplifier la fraction :</strong> {{fraction}}</p>",
        "solution_template_html": """<ol>
  <li>{{step1}}</li>
  <li>{{step2}}</li>
  <li>{{step3}}</li>
  <li><strong>Résultat :</strong> {{fraction_reduite}}</li>
</ol>""",
        "allowed_html_vars": []
    }
}


def validate_template(backend_url: str, generator_key: str, template: Dict) -> Dict:
    """
    Valide un template via l'API /validate
    
    Retourne: {"valid": bool, "errors": List[str]}
    """
    url = f"{backend_url}/api/v1/admin/generator-templates/validate"
    
    payload = {
        "generator_key": generator_key,
        "variant_id": template["variant_id"],
        "grade": template["grade"],
        "difficulty": template["difficulty"],
        "seed": 42,  # Seed fixe pour reproductibilité
        "enonce_template_html": template["enonce_template_html"],
        "solution_template_html": template["solution_template_html"],
        "allowed_html_vars": template["allowed_html_vars"]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "valid": data.get("valid", False),
                "errors": [],
                "used_placeholders": data.get("used_placeholders", [])
            }
        elif response.status_code == 422:
            data = response.json()
            detail = data.get("detail", {})
            errors = []
            
            if detail.get("missing_placeholders"):
                errors.append(f"Placeholders manquants: {', '.join(detail['missing_placeholders'])}")
            
            if detail.get("html_security_errors"):
                for err in detail["html_security_errors"]:
                    errors.append(f"HTML error: {err.get('message', 'Unknown')}")
            
            return {
                "valid": False,
                "errors": errors
            }
        else:
            return {
                "valid": False,
                "errors": [f"HTTP {response.status_code}: {response.text[:200]}"]
            }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Exception: {str(e)}"]
        }


def create_template(backend_url: str, generator_key: str, template: Dict, dry_run: bool = False) -> Dict:
    """
    Crée un template via l'API POST /generator-templates
    
    Retourne: {"success": bool, "template_id": str, "errors": List[str]}
    """
    url = f"{backend_url}/api/v1/admin/generator-templates"
    
    payload = {
        "generator_key": generator_key,
        "variant_id": template["variant_id"],
        "grade": template["grade"],
        "difficulty": template["difficulty"],
        "enonce_template_html": template["enonce_template_html"],
        "solution_template_html": template["solution_template_html"],
        "allowed_html_vars": template["allowed_html_vars"]
    }
    
    if dry_run:
        return {
            "success": True,
            "template_id": "dry-run-id",
            "errors": [],
            "dry_run": True
        }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 201:
            data = response.json()
            return {
                "success": True,
                "template_id": data.get("id"),
                "errors": []
            }
        else:
            return {
                "success": False,
                "template_id": None,
                "errors": [f"HTTP {response.status_code}: {response.text[:200]}"]
            }
    except Exception as e:
        return {
            "success": False,
            "template_id": None,
            "errors": [f"Exception: {str(e)}"]
        }


def check_template_exists(backend_url: str, generator_key: str, variant_id: str) -> bool:
    """Vérifie si un template existe déjà en DB"""
    url = f"{backend_url}/api/v1/admin/generator-templates"
    params = {"generator_key": generator_key}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            templates = response.json()
            for tpl in templates:
                if tpl.get("variant_id") == variant_id and tpl.get("grade") is None and tpl.get("difficulty") is None:
                    return True
        return False
    except Exception:
        return False


def migrate_templates(backend_url: str, dry_run: bool = False, force: bool = False):
    """
    Migration principale des templates legacy → DB
    """
    print("=" * 80)
    print("MIGRATION DES TEMPLATES LEGACY → MONGODB")
    print("=" * 80)
    print(f"\nBackend URL: {backend_url}")
    print(f"Mode: {'DRY-RUN (aucune création)' if dry_run else 'PRODUCTION (création réelle)'}")
    print(f"Force: {'Oui (écrase existants)' if force else 'Non (skip si existe)'}")
    print()
    
    results = {
        "total": len(LEGACY_TEMPLATES),
        "validated": 0,
        "created": 0,
        "skipped": 0,
        "errors": 0
    }
    
    for generator_key, template in LEGACY_TEMPLATES.items():
        print(f"\n{'─' * 80}")
        print(f"📦 {generator_key}")
        print(f"{'─' * 80}")
        
        # 1. Vérifier si existe déjà
        if not force:
            exists = check_template_exists(backend_url, generator_key, template["variant_id"])
            if exists:
                print(f"⏭️  Template existe déjà en DB → SKIP")
                results["skipped"] += 1
                continue
        
        # 2. Validation
        print("🔍 Validation via /validate...")
        validation = validate_template(backend_url, generator_key, template)
        
        if validation["valid"]:
            print(f"✅ Validation réussie")
            print(f"   Placeholders: {', '.join(validation['used_placeholders'])}")
            results["validated"] += 1
        else:
            print(f"❌ Validation échouée:")
            if not validation["errors"]:
                print(f"   - Aucune erreur détaillée retournée (vérifier logs backend)")
            for error in validation["errors"]:
                print(f"   - {error}")
            results["errors"] += 1
            continue
        
        # 3. Création
        if not dry_run:
            print("💾 Création template en DB...")
        else:
            print("💾 Création template en DB (DRY-RUN, pas de création réelle)...")
        
        creation = create_template(backend_url, generator_key, template, dry_run)
        
        if creation["success"]:
            if dry_run:
                print(f"✅ Template serait créé (dry-run)")
            else:
                print(f"✅ Template créé: ID={creation['template_id']}")
            results["created"] += 1
        else:
            print(f"❌ Création échouée:")
            for error in creation["errors"]:
                print(f"   - {error}")
            results["errors"] += 1
    
    # Résumé
    print(f"\n{'=' * 80}")
    print("RÉSUMÉ DE LA MIGRATION")
    print(f"{'=' * 80}")
    print(f"Total templates: {results['total']}")
    print(f"✅ Validés: {results['validated']}")
    print(f"✅ Créés: {results['created']}")
    print(f"⏭️  Skippés (existants): {results['skipped']}")
    print(f"❌ Erreurs: {results['errors']}")
    print()
    
    if dry_run:
        print("ℹ️  Mode DRY-RUN : Aucun template n'a été créé")
        print("   Relancez sans --dry-run pour effectuer la migration réelle")
    elif results["created"] > 0:
        print("✅ Migration terminée avec succès")
        print("   Les templates sont maintenant disponibles en DB")
        print("   L'API /generate utilisera automatiquement ces templates (template_source='db')")
    else:
        print("⚠️  Aucun template créé (tous skippés ou erreurs)")
    
    print()
    
    # Code de sortie
    if results["errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="Migrer les templates hardcodés legacy vers MongoDB"
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8000",
        help="URL du backend (défaut: http://localhost:8000)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode dry-run: valide mais ne crée pas les templates"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force la création même si les templates existent déjà"
    )
    
    args = parser.parse_args()
    
    migrate_templates(
        backend_url=args.backend_url,
        dry_run=args.dry_run,
        force=args.force
    )


if __name__ == "__main__":
    main()

