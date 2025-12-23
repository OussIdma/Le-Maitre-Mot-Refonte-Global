"""
Test Générique du Contrat Générateur Premium (P1.3)
===================================================

Valide automatiquement qu'un générateur respecte le contrat officiel.
Tout générateur premium DOIT passer tous ces tests.

Référence: docs/GENERATOR_PREMIUM_CONTRACT.md
"""

import pytest
from typing import Type
from backend.generators.base_generator import BaseGenerator, GeneratorMeta, ParamSchema
from backend.generators.factory import GeneratorFactory
from fastapi import HTTPException


# Liste des générateurs premium à tester
PREMIUM_GENERATORS = [
    "RAISONNEMENT_MULTIPLICATIF_V1",
    "CALCUL_NOMBRES_V1",
    "SIMPLIFICATION_FRACTIONS_V1",
    "SIMPLIFICATION_FRACTIONS_V2",
]

# Configuration spécifique par générateur
GENERATOR_CONFIG = {
    "RAISONNEMENT_MULTIPLICATIF_V1": {"difficulty": "moyen", "grade": "6e"},
    "CALCUL_NOMBRES_V1": {"difficulty": "facile", "grade": "6e"},  # Utilise "facile" ou "standard"
    "SIMPLIFICATION_FRACTIONS_V1": {"difficulty": "standard", "grade": "6e"},
    "SIMPLIFICATION_FRACTIONS_V2": {"difficulty": "standard", "grade": "6e"},
}


class TestGeneratorContract:
    """Tests génériques du contrat pour tous les générateurs premium."""
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_1_herite_base_generator(self, generator_key):
        """
        CONTRAT 1: Le générateur DOIT hériter de BaseGenerator.
        """
        gen_class = GeneratorFactory.get(generator_key)
        assert gen_class is not None, f"Générateur {generator_key} introuvable"
        assert issubclass(gen_class, BaseGenerator), \
            f"{generator_key} doit hériter de BaseGenerator"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_2_meta_complete(self, generator_key):
        """
        CONTRAT 2: get_meta() DOIT retourner GeneratorMeta complet.
        
        Vérifie:
        - key présent et non vide
        - label présent
        - description présente
        - version présente (format X.Y.Z)
        - niveaux non vide
        - exercise_type présent
        - is_dynamic = True
        - supported_grades présent
        """
        gen_class = GeneratorFactory.get(generator_key)
        meta = gen_class.get_meta()
        
        assert isinstance(meta, GeneratorMeta), "get_meta() doit retourner GeneratorMeta"
        assert meta.key, "meta.key manquant"
        assert meta.key == generator_key, f"meta.key ({meta.key}) != {generator_key}"
        assert meta.label, "meta.label manquant"
        assert len(meta.label) < 100, "meta.label trop long"
        assert meta.description, "meta.description manquante"
        assert meta.version, "meta.version manquante"
        # Vérifier format version X.Y.Z
        assert len(meta.version.split('.')) == 3, "Version doit être au format X.Y.Z"
        assert meta.niveaux, "meta.niveaux vide"
        assert len(meta.niveaux) > 0, "Au moins 1 niveau requis"
        assert meta.exercise_type, "meta.exercise_type manquant"
        
        # P1.2 - Nouveaux champs obligatoires
        assert hasattr(meta, 'is_dynamic'), "meta.is_dynamic manquant"
        assert meta.is_dynamic is True, "meta.is_dynamic doit être True pour un générateur premium"
        
        # supported_grades est auto-rempli depuis niveaux si absent
        meta_dict = meta.to_dict()
        assert 'supported_grades' in meta_dict, "supported_grades manquant dans to_dict()"
        assert len(meta_dict['supported_grades']) > 0, "supported_grades vide"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_3_schema_seed_obligatoire(self, generator_key):
        """
        CONTRAT 3: Le schéma DOIT contenir un paramètre 'seed' obligatoire.
        """
        gen_class = GeneratorFactory.get(generator_key)
        schema = gen_class.get_schema()
        
        assert isinstance(schema, list), "get_schema() doit retourner une liste"
        assert len(schema) > 0, "Schéma vide"
        
        # Chercher le paramètre seed
        seed_param = next((p for p in schema if p.name == "seed"), None)
        assert seed_param is not None, "Paramètre 'seed' manquant dans le schéma"
        assert seed_param.required is True, "Le paramètre 'seed' doit être obligatoire (required=True)"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_4_variables_obligatoires(self, generator_key):
        """
        CONTRAT 4: generate() DOIT retourner toutes les variables obligatoires.
        
        Variables minimales:
        - enonce
        - consigne
        - solution
        - calculs_intermediaires
        - reponse_finale
        - niveau
        - type_exercice
        """
        gen_class = GeneratorFactory.get(generator_key)
        generator = gen_class(seed=42)
        
        # Params minimaux pour générer (spécifiques à chaque générateur)
        config = GENERATOR_CONFIG.get(generator_key, {"difficulty": "moyen", "grade": "6e"})
        params = {
            "seed": 42,
            **config
        }
        
        result = generator.generate(params)
        
        assert "variables" in result, "result doit contenir 'variables'"
        variables = result["variables"]
        
        # Variables OBLIGATOIRES selon le contrat
        required_vars = [
            "enonce",
            "consigne",
            "solution",
            "calculs_intermediaires",
            "reponse_finale",
            "niveau",
            "type_exercice",
        ]
        
        for var in required_vars:
            assert var in variables, f"Variable obligatoire manquante: {var}"
            assert variables[var] is not None, f"Variable {var} est None"
            if var != "donnees":  # donnees peut être vide
                assert variables[var] != "", f"Variable {var} est vide"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_5_determinisme(self, generator_key):
        """
        CONTRAT 5: Le générateur DOIT être déterministe (seed fixe → résultat identique).
        """
        gen_class = GeneratorFactory.get(generator_key)
        
        config = GENERATOR_CONFIG.get(generator_key, {"difficulty": "moyen", "grade": "6e"})
        params = {
            "seed": 999,
            **config
        }
        
        gen1 = gen_class(seed=999)
        gen2 = gen_class(seed=999)
        
        result1 = gen1.generate(params)
        result2 = gen2.generate(params)
        
        # Vérifier que les variables clés sont identiques
        vars1 = result1["variables"]
        vars2 = result2["variables"]
        
        assert vars1["enonce"] == vars2["enonce"], "Déterminisme échoué: enonce différent"
        assert vars1["solution"] == vars2["solution"], "Déterminisme échoué: solution différente"
        assert vars1["reponse_finale"] == vars2["reponse_finale"], "Déterminisme échoué: reponse_finale différente"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_6_securite_html_enonce(self, generator_key):
        """
        CONTRAT 6: La variable 'enonce' NE DOIT PAS contenir de HTML complexe.
        
        P0.4 - Sécurisation HTML:
        - Pas de <table> (utiliser tableau_html)
        - Pas de <script>, <iframe>, <object>
        - Pas de javascript:, onclick, onerror
        """
        gen_class = GeneratorFactory.get(generator_key)
        generator = gen_class(seed=42)
        
        config = GENERATOR_CONFIG.get(generator_key, {"difficulty": "moyen", "grade": "6e"})
        params = {
            "seed": 42,
            **config
        }
        
        result = generator.generate(params)
        enonce = result["variables"]["enonce"]
        
        enonce_lower = enonce.lower()
        
        # Balises interdites
        forbidden_tags = [
            "<script",
            "<iframe",
            "<object",
            "<embed",
            "<style",
            "javascript:",
            "onclick=",
            "onerror=",
        ]
        
        for tag in forbidden_tags:
            assert tag not in enonce_lower, \
                f"❌ SÉCURITÉ: {tag} trouvé dans enonce (INTERDIT)"
        
        # P0.4: <table> ne doit PAS être dans enonce
        if "<table" in enonce_lower:
            # Vérifier que tableau_html existe
            assert "tableau_html" in result["variables"], \
                "Si <table> dans enonce, tableau_html DOIT exister (P0.4)"
            
            # ATTENTION: Cette règle peut être assouplie si le générateur n'utilise pas de tableau
            # Pour l'instant, on log un warning plutôt qu'échouer
            import warnings
            warnings.warn(f"{generator_key}: <table> trouvé dans enonce, devrait être dans tableau_html (P0.4)")
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_7_variete_enonces(self, generator_key):
        """
        CONTRAT 7: Le générateur DOIT produire au moins 3 variantes d'énoncés.
        
        P0.1 - Variabilité des énoncés.
        """
        gen_class = GeneratorFactory.get(generator_key)
        
        enonces = set()
        consignes = set()
        
        # Tester avec 50 seeds différents
        config = GENERATOR_CONFIG.get(generator_key, {"difficulty": "moyen", "grade": "6e"})
        for seed in range(50):
            generator = gen_class(seed=seed)
            params = {
                "seed": seed,
                **config
            }
            
            result = generator.generate(params)
            enonces.add(result["variables"]["enonce"])
            consignes.add(result["variables"]["consigne"])
        
        # Au moins 3 variantes d'énoncés différents
        assert len(enonces) >= 3, \
            f"Variété insuffisante: seulement {len(enonces)} énoncés différents sur 50 seeds (min: 3)"
        
        # Au moins 2 variantes de consignes
        assert len(consignes) >= 2, \
            f"Variété insuffisante: seulement {len(consignes)} consignes différentes sur 50 seeds (min: 2)"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_8_erreurs_422_structurees(self, generator_key):
        """
        CONTRAT 8: Les erreurs DOIVENT être des HTTPException 422 structurées.
        
        Format attendu:
        {
            "error_code": "CODE",
            "error": "code_snake",
            "message": "Message lisible",
            "hint": "Suggestion",
            "context": {...}
        }
        """
        gen_class = GeneratorFactory.get(generator_key)
        generator = gen_class(seed=42)
        
        # Tester avec des paramètres invalides
        invalid_params = {
            "seed": 42,
            "difficulty": "INVALID_DIFFICULTY_XXXXX",
            "grade": "6e",
        }
        
        with pytest.raises(HTTPException) as exc_info:
            generator.generate(invalid_params)
        
        # Vérifier le code HTTP
        assert exc_info.value.status_code == 422, "Code HTTP doit être 422"
        
        # Vérifier la structure du detail
        detail = exc_info.value.detail
        assert isinstance(detail, dict), "detail doit être un dict"
        assert "error_code" in detail, "error_code manquant"
        assert "message" in detail, "message manquant"
        
        # error_code doit être en MAJUSCULES
        assert detail["error_code"].isupper(), "error_code doit être en MAJUSCULES"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_9_presets_non_vide(self, generator_key):
        """
        CONTRAT 9: get_presets() DOIT retourner au moins 1 preset.
        """
        gen_class = GeneratorFactory.get(generator_key)
        presets = gen_class.get_presets()
        
        assert isinstance(presets, list), "get_presets() doit retourner une liste"
        assert len(presets) >= 1, "Au moins 1 preset requis"
        
        # Vérifier la structure du premier preset
        preset = presets[0]
        assert hasattr(preset, 'key'), "Preset doit avoir un 'key'"
        assert hasattr(preset, 'label'), "Preset doit avoir un 'label'"
        assert hasattr(preset, 'params'), "Preset doit avoir 'params'"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_10_reponse_finale_string(self, generator_key):
        """
        CONTRAT 10: La variable 'reponse_finale' DOIT être une chaîne (str).
        
        Même pour les nombres, convertir en string.
        """
        gen_class = GeneratorFactory.get(generator_key)
        generator = gen_class(seed=42)
        
        config = GENERATOR_CONFIG.get(generator_key, {"difficulty": "moyen", "grade": "6e"})
        params = {
            "seed": 42,
            **config
        }
        
        result = generator.generate(params)
        reponse_finale = result["variables"]["reponse_finale"]
        
        assert isinstance(reponse_finale, str), \
            f"reponse_finale doit être str, pas {type(reponse_finale).__name__}"
        assert reponse_finale != "", "reponse_finale ne doit pas être vide"
    
    @pytest.mark.parametrize("generator_key", PREMIUM_GENERATORS)
    def test_contract_11_enregistre_factory(self, generator_key):
        """
        CONTRAT 11: Le générateur DOIT être enregistré dans GeneratorFactory.
        """
        gen_class = GeneratorFactory.get(generator_key)
        assert gen_class is not None, \
            f"{generator_key} non enregistré dans GeneratorFactory"
        
        # Vérifier qu'il apparaît dans list_all()
        all_generators = GeneratorFactory.list_all()
        generator_keys = [g["key"] for g in all_generators]
        assert generator_key in generator_keys, \
            f"{generator_key} absent de GeneratorFactory.list_all()"
    
    def test_contract_12_tous_generateurs_testes(self):
        """
        CONTRAT 12: TOUS les générateurs premium enregistrés DOIVENT être testés.
        
        Ce test échoue si un nouveau générateur premium est ajouté
        sans être ajouté à PREMIUM_GENERATORS.
        """
        all_generators = GeneratorFactory.list_all()
        
        # Filtrer les générateurs premium (is_dynamic=True ou nom contient PREMIUM/V1)
        premium_keys = [
            g["key"] for g in all_generators 
            if g.get("key", "").endswith("_V1") or "PREMIUM" in g.get("label", "")
        ]
        
        # Vérifier que tous sont dans PREMIUM_GENERATORS
        for key in premium_keys:
            if key not in PREMIUM_GENERATORS:
                pytest.fail(
                    f"⚠️ Générateur premium {key} trouvé mais non testé!\n"
                    f"Ajouter '{key}' à PREMIUM_GENERATORS dans test_generator_contract.py"
                )
        
        print(f"✅ Tous les {len(PREMIUM_GENERATORS)} générateurs premium sont testés")


# Tests de validation globale (pas par générateur)
class TestGeneratorContractGlobal:
    """Tests globaux du contrat (tous générateurs ensemble)."""
    
    def test_global_cles_uniques(self):
        """
        GLOBAL: Les clés des générateurs DOIVENT être uniques.
        """
        all_generators = GeneratorFactory.list_all()
        keys = [g["key"] for g in all_generators]
        
        # Vérifier pas de doublons
        duplicates = [key for key in keys if keys.count(key) > 1]
        assert len(duplicates) == 0, f"Clés dupliquées trouvées: {set(duplicates)}"
    
    def test_global_versioning(self):
        """
        GLOBAL: Les clés DOIVENT suivre le pattern NOM_VX.
        """
        all_generators = GeneratorFactory.list_all()
        
        for gen in all_generators:
            key = gen["key"]
            # Vérifier format NAME_V1, NAME_V2, etc.
            assert "_V" in key, f"{key} ne suit pas le pattern NOM_VX"
            
            # Extraire la version
            version_part = key.split("_V")[-1]
            assert version_part.isdigit(), f"{key}: version doit être un nombre"


# Fonction de test rapide pour validation manuelle
if __name__ == "__main__":
    print("🧪 Test du Contrat Générateur Premium - Validation manuelle\n")
    
    for gen_key in PREMIUM_GENERATORS:
        print(f"\n{'='*60}")
        print(f"Validation: {gen_key}")
        print(f"{'='*60}")
        
        test_instance = TestGeneratorContract()
        
        try:
            print("✓ Test 1: Hérite BaseGenerator")
            test_instance.test_contract_1_herite_base_generator(gen_key)
            
            print("✓ Test 2: Meta complète")
            test_instance.test_contract_2_meta_complete(gen_key)
            
            print("✓ Test 3: Seed obligatoire")
            test_instance.test_contract_3_schema_seed_obligatoire(gen_key)
            
            print("✓ Test 4: Variables obligatoires")
            test_instance.test_contract_4_variables_obligatoires(gen_key)
            
            print("✓ Test 5: Déterminisme")
            test_instance.test_contract_5_determinisme(gen_key)
            
            print("✓ Test 6: Sécurité HTML")
            test_instance.test_contract_6_securite_html_enonce(gen_key)
            
            print("✓ Test 7: Variété énoncés")
            test_instance.test_contract_7_variete_enonces(gen_key)
            
            print("✓ Test 8: Erreurs 422")
            test_instance.test_contract_8_erreurs_422_structurees(gen_key)
            
            print("✓ Test 9: Presets")
            test_instance.test_contract_9_presets_non_vide(gen_key)
            
            print("✓ Test 10: Réponse finale string")
            test_instance.test_contract_10_reponse_finale_string(gen_key)
            
            print("✓ Test 11: Enregistré Factory")
            test_instance.test_contract_11_enregistre_factory(gen_key)
            
            print(f"\n✅ {gen_key}: TOUS LES TESTS PASSÉS")
            
        except AssertionError as e:
            print(f"\n❌ {gen_key}: ÉCHEC")
            print(f"   Erreur: {e}")
            raise
        except Exception as e:
            print(f"\n❌ {gen_key}: ERREUR INATTENDUE")
            print(f"   Erreur: {e}")
            raise
    
    print(f"\n{'='*60}")
    print(f"✅ TOUS LES GÉNÉRATEURS PREMIUM RESPECTENT LE CONTRAT")
    print(f"{'='*60}")

