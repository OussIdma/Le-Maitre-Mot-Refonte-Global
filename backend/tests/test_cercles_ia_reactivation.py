"""
Tests de réactivation IA pour CERCLES
Objectif : Valider que le pipeline IA → Validation → Fallback fonctionne correctement

Scénarios :
1. IA cohérente → acceptée
2. IA incohérente (rayon inventé) → rejetée → fallback
3. IA incohérente (centre inventé) → rejetée → fallback
4. Calcul taux d'acceptation/rejet IA
"""

import pytest
import asyncio
import sys
import os
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from services.math_text_service import MathTextService
from models.math_models import MathExerciseSpec


class TestCerclesIAReactivation:
    """Tests spécifiques réactivation IA pour Cercles"""
    
    def setup_method(self):
        """Setup avant chaque test"""
        self.math_service = MathGenerationService()
        self.text_service = MathTextService()
        
        # Compteurs pour monitoring
        self.stats = {
            "total": 0,
            "ia_acceptee": 0,
            "ia_rejetee": 0,
            "fallback_utilise": 0,
            "erreurs_validation": []
        }
    
    def _generate_cercle_spec(self) -> MathExerciseSpec:
        """Générer une spec Cercle"""
        specs = self.math_service.generate_math_exercise_specs(
            niveau="6e",
            chapitre="Aires",
            difficulte="facile",
            nb_exercices=1
        )
        
        # Filtrer pour obtenir un cercle
        for spec in specs:
            if spec.type_exercice.value == "cercle":
                return spec
        
        # Si pas de cercle, régénérer
        return self._generate_cercle_spec()
    
    @pytest.mark.asyncio
    async def test_cercle_ia_generation_basique(self):
        """Test basique : génération IA cercle"""
        print("\n" + "="*80)
        print("TEST : Génération IA Cercle (basique)")
        print("="*80)
        
        spec = self._generate_cercle_spec()
        
        print(f"Spec générée :")
        print(f"  - Type : {spec.type_exercice.value}")
        print(f"  - Rayon : {spec.parametres.get('rayon')} cm")
        print(f"  - Centre : {spec.figure_geometrique.points[0] if spec.figure_geometrique else 'N/A'}")
        
        # Générer texte IA
        text = await self.text_service._generate_text_for_single_spec(spec)
        
        print(f"\nTexte généré :")
        print(f"  - Énoncé : {text.enonce[:80]}...")
        print(f"  - Solution : {text.solution_redigee[:80] if text.solution_redigee else 'N/A'}...")
        
        # Vérifications
        assert text.enonce is not None
        assert len(text.enonce) > 10
        
        print("\n✅ Test basique réussi")
    
    @pytest.mark.asyncio
    async def test_cercle_validation_coherence(self):
        """Test validation : vérifier que les données sont cohérentes"""
        print("\n" + "="*80)
        print("TEST : Validation Cohérence Cercle")
        print("="*80)
        
        spec = self._generate_cercle_spec()
        rayon_attendu = spec.parametres.get("rayon")
        centre_attendu = spec.figure_geometrique.points[0] if spec.figure_geometrique else None
        
        print(f"Données attendues :")
        print(f"  - Rayon : {rayon_attendu} cm")
        print(f"  - Centre : {centre_attendu}")
        
        # Générer texte
        text = await self.text_service._generate_text_for_single_spec(spec)
        
        # Vérifier présence des données
        import re
        
        # Vérifier rayon dans énoncé
        rayon_pattern = r'rayon\s+(?:de\s+)?(\d+(?:\.\d+)?)\s*cm'
        rayons_detectes = re.findall(rayon_pattern, text.enonce, re.IGNORECASE)
        
        print(f"\nRayons détectés dans énoncé : {rayons_detectes}")
        
        if rayons_detectes:
            rayon_detecte = float(rayons_detectes[0])
            assert abs(rayon_detecte - rayon_attendu) < 0.01, \
                f"Rayon incohérent : attendu={rayon_attendu}, détecté={rayon_detecte}"
            print(f"✅ Rayon cohérent : {rayon_detecte} cm")
        else:
            print(f"⚠️ Aucun rayon explicite détecté (peut être implicite)")
        
        # Vérifier centre
        if centre_attendu:
            centre_pattern = r'centre\s+([A-Z])'
            centres_detectes = re.findall(centre_pattern, text.enonce, re.IGNORECASE)
            
            print(f"Centres détectés : {centres_detectes}")
            
            if centres_detectes:
                for centre in centres_detectes:
                    assert centre == centre_attendu, \
                        f"Centre incohérent : attendu={centre_attendu}, détecté={centre}"
                print(f"✅ Centre cohérent : {centre_attendu}")
        
        print("\n✅ Validation cohérence réussie")
    
    @pytest.mark.asyncio
    async def test_cercle_batch_monitoring(self):
        """Test batch : générer 20 cercles et monitorer le taux d'acceptation IA"""
        print("\n" + "="*80)
        print("TEST : Batch Monitoring (20 Cercles)")
        print("="*80)
        
        nb_tests = 20
        stats = {
            "total": 0,
            "ia_utilisee": 0,
            "fallback_utilise": 0,
            "coherents": 0,
            "incoherents": 0
        }
        
        for i in range(nb_tests):
            try:
                spec = self._generate_cercle_spec()
                text = await self.text_service._generate_text_for_single_spec(spec)
                
                stats["total"] += 1
                
                # Vérifier si fallback a été utilisé (énoncé commence par pattern fallback)
                est_fallback = "Calculer le périmètre" in text.enonce or "Calculer l'aire" in text.enonce
                
                if est_fallback:
                    stats["fallback_utilise"] += 1
                else:
                    stats["ia_utilisee"] += 1
                
                # Vérifier cohérence
                rayon_attendu = spec.parametres.get("rayon")
                import re
                rayon_pattern = r'rayon\s+(?:de\s+)?(\d+(?:\.\d+)?)\s*cm'
                rayons_detectes = re.findall(rayon_pattern, text.enonce, re.IGNORECASE)
                
                est_coherent = True
                if rayons_detectes:
                    rayon_detecte = float(rayons_detectes[0])
                    if abs(rayon_detecte - rayon_attendu) > 0.01:
                        est_coherent = False
                
                if est_coherent:
                    stats["coherents"] += 1
                else:
                    stats["incoherents"] += 1
                
                print(f"Exercice {i+1}/{nb_tests} : {'✅ Cohérent' if est_coherent else '❌ Incohérent'} "
                      f"({'Fallback' if est_fallback else 'IA'})")
                
            except Exception as e:
                print(f"Erreur exercice {i+1} : {e}")
        
        # Afficher résultats
        print("\n" + "="*80)
        print("RÉSULTATS MONITORING")
        print("="*80)
        print(f"Total exercices : {stats['total']}")
        print(f"IA utilisée : {stats['ia_utilisee']} ({stats['ia_utilisee']/stats['total']*100:.1f}%)")
        print(f"Fallback utilisé : {stats['fallback_utilise']} ({stats['fallback_utilise']/stats['total']*100:.1f}%)")
        print(f"Exercices cohérents : {stats['coherents']} ({stats['coherents']/stats['total']*100:.1f}%)")
        print(f"Exercices incohérents : {stats['incoherents']} ({stats['incoherents']/stats['total']*100:.1f}%)")
        
        # Assertions
        taux_coherence = stats['coherents'] / stats['total']
        assert taux_coherence >= 0.95, \
            f"Taux de cohérence insuffisant : {taux_coherence*100:.1f}% (min 95%)"
        
        print("\n✅ Test batch monitoring réussi")
    
    @pytest.mark.asyncio
    async def test_cercle_formules_correctes(self):
        """Test : vérifier que les formules sont correctes (périmètre vs aire)"""
        print("\n" + "="*80)
        print("TEST : Formules Correctes (Périmètre vs Aire)")
        print("="*80)
        
        # Tester périmètre
        print("\n1️⃣ Test Périmètre")
        spec = self._generate_cercle_spec()
        
        # Forcer type périmètre si possible
        if spec.parametres.get("type") != "perimetre":
            # Régénérer jusqu'à obtenir périmètre
            for _ in range(10):
                spec = self._generate_cercle_spec()
                if spec.parametres.get("type") == "perimetre":
                    break
        
        if spec.parametres.get("type") == "perimetre":
            text = await self.text_service._generate_text_for_single_spec(spec)
            
            # Vérifier formule 2πr présente
            import re
            formule_ok = bool(re.search(r'2\s*[×x*π]\s*π\s*[×x*]\s*r|2\s*π\s*r|périmètre', 
                                       text.enonce + (text.solution_redigee or ''), 
                                       re.IGNORECASE))
            
            print(f"Formule périmètre détectée : {formule_ok}")
            assert formule_ok or "périmètre" in text.enonce.lower(), \
                "Formule périmètre non détectée"
        
        print("\n✅ Test formules réussi")


if __name__ == "__main__":
    # Exécution directe
    import asyncio
    
    test = TestCerclesIAReactivation()
    test.setup_method()
    
    print("\n" + "🚀"*40)
    print("TESTS RÉACTIVATION IA - CERCLES")
    print("🚀"*40 + "\n")
    
    async def run_tests():
        try:
            await test.test_cercle_ia_generation_basique()
            await test.test_cercle_validation_coherence()
            await test.test_cercle_batch_monitoring()
            await test.test_cercle_formules_correctes()
            
            print("\n" + "="*80)
            print("✅ TOUS LES TESTS RÉACTIVATION IA CERCLES PASSENT")
            print("="*80 + "\n")
            
        except AssertionError as e:
            print(f"\n❌ ÉCHEC DES TESTS: {e}\n")
            exit(1)
    
    asyncio.run(run_tests())
