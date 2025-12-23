"""
Service de gestion des templates éditables de générateurs

Permet aux admins de créer, modifier, et valider les templates
de rédaction (énoncés/solutions) sans toucher au code.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import re

from backend.models.generator_template import (
    GeneratorTemplate,
    GeneratorTemplateCreate,
    GeneratorTemplateUpdate,
    GeneratorTemplateValidateRequest,
    GeneratorTemplateValidateResponse
)
from backend.generators.factory import GeneratorFactory
from backend.services.template_renderer import render_template
from logger import get_logger

logger = get_logger()


class GeneratorTemplateService:
    """Service de gestion des templates de générateurs"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.generator_templates
    
    async def create_template(self, template_data: GeneratorTemplateCreate) -> GeneratorTemplate:
        """Créer un nouveau template"""
        template_dict = template_data.dict()
        template_dict["created_at"] = datetime.utcnow()
        template_dict["updated_at"] = datetime.utcnow()
        
        result = await self.collection.insert_one(template_dict)
        template_dict["_id"] = str(result.inserted_id)
        
        logger.info(
            f"Template créé: generator={template_data.generator_key}, "
            f"variant={template_data.variant_id}, id={result.inserted_id}"
        )
        
        return GeneratorTemplate(**template_dict)
    
    async def get_template(self, template_id: str) -> Optional[GeneratorTemplate]:
        """Récupérer un template par ID"""
        try:
            template_dict = await self.collection.find_one({"_id": ObjectId(template_id)})
            if template_dict:
                template_dict["_id"] = str(template_dict["_id"])
                return GeneratorTemplate(**template_dict)
        except Exception as e:
            logger.error(f"Erreur récupération template {template_id}: {e}")
        return None
    
    async def list_templates(
        self,
        generator_key: Optional[str] = None,
        variant_id: Optional[str] = None,
        grade: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> List[GeneratorTemplate]:
        """Lister les templates avec filtres optionnels"""
        query = {}
        if generator_key:
            query["generator_key"] = generator_key
        if variant_id:
            query["variant_id"] = variant_id
        if grade:
            query["grade"] = grade
        if difficulty:
            query["difficulty"] = difficulty
        
        templates = []
        cursor = self.collection.find(query).sort("created_at", -1)
        
        async for template_dict in cursor:
            template_dict["_id"] = str(template_dict["_id"])
            templates.append(GeneratorTemplate(**template_dict))
        
        logger.info(f"Liste templates: {len(templates)} trouvés avec query={query}")
        return templates
    
    async def update_template(
        self,
        template_id: str,
        template_update: GeneratorTemplateUpdate
    ) -> Optional[GeneratorTemplate]:
        """Mettre à jour un template"""
        update_data = template_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        try:
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(template_id)},
                {"$set": update_data},
                return_document=True
            )
            
            if result:
                result["_id"] = str(result["_id"])
                logger.info(f"Template mis à jour: id={template_id}")
                return GeneratorTemplate(**result)
        except Exception as e:
            logger.error(f"Erreur mise à jour template {template_id}: {e}")
        
        return None
    
    async def delete_template(self, template_id: str) -> bool:
        """Supprimer un template"""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(template_id)})
            if result.deleted_count > 0:
                logger.info(f"Template supprimé: id={template_id}")
                return True
        except Exception as e:
            logger.error(f"Erreur suppression template {template_id}: {e}")
        
        return False
    
    async def get_best_template(
        self,
        generator_key: str,
        variant_id: str = "default",
        grade: Optional[str] = None,
        difficulty: Optional[str] = None
    ) -> Optional[GeneratorTemplate]:
        """
        Récupérer le meilleur template selon la priorité:
        1. Exact match (generator + variant + grade + difficulty)
        2. Sans difficulty (generator + variant + grade)
        3. Sans grade (generator + variant)
        4. Default (generator + "default")
        """
        queries = []
        
        # 1. Exact match
        if grade and difficulty:
            queries.append({
                "generator_key": generator_key,
                "variant_id": variant_id,
                "grade": grade,
                "difficulty": difficulty
            })
        
        # 2. Sans difficulty
        if grade:
            queries.append({
                "generator_key": generator_key,
                "variant_id": variant_id,
                "grade": grade,
                "difficulty": None
            })
        
        # 3. Sans grade
        queries.append({
            "generator_key": generator_key,
            "variant_id": variant_id,
            "grade": None,
            "difficulty": None
        })
        
        # 4. Default variant
        if variant_id != "default":
            queries.append({
                "generator_key": generator_key,
                "variant_id": "default",
                "grade": None,
                "difficulty": None
            })
        
        # Tester chaque query par priorité
        for query in queries:
            template_dict = await self.collection.find_one(query)
            if template_dict:
                template_dict["_id"] = str(template_dict["_id"])
                logger.info(
                    f"Template trouvé (priorité): generator={generator_key}, "
                    f"query={query}"
                )
                return GeneratorTemplate(**template_dict)
        
        logger.info(
            f"Aucun template trouvé pour generator={generator_key}, "
            f"variant={variant_id}, grade={grade}, difficulty={difficulty}"
        )
        return None
    
    async def validate_template(
        self,
        request: GeneratorTemplateValidateRequest
    ) -> GeneratorTemplateValidateResponse:
        """
        Valider un template et générer un preview
        
        1. Génère des variables via GeneratorFactory
        2. Parse les placeholders dans les templates
        3. Vérifie que tous les placeholders existent
        4. Vérifie la sécurité HTML (triple moustaches)
        5. Génère un preview du rendu
        """
        try:
            # 1. Générer des variables via le générateur
            logger.info(
                f"Validation template: generator={request.generator_key}, "
                f"seed={request.seed}"
            )
            
            generated = GeneratorFactory.generate(
                key=request.generator_key,
                exercise_params={},
                overrides={
                    "seed": request.seed,
                    "grade": request.grade,
                    "difficulty": request.difficulty,
                    "variant_id": request.variant_id
                },
                seed=request.seed
            )
            
            variables = generated.get("variables", {})
            
            # 2. Parser les placeholders utilisés dans les templates
            enonce_placeholders = self._extract_placeholders(request.enonce_template_html)
            solution_placeholders = self._extract_placeholders(request.solution_template_html)
            all_placeholders = set(enonce_placeholders + solution_placeholders)
            
            # 3. Vérifier les placeholders manquants
            missing = []
            for placeholder in all_placeholders:
                if placeholder not in variables:
                    missing.append(placeholder)
            
            # 4. Vérifier la sécurité HTML (triple moustaches)
            html_errors = []
            triple_enonce = self._extract_triple_placeholders(request.enonce_template_html)
            triple_solution = self._extract_triple_placeholders(request.solution_template_html)
            all_triple = set(triple_enonce + triple_solution)
            
            for var in all_triple:
                if var not in request.allowed_html_vars:
                    html_errors.append({
                        "type": "html_var_not_allowed",
                        "placeholder": var,
                        "message": (
                            f"Triple moustaches interdites pour '{var}'. "
                            f"Ajoutez '{var}' à allowed_html_vars ou utilisez {{{{var}}}}"
                        )
                    })
            
            # Si erreurs, retourner invalid
            if missing or html_errors:
                return GeneratorTemplateValidateResponse(
                    valid=False,
                    used_placeholders=list(all_placeholders),
                    missing_placeholders=missing,
                    html_security_errors=html_errors,
                    error_message=self._build_error_message(missing, html_errors)
                )
            
            # 5. Générer le preview
            enonce_html = render_template(request.enonce_template_html, variables)
            solution_html = render_template(request.solution_template_html, variables)
            
            return GeneratorTemplateValidateResponse(
                valid=True,
                used_placeholders=list(all_placeholders),
                missing_placeholders=[],
                html_security_errors=[],
                preview={
                    "enonce_html": enonce_html,
                    "solution_html": solution_html,
                    "variables": variables
                }
            )
            
        except Exception as e:
            logger.error(f"Erreur validation template: {e}", exc_info=True)
            return GeneratorTemplateValidateResponse(
                valid=False,
                error_message=f"Erreur lors de la validation: {str(e)}"
            )
    
    def _extract_placeholders(self, template: str) -> List[str]:
        """Extraire tous les placeholders {{var}} et {{{var}}} d'un template"""
        # Pattern pour {{var}} et {{{var}}}
        pattern = r'\{\{+(\w+)\}\}+'
        matches = re.findall(pattern, template)
        return list(set(matches))
    
    def _extract_triple_placeholders(self, template: str) -> List[str]:
        """Extraire uniquement les placeholders {{{var}}}"""
        pattern = r'\{\{\{(\w+)\}\}\}'
        matches = re.findall(pattern, template)
        return list(set(matches))
    
    def _build_error_message(
        self,
        missing: List[str],
        html_errors: List[dict]
    ) -> str:
        """Construire un message d'erreur lisible"""
        messages = []
        
        if missing:
            messages.append(
                f"Placeholders manquants: {', '.join(missing)}. "
                "Ces variables n'existent pas dans le générateur."
            )
        
        if html_errors:
            vars_not_allowed = [e["placeholder"] for e in html_errors]
            messages.append(
                f"Variables HTML non autorisées: {', '.join(vars_not_allowed)}. "
                "Ajoutez-les à allowed_html_vars ou utilisez {{{{var}}}}."
            )
        
        return " | ".join(messages)


def get_template_service(db: AsyncIOMotorDatabase) -> GeneratorTemplateService:
    """Factory pour créer le service de templates"""
    return GeneratorTemplateService(db)

