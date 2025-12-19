"""
Tests massifs des 16 générateurs mathématiques
50 générations par générateur pour détecter bugs rares
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.math_generation_service import MathGenerationService
from models.math_models import MathExerciseType
import json
import math


class TestResults:
    """Stockage des résultats de tests"""
    def __init__(self, generator_name):
        self.generator_name = generator_name
        self.total = 0
        self.success = 0
        self.errors = []
        self.warnings = []
        self.examples = []
    
    def add_success(self):
        self.total += 1
        self.success += 1
    
    def add_error(self, message, spec=None):
        self.total += 1
        self.errors.append({
            'message': message,
            'spec': spec.parametres if spec else None
        })
    
    def add_warning(self, message):
        self.warnings.append(message)
    
    def add_example(self, spec):
        if len(self.examples) < 2:
            self.examples.append({
                'parametres': spec.parametres,
                'resultat': spec.resultat_final
            })
    
    def get_success_rate(self):
        return (self.success / self.total * 100) if self.total > 0 else 0
    
    def print_report(self):
        print(f"\n{'='*80}")
        print(f"📊 RAPPORT: {self.generator_name}")
        print(f"{'='*80}")
        print(f"Total générations: {self.total}")
        print(f"Succès: {self.success} ({self.get_success_rate():.1f}%)")
        print(f"Erreurs: {len(self.errors)}")
        print(f"Warnings: {len(self.warnings)}")
        
        if self.errors:
            print(f"\n❌ ERREURS:")
            for i, err in enumerate(self.errors[:3], 1):
                print(f"  {i}. {err['message']}")
                if err['spec']:
                    print(f"     Params: {err['spec']}")
        
        if self.warnings:
            print(f"\n⚠️ WARNINGS:")
            for warn in self.warnings[:3]:
                print(f"  - {warn}")
        
        if self.examples:
            print(f"\n📄 EXEMPLES:")
            for i, ex in enumerate(self.examples, 1):
                print(f"  Exemple {i}: {ex['resultat']}")


def test_generator(service, generator_func, niveau, chapitre, nb_tests=50):
    """Test un générateur avec nb_tests générations"""
    generator_name = generator_func.__name__.replace('_gen_', '')
    results = TestResults(generator_name)
    
    for i in range(nb_tests):
        try:
            spec = generator_func(niveau, chapitre, "facile")
            
            # Vérification 1: Spec existe
            if spec is None:
                results.add_error("Spec None retournée")
                continue
            
            # Vérification 2: Champs obligatoires
            if not spec.parametres:
                results.add_error("Paramètres manquants", spec)
                continue
            
            if not spec.solution_calculee:
                results.add_error("Solution calculée manquante", spec)
                continue
            
            # Vérification 3: Calculs mathématiques selon le type
            error = verify_calculations(spec)
            if error:
                results.add_error(error, spec)
                continue
            
            # Vérification 4: Points géométriques cohérents
            if spec.figure_geometrique:
                error = verify_geometry_points(spec)
                if error:
                    results.add_warning(error)
            
            results.add_success()
            results.add_example(spec)
            
        except Exception as e:
            results.add_error(f"Exception: {str(e)[:100]}")
    
    return results


def verify_calculations(spec):
    """Vérifie la cohérence mathématique selon le type"""
    type_ex = spec.type_exercice
    params = spec.parametres
    solution = spec.solution_calculee
    
    try:
        if type_ex == "cercle":
            if params.get('type') == 'perimetre':
                rayon = params['rayon']
                perimetre = solution['perimetre']
                attendu = round(2 * math.pi * rayon, 2)
                if abs(perimetre - attendu) > 0.02:
                    return f"Périmètre incorrect: {perimetre} != {attendu}"
            
            elif params.get('type') == 'aire':
                rayon = params['rayon']
                aire = solution['aire']
                attendu = round(math.pi * rayon * rayon, 2)
                if abs(aire - attendu) > 0.02:
                    return f"Aire incorrecte: {aire} != {attendu}"
        
        elif type_ex == "triangle_rectangle":
            # Vérifier Pythagore si données disponibles
            pass
        
        elif type_ex == "thales":
            AD = params.get('AD', 0)
            DB = params.get('DB', 0)
            AE = params.get('AE', 0)
            EC = params.get('EC', 0)
            AB = solution.get('AB', 0)
            AC = solution.get('AC', 0)
            
            if AB != AD + DB:
                return f"Somme incorrecte: AB={AB} != {AD}+{DB}"
            if AC != AE + EC:
                return f"Somme incorrecte: AC={AC} != {AE}+{EC}"
            
            # Vérifier égalité rapports
            if AB > 0 and AC > 0:
                r1 = round(AD / AB, 4)
                r2 = round(AE / AC, 4)
                if abs(r1 - r2) > 0.01:
                    return f"Rapports Thalès non égaux: {r1} != {r2}"
        
        elif type_ex == "volume":
            # Vérifications volumes
            pass
        
        return None
    except Exception as e:
        return f"Erreur vérification: {str(e)}"


def verify_geometry_points(spec):
    """Vérifie cohérence des points géométriques"""
    figure = spec.figure_geometrique
    
    if not figure or not figure.points:
        return None
    
    # Vérifier que les points sont uniques
    if len(figure.points) != len(set(figure.points)):
        return "Points géométriques dupliqués"
    
    # Vérifier que ce sont des lettres majuscules
    for point in figure.points:
        if not point.isupper() or len(point) != 1:
            return f"Point invalide: {point}"
    
    return None


def run_all_tests():
    """Exécute tous les tests sur les 16 générateurs"""
    service = MathGenerationService()
    
    generators_config = [
        # (fonction, niveau, chapitre, nom)
        (service._gen_calcul_relatifs, "5e", "Nombres relatifs", "Calcul Relatifs"),
        (service._gen_calcul_fractions, "6e", "Fractions", "Calcul Fractions"),
        (service._gen_calcul_decimaux, "6e", "Nombres entiers et décimaux", "Calcul Décimaux"),
        (service._gen_equation_1er_degre, "4e", "Équations", "Équations 1er degré"),
        (service._gen_triangle_rectangle, "4e", "Théorème de Pythagore", "Triangle Rectangle"),
        (service._gen_triangle_quelconque, "5e", "Triangles", "Triangle Quelconque"),
        (service._gen_proportionnalite, "6e", "Proportionnalité", "Proportionnalité"),
        (service._gen_perimetre_aire, "6e", "Périmètres et aires", "Périmètre/Aire"),
        (service._gen_rectangle, "6e", "Géométrie - Triangles et quadrilatères", "Rectangle"),
        (service._gen_volume, "6e", "Volumes", "Volumes"),
        (service._gen_statistiques, "5e", "Statistiques", "Statistiques"),
        (service._gen_probabilites, "3e", "Probabilités", "Probabilités"),
        (service._gen_puissances, "4e", "Puissances", "Puissances"),
        (service._gen_cercle, "6e", "Aires", "Cercles"),
        (service._gen_thales, "3e", "Théorème de Thalès", "Thalès"),
        (service._gen_trigonometrie, "3e", "Trigonométrie", "Trigonométrie"),
    ]
    
    all_results = []
    
    print("="*80)
    print("🧪 TESTS MASSIFS - 16 GÉNÉRATEURS × 50 GÉNÉRATIONS")
    print("="*80)
    
    for i, (func, niveau, chapitre, name) in enumerate(generators_config, 1):
        print(f"\n[{i}/16] Test {name}...", end=" ")
        results = test_generator(service, func, niveau, chapitre, nb_tests=50)
        all_results.append(results)
        print(f"✅ {results.success}/50" if results.success == 50 else f"⚠️ {results.success}/50")
    
    # Rapport final
    print(f"\n\n{'='*80}")
    print("📋 RAPPORT FINAL - TESTS MASSIFS")
    print(f"{'='*80}")
    
    for results in all_results:
        results.print_report()
    
    # Synthèse globale
    total_tests = sum(r.total for r in all_results)
    total_success = sum(r.success for r in all_results)
    total_errors = sum(len(r.errors) for r in all_results)
    
    print(f"\n\n{'='*80}")
    print("🎯 SYNTHÈSE GLOBALE")
    print(f"{'='*80}")
    print(f"Total générations: {total_tests}")
    print(f"Succès: {total_success} ({total_success/total_tests*100:.1f}%)")
    print(f"Erreurs: {total_errors}")
    
    generators_ok = sum(1 for r in all_results if r.get_success_rate() == 100)
    print(f"\nGénérateurs 100% OK: {generators_ok}/16")
    
    if generators_ok == 16:
        print("\n✅ TOUS LES GÉNÉRATEURS SONT OPÉRATIONNELS")
    else:
        print(f"\n⚠️ {16 - generators_ok} GÉNÉRATEUR(S) À CORRIGER")


if __name__ == "__main__":
    run_all_tests()
