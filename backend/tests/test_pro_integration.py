#!/usr/bin/env python3
"""
Tests d'intégration PRO pour le générateur d'exercices

Ces tests valident:
1. Génération standard (mode gratuit) - pas de is_premium
2. Génération PRO (offer=pro) - is_premium=true + générateur DUREES_PREMIUM
3. Non-régression mode legacy (niveau + chapitre)
4. Structure de réponse compatible frontend (enonce_html, solution_html, svg)
"""

import requests
import pytest
import json
import time
from typing import Dict, Any

BASE_URL = "https://math-exercise-sync.preview.emergentagent.com"
API_URL = f"{BASE_URL}/api/v1/exercises"


def generate_exercise(payload: Dict[str, Any]) -> tuple:
    """Génère un exercice via l'API"""
    response = requests.post(
        f"{API_URL}/generate",
        json=payload,
        headers={"Content-Type": "application/json"},
        timeout=30
    )
    return response.json(), response.status_code


class TestStandardMode:
    """Tests du mode standard (gratuit)"""
    
    def test_standard_generation_6e_gm07(self):
        """Génération standard pour 6e_GM07 - doit retourner is_premium=false"""
        data, status = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen"
        })
        
        assert status == 200, f"HTTP {status}: {data}"
        assert "id_exercice" in data
        assert "enonce_html" in data
        assert "solution_html" in data
        assert data.get("metadata", {}).get("is_premium") == False
        assert data.get("metadata", {}).get("offer") in ["free", None, ""]
    
    def test_standard_generation_fractions(self):
        """Génération standard pour Fractions"""
        data, status = generate_exercise({
            "code_officiel": "6e_N08",
            "difficulte": "facile"
        })
        
        assert status == 200
        assert data.get("metadata", {}).get("is_premium") == False
        assert "FRACTION" in data.get("metadata", {}).get("generator_code", "")


class TestProMode:
    """Tests du mode PRO (premium)"""
    
    def test_pro_generation_6e_gm07(self):
        """Génération PRO pour 6e_GM07 - doit activer DUREES_PREMIUM"""
        data, status = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro"
        })
        
        assert status == 200, f"HTTP {status}: {data}"
        assert data.get("metadata", {}).get("is_premium") == True
        assert data.get("metadata", {}).get("offer") == "pro"
        assert "DUREES_PREMIUM" in data.get("metadata", {}).get("generator_code", "")
    
    def test_pro_response_structure(self):
        """Vérifie que la réponse PRO a tous les champs nécessaires au frontend"""
        data, status = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "facile",
            "offer": "pro"
        })
        
        assert status == 200
        # Champs requis par le frontend
        assert "id_exercice" in data
        assert "niveau" in data
        assert "chapitre" in data
        assert "enonce_html" in data
        assert "solution_html" in data
        assert "metadata" in data
        
        # Champs metadata requis
        metadata = data["metadata"]
        assert "is_premium" in metadata
        assert "generator_code" in metadata
        assert "difficulte" in metadata
    
    def test_pro_content_quality(self):
        """Vérifie la qualité du contenu PRO"""
        data, status = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro"
        })
        
        assert status == 200
        # L'énoncé doit être substantiel
        assert len(data.get("enonce_html", "")) > 100
        # La solution doit être substantielle
        assert len(data.get("solution_html", "")) > 100


class TestLegacyMode:
    """Tests du mode legacy (compatibilité)"""
    
    def test_legacy_fractions(self):
        """Mode legacy avec niveau + chapitre"""
        data, status = generate_exercise({
            "niveau": "6e",
            "chapitre": "Fractions",
            "difficulte": "facile"
        })
        
        assert status == 200
        assert "id_exercice" in data
        assert data.get("niveau") == "6e"
        assert "Fractions" in data.get("chapitre", "")


class TestVariation:
    """Tests des variations (même endpoint /generate avec seed différent)"""
    
    def test_variation_standard(self):
        """Variation en mode standard - doit produire des contenus différents"""
        # Génération initiale
        data1, status1 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "seed": 12345
        })
        
        # Attendre pour avoir un timestamp différent
        time.sleep(1.1)
        
        # Variation (seed différent)
        data2, status2 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "seed": 67890
        })
        
        assert status1 == 200
        assert status2 == 200
        # Les deux doivent avoir des IDs différents (timestamp différent)
        assert data1["id_exercice"] != data2["id_exercice"]
    
    def test_variation_pro(self):
        """Variation en mode PRO"""
        # Génération initiale PRO
        data1, status1 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro",
            "seed": 11111
        })
        
        # Attendre pour avoir un timestamp différent
        time.sleep(1.1)
        
        # Variation PRO (seed différent)
        data2, status2 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro",
            "seed": 22222
        })
        
        assert status1 == 200
        assert status2 == 200
        # Les deux doivent être PREMIUM
        assert data1.get("metadata", {}).get("is_premium") == True
        assert data2.get("metadata", {}).get("is_premium") == True
        # Les deux doivent avoir des IDs différents
        assert data1["id_exercice"] != data2["id_exercice"]


class TestErrorHandling:
    """Tests de gestion d'erreurs"""
    
    def test_invalid_code_officiel(self):
        """Code officiel invalide doit retourner 422"""
        data, status = generate_exercise({
            "code_officiel": "INVALID_CODE_XYZ",
            "difficulte": "facile"
        })
        
        assert status == 422
        assert "error" in data.get("detail", {}) or "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])


class TestVariationPremiumFix:
    """Tests spécifiques pour le fix de variation PREMIUM"""
    
    def test_variation_premium_stays_premium(self):
        """Une variation d'un exercice PREMIUM doit rester PREMIUM"""
        # Génération initiale PREMIUM
        data1, status1 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro",
            "seed": 11111
        })
        
        assert status1 == 200
        assert data1.get("metadata", {}).get("is_premium") == True, "L'exercice initial doit être PREMIUM"
        assert "DUREES_PREMIUM" in data1.get("metadata", {}).get("generator_code", "")
        
        # Variation PREMIUM (simule le frontend qui détecte is_premium=true et envoie offer=pro)
        time.sleep(1.1)
        data2, status2 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "offer": "pro",  # Car l'exercice courant est PREMIUM
            "seed": 22222
        })
        
        assert status2 == 200
        assert data2.get("metadata", {}).get("is_premium") == True, "La variation PREMIUM doit rester PREMIUM"
        assert "DUREES_PREMIUM" in data2.get("metadata", {}).get("generator_code", "")
        assert data1["id_exercice"] != data2["id_exercice"], "Les IDs doivent être différents"
    
    def test_variation_standard_stays_standard(self):
        """Une variation d'un exercice STANDARD doit rester STANDARD"""
        # Génération initiale STANDARD (pas de offer=pro)
        data1, status1 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            "seed": 33333
        })
        
        assert status1 == 200
        assert data1.get("metadata", {}).get("is_premium") == False, "L'exercice initial doit être STANDARD"
        assert "DUREES_PREMIUM" not in data1.get("metadata", {}).get("generator_code", "")
        
        # Variation STANDARD (simule le frontend qui détecte is_premium=false et n'envoie PAS offer=pro)
        time.sleep(1.1)
        data2, status2 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "moyen",
            # PAS de offer=pro car l'exercice courant est STANDARD
            "seed": 44444
        })
        
        assert status2 == 200
        assert data2.get("metadata", {}).get("is_premium") == False, "La variation STANDARD doit rester STANDARD"
        assert "DUREES_PREMIUM" not in data2.get("metadata", {}).get("generator_code", "")
        assert data1["id_exercice"] != data2["id_exercice"], "Les IDs doivent être différents"
    
    def test_no_accidental_premium_upgrade(self):
        """Un utilisateur PRO avec un exercice STANDARD ne doit pas upgrader en PREMIUM via variation"""
        # Même si l'utilisateur est PRO, si son exercice courant est STANDARD,
        # la variation doit rester STANDARD (comportement attendu après le fix)
        
        # Génération initiale STANDARD (utilisateur PRO mais pas de offer=pro)
        data1, status1 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "facile",
            "seed": 55555
            # PAS de offer=pro → exercice STANDARD
        })
        
        assert status1 == 200
        assert data1.get("metadata", {}).get("is_premium") == False
        
        # Variation (le frontend détecte que l'exercice courant est STANDARD)
        time.sleep(1.1)
        data2, status2 = generate_exercise({
            "code_officiel": "6e_GM07",
            "difficulte": "facile",
            "seed": 66666
            # PAS de offer=pro car exercice courant est STANDARD
        })
        
        assert status2 == 200
        assert data2.get("metadata", {}).get("is_premium") == False, "Ne doit pas upgrader accidentellement"
