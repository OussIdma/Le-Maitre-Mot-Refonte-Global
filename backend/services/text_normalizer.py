"""
Service de normalisation et sécurisation des textes générés par l'IA
Garantit la cohérence des notations mathématiques et géométriques
"""
import re
from typing import Dict, List, Set
from backend.constants import MATH_SYMBOLS


class TextNormalizer:
    """Normalise et sécurise les textes d'exercices"""
    
    def __init__(self):
        self.math_symbols = MATH_SYMBOLS
    
    def normalize_math_symbols(self, text: str) -> str:
        """
        Normalise les symboles mathématiques dans le texte
        
        Remplace :
        - * ou x par ×
        - / par ÷ (dans certains contextes)
        - ^2 par ²
        - deg ou ° manquants
        """
        # Multiplication
        text = re.sub(r'\s*\*\s*', ' × ', text)
        text = re.sub(r'(\d+)\s*x\s*(\d+)', r'\1 × \2', text)
        
        # Puissances
        text = re.sub(r'\^2(?!\d)', '²', text)
        text = re.sub(r'\^3(?!\d)', '³', text)
        
        # Approximation
        text = re.sub(r'≈|~=|environ', '≈', text)
        
        # Degrés
        text = re.sub(r'(\d+)\s*deg\b', r'\1°', text)
        
        return text
    
    def validate_geometry_points(
        self, 
        text: str, 
        expected_points: List[str]
    ) -> Dict[str, any]:
        """
        Vérifie que les points géométriques dans le texte correspondent
        aux points attendus de la spec
        
        Args:
            text: Texte à vérifier
            expected_points: Points attendus (ex: ['A', 'B', 'C'])
            
        Returns:
            {
                'valid': bool,
                'found_points': List[str],
                'unexpected_points': List[str],
                'missing_points': List[str]
            }
        """
        # Extraire tous les points (lettres majuscules isolées)
        found_points = set(re.findall(r'\b([A-Z])\b', text))
        expected_set = set(expected_points)
        
        unexpected = found_points - expected_set
        missing = expected_set - found_points
        
        # Filtrer les faux positifs courants
        false_positives = {'I', 'O', 'L', 'D', 'E', 'M', 'N', 'P', 'R', 'S', 'T', 'U', 'V'}
        # Ne garder que les points non ambigus ou ceux dans expected
        unexpected = {p for p in unexpected if p in expected_set or p not in false_positives}
        
        return {
            'valid': len(unexpected) == 0,
            'found_points': sorted(found_points),
            'unexpected_points': sorted(unexpected),
            'missing_points': sorted(missing)
        }
    
    def ensure_point_consistency(
        self, 
        enonce: str, 
        solution: str, 
        spec_points: List[str]
    ) -> Dict[str, str]:
        """
        S'assure que les points mentionnés dans l'énoncé et la solution
        sont cohérents avec la spec
        
        Retourne les textes corrigés si nécessaire
        """
        result = {
            'enonce': enonce,
            'solution': solution,
            'warnings': []
        }
        
        # Vérifier l'énoncé
        enonce_validation = self.validate_geometry_points(enonce, spec_points)
        if not enonce_validation['valid']:
            result['warnings'].append(
                f"Points inattendus dans énoncé: {enonce_validation['unexpected_points']}"
            )
        
        # Vérifier la solution
        solution_validation = self.validate_geometry_points(solution, spec_points)
        if not solution_validation['valid']:
            result['warnings'].append(
                f"Points inattendus dans solution: {solution_validation['unexpected_points']}"
            )
        
        return result
    
    def remove_personal_names(self, text: str) -> str:
        """
        Supprime les prénoms personnels qui pourraient apparaître
        (ex: "Chaima", "Pierre", etc.)
        
        Garde uniquement les points géométriques A-Z
        """
        # Liste de prénoms courants à détecter (à compléter si nécessaire)
        common_names = [
            'Chaima', 'Pierre', 'Marie', 'Jean', 'Sophie', 'Lucas',
            'Emma', 'Louis', 'Léa', 'Hugo', 'Chloé', 'Gabriel'
        ]
        
        for name in common_names:
            # Remplacer le prénom par un point géométrique générique
            text = re.sub(rf'\b{name}\b', '[point]', text, flags=re.IGNORECASE)
        
        return text
    
    def clean_latex_symbols(self, text: str) -> str:
        """
        Nettoie les symboles LaTeX mal formés
        """
        # Remplacer \frac mal formé
        text = re.sub(r'\\frac\s*{([^}]+)}\s*{([^}]+)}', r'\1/\2', text)
        
        # Supprimer les \( \) isolés
        text = re.sub(r'\\\(|\\\)', '', text)
        
        return text


# Instance globale
normalizer = TextNormalizer()
