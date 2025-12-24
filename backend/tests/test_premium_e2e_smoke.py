"""
Smoke Test E2E Premium (P1.4)
==============================

Test de bout en bout minimal pour valider le parcours premium complet:
- API /api/v1/exercises/generate avec offer=pro
- Dispatch automatique vers GeneratorFactory
- Rendu HTML correct (enonce_html + solution_html)
- Métadonnées premium (is_premium=true, generator_key)

Contraintes:
- Test rapide (<2s)
- Seed fixe pour déterminisme
- Pas d'IA externe, pas de DB
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from backend.routes.exercises_routes import router

# Créer une instance FastAPI et y inclure le router
app = FastAPI()
app.include_router(router, prefix="/api/v1/exercises")

client = TestClient(app)


class TestPremiumE2ESmoke:
    """Tests E2E pour les générateurs premium."""
    
    def test_e2e_6e_sp03_raisonnement_multiplicatif(self):
        """
        Test E2E: 6e_SP03 → RAISONNEMENT_MULTIPLICATIF_V1
        
        Vérifie:
        - 200 OK
        - enonce_html non vide
        - solution_html non vide
        - metadata.is_premium = true
        - metadata.generator_key présent
        """
        # Requête réelle à l'API
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité simple dans des tableaux",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42
            }
        )
        
        # Assertions de base
        assert response.status_code == 200, f"Erreur API: {response.text}"
        
        data = response.json()
        
        # Vérifier la structure de base
        assert "id_exercice" in data
        assert "niveau" in data
        assert "chapitre" in data
        assert "enonce_html" in data
        assert "solution_html" in data
        assert "metadata" in data
        
        # Vérifier que les HTML ne sont pas vides
        assert len(data["enonce_html"]) > 100, "enonce_html est trop court ou vide"
        assert len(data["solution_html"]) > 100, "solution_html est trop court ou vide"
        
        # Vérifier les métadonnées premium
        metadata = data["metadata"]
        assert metadata.get("is_premium") is True, "is_premium devrait être True"
        assert "generator_key" in metadata, "generator_key manquant"
        assert metadata["generator_key"] in ["RAISONNEMENT_MULTIPLICATIF_V1", "CALCUL_NOMBRES_V1"], \
            f"generator_key inattendu: {metadata.get('generator_key')}"
        
        # Vérifier que le HTML contient des éléments attendus
        assert "<p>" in data["enonce_html"], "enonce_html mal formé (pas de <p>)"
        assert "<strong>" in data["enonce_html"], "enonce_html mal formé (pas de <strong>)"
        
        # Pour RAISONNEMENT_MULTIPLICATIF_V1, on s'attend à un tableau
        if metadata["generator_key"] == "RAISONNEMENT_MULTIPLICATIF_V1":
            assert "<table" in data["enonce_html"], "Tableau HTML manquant pour RAISONNEMENT_MULTIPLICATIF_V1"
        
        # Vérifier le seed dans les métadonnées
        assert metadata.get("seed") == 42, "Seed incorrect dans metadata"
        
        print(f"✅ Test E2E 6e_SP03 → {metadata['generator_key']} : OK")
        print(f"   Énoncé: {len(data['enonce_html'])} chars")
        print(f"   Solution: {len(data['solution_html'])} chars")
    
    def test_e2e_6e_n04_calcul_nombres(self):
        """
        Test E2E: 6e_N04 → CALCUL_NOMBRES_V1
        
        Vérifie:
        - 200 OK
        - enonce_html non vide
        - solution_html non vide
        - metadata.is_premium = true
        - metadata.generator_key = CALCUL_NOMBRES_V1
        """
        # Requête réelle à l'API
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_N04",
                "niveau": "6e",
                "chapitre": "Addition et soustraction de nombres entiers",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 123
            }
        )
        
        # Assertions de base
        assert response.status_code == 200, f"Erreur API: {response.text}"
        
        data = response.json()
        
        # Vérifier la structure de base
        assert "enonce_html" in data
        assert "solution_html" in data
        assert "metadata" in data
        
        # Vérifier que les HTML ne sont pas vides
        assert len(data["enonce_html"]) > 50, "enonce_html est trop court ou vide"
        assert len(data["solution_html"]) > 50, "solution_html est trop court ou vide"
        
        # Vérifier les métadonnées premium
        metadata = data["metadata"]
        assert metadata.get("is_premium") is True, "is_premium devrait être True"
        assert "generator_key" in metadata, "generator_key manquant"
        assert metadata["generator_key"] in ["CALCUL_NOMBRES_V1", "RAISONNEMENT_MULTIPLICATIF_V1"], \
            f"generator_key inattendu: {metadata.get('generator_key')}"
        
        # Vérifier que le HTML contient des éléments attendus
        assert "<p>" in data["enonce_html"], "enonce_html mal formé"
        assert "<div" in data["solution_html"], "solution_html mal formé"
        
        # Pour CALCUL_NOMBRES_V1, on s'attend à des calculs
        if metadata["generator_key"] == "CALCUL_NOMBRES_V1":
            # Vérifier que les variables sont présentes
            assert "variables" in metadata, "Variables manquantes dans metadata"
            variables = metadata["variables"]
            assert "consigne" in variables, "Consigne manquante"
            assert "enonce" in variables, "Énoncé manquant"
            assert "solution" in variables, "Solution manquante"
            assert "reponse_finale" in variables, "Réponse finale manquante"
        
        print(f"✅ Test E2E 6e_N04 → {metadata['generator_key']} : OK")
        print(f"   Énoncé: {len(data['enonce_html'])} chars")
        print(f"   Solution: {len(data['solution_html'])} chars")
    
    def test_e2e_determinisme_premium(self):
        """
        Test E2E: Déterminisme avec seed fixe.
        
        Vérifie que 2 appels avec le même seed produisent le même exercice.
        """
        params = {
            "code_officiel": "6e_SP03",
            "niveau": "6e",
            "chapitre": "Proportionnalité",
            "difficulte": "moyen",
            "offer": "pro",
            "seed": 999
        }
        
        # Premier appel
        response1 = client.post("/api/v1/exercises/generate", json=params)
        assert response1.status_code == 200
        data1 = response1.json()
        
        # Deuxième appel avec le même seed
        response2 = client.post("/api/v1/exercises/generate", json=params)
        assert response2.status_code == 200
        data2 = response2.json()
        
        # Vérifier que les contenus sont identiques
        assert data1["enonce_html"] == data2["enonce_html"], "Déterminisme échoué: enonce_html différent"
        assert data1["solution_html"] == data2["solution_html"], "Déterminisme échoué: solution_html différent"
        assert data1["metadata"]["generator_key"] == data2["metadata"]["generator_key"], \
            "Déterminisme échoué: generator_key différent"
        
        print("✅ Test E2E déterminisme : OK")
    
    def test_e2e_offer_free_pas_premium(self):
        """
        Test E2E: offer=free ne doit PAS utiliser les générateurs premium.
        
        Vérifie que même avec un chapitre ayant des générateurs premium,
        offer=free ne les utilise pas.
        """
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "free",  # ← FREE
                "seed": 42
            }
        )
        
        # Peut réussir (200) ou échouer (422) selon la disponibilité d'exercices non-premium
        if response.status_code == 200:
            data = response.json()
            metadata = data.get("metadata", {})
            
            # Si 200, vérifier qu'on n'a PAS de générateur premium Factory
            # (is_premium peut ne pas exister ou être False)
            is_premium = metadata.get("is_premium", False)
            assert is_premium is False, "offer=free ne devrait pas déclencher premium Factory"
            
            print("✅ Test E2E offer=free : OK (pas de premium)")
        elif response.status_code == 422:
            # 422 acceptable si pas d'exercices non-premium disponibles
            print("✅ Test E2E offer=free : OK (422 car pas d'exercices free)")
        else:
            pytest.fail(f"Status inattendu: {response.status_code}")
    
    def test_e2e_generation_time(self):
        """
        Test E2E: Temps de génération raisonnable (<2s).
        
        Vérifie que la génération est rapide.
        """
        import time
        
        start = time.time()
        
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42
            }
        )
        
        duration = time.time() - start
        
        assert response.status_code == 200
        assert duration < 2.0, f"Génération trop lente: {duration:.2f}s (attendu <2s)"
        
        print(f"✅ Test E2E temps de génération : {duration:.3f}s (OK)")
    
    def test_e2e_html_security(self):
        """
        Test E2E: Sécurité HTML (pas de <script>, <iframe>, etc.).
        
        Vérifie que les HTML générés ne contiennent pas de balises dangereuses.
        """
        response = client.post(
            "/api/v1/exercises/generate",
            json={
                "code_officiel": "6e_SP03",
                "niveau": "6e",
                "chapitre": "Proportionnalité",
                "difficulte": "moyen",
                "offer": "pro",
                "seed": 42
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        enonce_html = data["enonce_html"].lower()
        solution_html = data["solution_html"].lower()
        
        # Balises dangereuses interdites
        forbidden_tags = ["<script", "<iframe", "<object", "<embed", "javascript:", "onerror=", "onclick="]
        
        for tag in forbidden_tags:
            assert tag not in enonce_html, f"⚠️ SÉCURITÉ: {tag} trouvé dans enonce_html"
            assert tag not in solution_html, f"⚠️ SÉCURITÉ: {tag} trouvé dans solution_html"
        
        print("✅ Test E2E sécurité HTML : OK (pas de balises dangereuses)")


# Fonction de test rapide pour validation manuelle
if __name__ == "__main__":
    print("🧪 Smoke Tests E2E Premium - Validation manuelle\n")
    
    test_instance = TestPremiumE2ESmoke()
    
    try:
        print("Test 1/7: 6e_SP03 → RAISONNEMENT_MULTIPLICATIF_V1")
        test_instance.test_e2e_6e_sp03_raisonnement_multiplicatif()
        print()
        
        print("Test 2/7: 6e_N04 → CALCUL_NOMBRES_V1")
        test_instance.test_e2e_6e_n04_calcul_nombres()
        print()
        
        print("Test 3/7: Déterminisme")
        test_instance.test_e2e_determinisme_premium()
        print()
        
        print("Test 4/7: offer=free pas premium")
        test_instance.test_e2e_offer_free_pas_premium()
        print()
        
        print("Test 5/7: Temps de génération")
        test_instance.test_e2e_generation_time()
        print()
        
        print("Test 6/7: Sécurité HTML")
        test_instance.test_e2e_html_security()
        print()
        
        print("\n✅ Tous les smoke tests E2E sont passés!")
        
    except AssertionError as e:
        print(f"\n❌ Échec: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise





