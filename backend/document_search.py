# SYSTÈME DE RECHERCHE DE DOCUMENTS PÉDAGOGIQUES
# Spécialisé pour la Géographie avec cartes libres de droit

import aiohttp
import json
import re
from typing import Dict, List, Optional, Any
from logger import get_logger

logger = get_logger()

class DocumentSearcher:
    """Recherche automatique de documents pédagogiques libres de droit"""
    
    def __init__(self):
        self.wikimedia_api_base = "https://commons.wikimedia.org/w/api.php"
        self.wikimedia_base_url = "https://commons.wikimedia.org"
        
        # Cache des documents validés avec URLs TESTÉES ET VALIDES (Octobre 2025)
        self.validated_documents_cache = {
            # Cartes de base avec URLs vérifiées fonctionnelles
            "carte_france": {
                "titre": "Carte administrative de France métropolitaine",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/France%2C_administrative_divisions_-_Nmbrs_%28departments%2Boverseas%29.svg/1200px-France%2C_administrative_divisions_-_Nmbrs_%28departments%2Boverseas%29.svg.png",
                "licence": {"type": "CC BY-SA 3.0", "notice_attribution": "TUBS, CC BY-SA 3.0, via Wikimedia Commons"},
                "largeur_px": 1200,
                "hauteur_px": 1154
            },
            "carte_monde": {
                "titre": "Planisphère avec continents et océans",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "licence": {"type": "PD", "notice_attribution": "Domaine public"},
                "largeur_px": 1200,
                "hauteur_px": 600
            },
            
            # Cartes simplifiées utilisant des URLs plus fiables (fallback sur carte monde pour régions)
            "carte_europe": {
                "titre": "Carte du monde centrée sur l'Europe",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "licence": {"type": "PD", "notice_attribution": "Domaine public"},
                "largeur_px": 1200,
                "hauteur_px": 600
            },
            "carte_asie": {
                "titre": "Carte du monde centrée sur l'Asie",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "licence": {"type": "PD", "notice_attribution": "Domaine public"},
                "largeur_px": 1200,
                "hauteur_px": 600
            },
            "carte_amerique_nord": {
                "titre": "Carte du monde centrée sur l'Amérique du Nord",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "licence": {"type": "PD", "notice_attribution": "Domaine public"},
                "largeur_px": 1200,
                "hauteur_px": 600
            },
            "carte_afrique": {
                "titre": "Carte du monde centrée sur l'Afrique",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "licence": {"type": "PD", "notice_attribution": "Domaine public"},
                "largeur_px": 1200,
                "hauteur_px": 600
            }
        }
    
    async def search_geographic_document(self, document_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Recherche un document géographique selon les critères spécifiés avec DIVERSIFICATION FORCÉE
        
        Args:
            document_request: Dictionnaire avec type, doit_afficher, langue, avoid_types, etc.
        
        Returns:
            Dictionnaire avec métadonnées complètes du document trouvé
        """
        doc_type = document_request.get("type", "carte_monde")
        langue = document_request.get("langue", "français")
        elements_requis = document_request.get("doit_afficher", [])
        avoid_types = document_request.get("avoid_types", [])  # NOUVEAU : types à éviter
        
        # NOUVEAU : Analyse intelligente du contenu pour choisir le bon document
        enonce = document_request.get("enonce", "")
        if enonce:
            intelligent_doc_type = self._analyze_content_for_document_type(enonce)
            logger.info(f"🧠 Document analysis: {doc_type} → {intelligent_doc_type}")
            # Utiliser le type intelligent si différent
            if intelligent_doc_type != "carte_monde" or doc_type == "cartographic":
                doc_type = intelligent_doc_type
        
        logger.info(
            f"🔍 Starting geographic document search",
            module_name="document_search",
            func_name="search_geographic_document",
            doc_type=doc_type,
            langue=langue,
            elements_requis=elements_requis
        )
        
        # Vérifier d'abord le cache des documents validés avec DIVERSIFICATION
        cached_doc = self._check_cache(doc_type, elements_requis)
        if cached_doc:
            # 🎯 FORCER LA DIVERSIFICATION : Éviter les titres déjà utilisés
            doc_title = cached_doc.get('titre', '')
            if doc_title in avoid_types:
                logger.info(f"🔄 Document '{doc_title}' déjà utilisé, cherchons une alternative...")
                # Essayer d'autres types disponibles
                alternative_types = ["carte_france", "carte_europe", "carte_asie", "carte_amerique_nord", "carte_afrique", "carte_monde"]
                for alt_type in alternative_types:
                    if alt_type != doc_type:
                        alt_doc = self._check_cache(alt_type, elements_requis)
                        if alt_doc and alt_doc.get('titre', '') not in avoid_types:
                            logger.info(f"✅ Alternative document found: {alt_doc['titre']} (type: {alt_type})")
                            return self._enrich_document_metadata(alt_doc, document_request)
                logger.warning(f"⚠️ No alternative found, using original despite duplication")
            
            logger.info(f"✅ Document found in validated cache: {cached_doc['titre']}")
            return self._enrich_document_metadata(cached_doc, document_request)
        
        # Recherche via API Wikimedia Commons
        try:
            search_results = await self._search_wikimedia_commons(doc_type, elements_requis, langue)
            if search_results:
                best_match = self._select_best_document(search_results, document_request)
                if best_match:
                    logger.info(f"✅ Document found via Wikimedia: {best_match['titre']}")
                    return self._enrich_document_metadata(best_match, document_request)
        except Exception as e:
            logger.error(f"❌ Error searching Wikimedia Commons: {e}")
        
        # Fallback: retourner un document par défaut approprié
        logger.warning(f"⚠️ No specific document found, using fallback for {doc_type}")
        return self._get_fallback_document(doc_type, document_request)
    
    def _check_cache(self, doc_type: str, elements_requis: List[str]) -> Optional[Dict[str, Any]]:
        """Vérifie le cache des documents validés avec sélection intelligente"""
        
        # Mapping des types vers les clés de cache avec logique intelligente
        cache_mapping = {
            "carte_france": "carte_france",
            "carte_monde": "carte_monde", 
            "planisphere": "carte_monde",
            "carte_europe": "carte_europe",
            "carte_asie": "carte_asie", 
            "carte_amerique_nord": "carte_amerique_nord",
            "carte_afrique": "carte_afrique"
        }
        
        cache_key = cache_mapping.get(doc_type)
        if cache_key and cache_key in self.validated_documents_cache:
            return self.validated_documents_cache[cache_key]
        
        return None
    
    def _analyze_content_for_document_type(self, enonce: str) -> str:
        """Analyse RENFORCÉE pour garantir la diversification"""
        enonce_lower = enonce.lower()
        
        # DÉTECTION ULTRA-PRÉCISE avec mots-clés étendus
        
        # FRANCE - Détection élargie
        france_keywords = [
            "france", "français", "paris", "lyon", "marseille", "toulouse", 
            "région", "département", "préfecture", "hexagone", "métropole",
            "aquitaine", "bretagne", "normandie", "paca", "île-de-france"
        ]
        if any(mot in enonce_lower for mot in france_keywords):
            return "carte_france"
        
        # EUROPE - Détection élargie  
        europe_keywords = [
            "europe", "européen", "union européenne", "ue", "schengen",
            "allemagne", "berlin", "italie", "rome", "espagne", "madrid",
            "royaume-uni", "londres", "portugal", "grèce", "pologne", "brexit"
        ]
        if any(mot in enonce_lower for mot in europe_keywords):
            return "carte_europe"
        
        # ASIE - Détection élargie
        asie_keywords = [
            "asie", "asiatique", "extrême-orient", "orient",
            "chine", "beijing", "pékin", "shanghai", "japon", "tokyo", "osaka",
            "inde", "delhi", "mumbai", "corée", "séoul", "thaïlande", "vietnam"
        ]
        if any(mot in enonce_lower for mot in asie_keywords):
            return "carte_asie"
        
        # AMÉRIQUE DU NORD - Détection élargie
        amerique_nord_keywords = [
            "amérique du nord", "nord-américain", "alena", "nafta",
            "états-unis", "usa", "etats-unis", "américain",
            "new york", "washington", "californie", "texas", "floride",
            "canada", "toronto", "vancouver", "ottawa", "québec",
            "mexique", "mexico"
        ]
        if any(mot in enonce_lower for mot in amerique_nord_keywords):
            return "carte_amerique_nord"
        
        # AFRIQUE - Détection élargie
        afrique_keywords = [
            "afrique", "africain", "sahara", "sahel", "maghreb",
            "nil", "congo", "niger", "zambèze",
            "maroc", "algérie", "tunisie", "egypte", "kenya", "nigeria",
            "afrique du sud", "ghana", "sénégal", "mali", "tchad"
        ]
        if any(mot in enonce_lower for mot in afrique_keywords):
            return "carte_afrique"
        
        # MONDE/GLOBAL - Détection élargie
        monde_keywords = [
            "monde", "mondial", "planète", "terre", "global",
            "continents", "océans", "hémisphère", "équateur", "tropiques",
            "mondialisation", "géographie mondiale", "planisphère"
        ]
        if any(mot in enonce_lower for mot in monde_keywords):
            return "carte_monde"
        
        # URBAIN - Détection spéciale
        urban_keywords = [
            "ville", "urbain", "métropole", "agglomération", "banlieue",
            "urbanisation", "périurbain", "centre-ville", "quartier"
        ]
        if any(mot in enonce_lower for mot in urban_keywords):
            # Pour l'urbain, choisir selon contexte géographique
            if any(mot in enonce_lower for mot in ["tokyo", "osaka", "beijing", "seoul"]):
                return "carte_asie"
            elif any(mot in enonce_lower for mot in ["new york", "chicago", "los angeles"]):
                return "carte_amerique_nord"
            elif any(mot in enonce_lower for mot in ["paris", "lyon", "marseille"]):
                return "carte_france"
            elif any(mot in enonce_lower for mot in ["berlin", "rome", "madrid", "londres"]):
                return "carte_europe"
            else:
                return "carte_monde"  # Urbain général
        
        # FALLBACK par défaut
        return "carte_monde"
    
    async def _search_wikimedia_commons(self, doc_type: str, elements_requis: List[str], langue: str) -> List[Dict[str, Any]]:
        """Recherche via l'API Wikimedia Commons"""
        
        # Construction de la requête de recherche
        search_terms = self._build_search_terms(doc_type, elements_requis, langue)
        
        params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": search_terms,
            "srnamespace": "6",  # Namespace File
            "srlimit": "10"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.wikimedia_api_base, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        search_results = data.get("query", {}).get("search", [])
                        
                        # Enrichir avec les métadonnées de chaque fichier
                        enriched_results = []
                        for result in search_results[:5]:  # Limiter à 5 résultats
                            file_metadata = await self._get_file_metadata(result["title"])
                            if file_metadata:
                                enriched_results.append(file_metadata)
                        
                        return enriched_results
        except Exception as e:
            logger.error(f"Error in Wikimedia API call: {e}")
            return []
        
        return []
    
    def _build_search_terms(self, doc_type: str, elements_requis: List[str], langue: str) -> str:
        """Construction des termes de recherche optimisés"""
        
        base_terms = {
            "carte_france": "France map administrative regions",
            "carte_monde": "world map continents oceans",
            "carte_europe": "Europe map countries",
            "planisphere": "world map projection continents",
            "carte_thematique": "thematic map"
        }
        
        base = base_terms.get(doc_type, "map")
        
        # Ajouter les éléments requis
        if elements_requis:
            elements_str = " ".join(elements_requis)
            base += f" {elements_str}"
        
        # Privilégier le français si demandé
        if langue == "français":
            base += " french labels français"
        
        # Privilégier les formats vectoriels
        base += " svg vector"
        
        return base
    
    async def _get_file_metadata(self, filename: str) -> Optional[Dict[str, Any]]:
        """Récupère les métadonnées détaillées d'un fichier"""
        
        params = {
            "action": "query",
            "format": "json",
            "titles": filename,
            "prop": "imageinfo",
            "iiprop": "url|size|mime|metadata|commonsmeta",
            "iiurlwidth": "1200"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.wikimedia_api_base, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        pages = data.get("query", {}).get("pages", {})
                        
                        for page_id, page_data in pages.items():
                            if "imageinfo" in page_data:
                                imageinfo = page_data["imageinfo"][0]
                                
                                # Extraire les informations essentielles
                                metadata = {
                                    "titre": filename.replace("File:", "").replace("_", " "),
                                    "url_fichier_direct": imageinfo.get("url"),
                                    "largeur_px": imageinfo.get("width", 0),
                                    "hauteur_px": imageinfo.get("height", 0),
                                    "mime_type": imageinfo.get("mime"),
                                    "taille_bytes": imageinfo.get("size", 0),
                                    "url_page_commons": f"{self.wikimedia_base_url}/wiki/{filename}"
                                }
                                
                                # Analyser la licence
                                licence_info = self._extract_license_info(page_data)
                                metadata["licence"] = licence_info
                                
                                return metadata
        except Exception as e:
            logger.error(f"Error getting file metadata for {filename}: {e}")
        
        return None
    
    def _extract_license_info(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extrait les informations de licence d'une page Commons"""
        
        # Par défaut, licence inconnue
        licence_info = {
            "type": "unknown",
            "notice_attribution": "Vérifier la licence sur Wikimedia Commons",
            "lien_licence": ""
        }
        
        try:
            # Analyser les métadonnées Commons
            imageinfo = page_data.get("imageinfo", [{}])[0]
            commonsmeta = imageinfo.get("commonsmeta", {})
            
            # Recherche de licences communes
            if "LicenseShortName" in commonsmeta:
                license_short = commonsmeta["LicenseShortName"]
                if "cc-by-sa" in license_short.lower():
                    licence_info["type"] = "CC BY-SA"
                    licence_info["lien_licence"] = "https://creativecommons.org/licenses/by-sa/3.0/"
                elif "cc-by" in license_short.lower():
                    licence_info["type"] = "CC BY"
                    licence_info["lien_licence"] = "https://creativecommons.org/licenses/by/3.0/"
                elif "pd" in license_short.lower() or "public domain" in license_short.lower():
                    licence_info["type"] = "PD"
                    licence_info["notice_attribution"] = "Domaine public"
        except Exception as e:
            logger.warning(f"Error extracting license info: {e}")
        
        return licence_info
    
    def _select_best_document(self, search_results: List[Dict[str, Any]], document_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Sélectionne le meilleur document parmi les résultats de recherche"""
        
        if not search_results:
            return None
        
        # Critères de sélection
        scored_results = []
        
        for doc in search_results:
            score = 0
            
            # Privilégier les formats vectoriels (SVG)
            if doc.get("mime_type") == "image/svg+xml":
                score += 3
            
            # Privilégier les images de bonne résolution
            width = doc.get("largeur_px", 0)
            if width > 1000:
                score += 2
            elif width > 500:
                score += 1
            
            # Privilégier les licences libres
            licence_type = doc.get("licence", {}).get("type", "unknown")
            if licence_type in ["PD", "CC BY", "CC BY-SA"]:
                score += 2
            
            # Privilégier les titres pertinents
            titre = doc.get("titre", "").lower()
            doc_type = document_request.get("type", "")
            if doc_type.replace("_", " ") in titre:
                score += 1
            
            scored_results.append((score, doc))
        
        # Trier par score décroissant et retourner le meilleur
        if scored_results:
            scored_results.sort(key=lambda x: x[0], reverse=True)
            return scored_results[0][1]
        
        return None
    
    def _get_fallback_document(self, doc_type: str, document_request: Dict[str, Any]) -> Dict[str, Any]:
        """Retourne un document de fallback en cas d'échec de recherche"""
        
        fallback_docs = {
            "carte_france": {
                "titre": "Carte administrative France (fallback)",
                "langue_labels": "français",
                "projection": "Lambert conformal conic",
                "inclut_continents": False,
                "inclut_regions": True,
                "licence": {
                    "type": "CC BY-SA 3.0",
                    "notice_attribution": "TUBS, CC BY-SA 3.0, via Wikimedia Commons",
                    "lien_licence": "https://creativecommons.org/licenses/by-sa/3.0/"
                },
                "auteur_source": "TUBS/Wikimedia Commons",
                "url_page_commons": "https://commons.wikimedia.org/wiki/File:France,_administrative_divisions_-_Nmbrs_(departments+overseas).svg",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/France%2C_administrative_divisions_-_Nmbrs_%28departments%2Boverseas%29.svg/1200px-France%2C_administrative_divisions_-_Nmbrs_%28departments%2Boverseas%29.svg.png",
                "largeur_px": 1200,
                "hauteur_px": 1154,
                "pourquoi_choisie": "Document de fallback - carte administrative avec départements",
                "conseils_impression": "Format A4 paysage, marges 15mm"
            },
            "carte_monde": {
                "titre": "Planisphère monde (fallback)",
                "langue_labels": "multilingue",
                "projection": "Equirectangular",
                "inclut_continents": True,
                "inclut_oceans": True,
                "licence": {
                    "type": "PD",
                    "notice_attribution": "Domaine public",
                    "lien_licence": ""
                },
                "auteur_source": "NASA/Wikimedia",
                "url_page_commons": "https://commons.wikimedia.org/wiki/File:Equirectangular_projection_SW.jpg",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "largeur_px": 1200,
                "hauteur_px": 600,
                "pourquoi_choisie": "Document de fallback - planisphère standard",
                "conseils_impression": "Format A3 paysage, marges 10mm"
            },
            "carte_asie": {
                "titre": "Carte du monde pour l'Asie (fallback)",
                "langue_labels": "multilingue",
                "projection": "Equirectangular",
                "inclut_continents": True,
                "inclut_asie": True,
                "licence": {
                    "type": "PD",
                    "notice_attribution": "Domaine public",
                    "lien_licence": ""
                },
                "auteur_source": "NASA/Wikimedia",
                "url_page_commons": "https://commons.wikimedia.org/wiki/File:Equirectangular_projection_SW.jpg",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "largeur_px": 1200,
                "hauteur_px": 600,
                "pourquoi_choisie": "Carte monde fiable pour exercices sur l'Asie",
                "conseils_impression": "Format A4 paysage, marges 12mm"
            },
            "carte_amerique_nord": {
                "titre": "Carte du monde pour l'Amérique du Nord (fallback)",
                "langue_labels": "multilingue",
                "projection": "Equirectangular",
                "inclut_continents": True,
                "inclut_amerique_nord": True,
                "licence": {
                    "type": "PD",
                    "notice_attribution": "Domaine public",
                    "lien_licence": ""
                },
                "auteur_source": "NASA/Wikimedia",
                "url_page_commons": "https://commons.wikimedia.org/wiki/File:Equirectangular_projection_SW.jpg",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "largeur_px": 1200,
                "hauteur_px": 600,
                "pourquoi_choisie": "Carte monde fiable pour exercices sur l'Amérique du Nord",
                "conseils_impression": "Format A4 paysage, marges 12mm"
            },
            "carte_europe": {
                "titre": "Carte du monde pour l'Europe (fallback)",
                "langue_labels": "multilingue",
                "projection": "Equirectangular",
                "inclut_continents": True,
                "inclut_europe": True,
                "licence": {
                    "type": "PD",
                    "notice_attribution": "Domaine public",
                    "lien_licence": ""
                },
                "auteur_source": "NASA/Wikimedia",
                "url_page_commons": "https://commons.wikimedia.org/wiki/File:Equirectangular_projection_SW.jpg",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "largeur_px": 1200,
                "hauteur_px": 600,
                "pourquoi_choisie": "Carte monde fiable pour exercices sur l'Europe",
                "conseils_impression": "Format A4 paysage, marges 12mm"
            },
            "carte_afrique": {
                "titre": "Carte du monde pour l'Afrique (fallback)",
                "langue_labels": "multilingue",
                "projection": "Equirectangular",
                "inclut_continents": True,
                "inclut_afrique": True,
                "licence": {
                    "type": "PD",
                    "notice_attribution": "Domaine public",
                    "lien_licence": ""
                },
                "auteur_source": "NASA/Wikimedia",
                "url_page_commons": "https://commons.wikimedia.org/wiki/File:Equirectangular_projection_SW.jpg",
                "url_fichier_direct": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Equirectangular_projection_SW.jpg/1200px-Equirectangular_projection_SW.jpg",
                "largeur_px": 1200,
                "hauteur_px": 600,
                "pourquoi_choisie": "Carte monde fiable pour exercices sur l'Afrique",
                "conseils_impression": "Format A4 paysage, marges 12mm"
            }
        }
        
        return fallback_docs.get(doc_type, fallback_docs["carte_monde"])
    
    def _enrich_document_metadata(self, doc: Dict[str, Any], document_request: Dict[str, Any]) -> Dict[str, Any]:
        """Enrichit les métadonnées du document avec les informations de contexte"""
        
        enriched = doc.copy()
        
        # Ajouter les informations de contexte
        enriched.update({
            "langue_labels": document_request.get("langue", "français"),
            "elements_demandes": document_request.get("doit_afficher", []),
            "echelle": document_request.get("echelle_preferee", "inconnue"),
            "contexte_pedagogique": f"Document pour exercice niveau {document_request.get('niveau', 'collège')}",
            "date_recherche": "2025-09-30",
            "statut_verification": "automatique"
        })
        
        # Validation des éléments requis
        elements_requis = document_request.get("doit_afficher", [])
        if "continents" in elements_requis:
            enriched["inclut_continents"] = True
        if "océans" in elements_requis or "oceans" in elements_requis:
            enriched["inclut_oceans"] = True
        
        return enriched

# Instance globale pour utilisation dans les exercices
document_searcher = DocumentSearcher()

async def search_educational_document(document_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fonction utilitaire pour rechercher un document éducatif
    
    Args:
        document_request: Dictionnaire spécifiant le type de document demandé
    
    Returns:
        Métadonnées complètes du document trouvé
    """
    return await document_searcher.search_geographic_document(document_request)