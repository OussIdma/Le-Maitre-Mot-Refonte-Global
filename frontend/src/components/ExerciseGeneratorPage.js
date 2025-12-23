/**
 * ExerciseGeneratorPage - Générateur d'exercice (V2)
 * 
 * Migration vers le référentiel officiel:
 * - Charge le catalogue depuis /api/v1/curriculum/6e/catalog
 * - Toggle Mode Simple / Mode Standard (programme)
 * - Génère toujours via code_officiel
 * 
 * Mode Simple: chapitres macro regroupés (exercices guidés)
 * Mode Standard: chapitres officiels du programme (difficulté normale)
 */

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Switch } from "./ui/switch";
import { Label } from "./ui/label";
import { 
  BookOpen, 
  FileText, 
  Download, 
  Shuffle, 
  Loader2, 
  ChevronLeft, 
  ChevronRight,
  AlertCircle,
  CheckCircle,
  GraduationCap,
  Settings2,
  Layers,
  List,
  Crown
} from "lucide-react";
import MathRenderer from "./MathRenderer";
import { useToast } from "../hooks/use-toast";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "./ui/tooltip";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "./ui/collapsible";
import { Trash2, RefreshCw, Save, Check } from "lucide-react";
import PremiumUpsellModal from "./PremiumUpsellModal";
import UpgradeProModal, { trackPremiumEvent } from "./UpgradeProModal";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API_V1 = `${BACKEND_URL}/api/v1/exercises`;
const CATALOG_API = `${BACKEND_URL}/api/v1/curriculum`;

/**
 * MathHtmlRenderer - Composant pour rendre du HTML contenant du LaTeX
 */
const MathHtmlRenderer = ({ html, className = "" }) => {
  if (!html) {
    return null;
  }

  const renderMixedContent = (htmlContent) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');
    
    const processNode = (node, index = 0) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent;
        if (text && text.trim()) {
          const hasLatex = /\\(?:frac|sqrt|times|div|pm|cdot|leq|geq|neq|approx|[a-zA-Z]+)\{/.test(text) ||
                          /\^{[^}]+}/.test(text) ||
                          /_\{[^}]+\}/.test(text);
          
          if (hasLatex) {
            return <MathRenderer key={`math-${index}`} content={text} className="inline" />;
          }
          return <span key={`text-${index}`}>{text}</span>;
        }
        return null;
      }
      
      if (node.nodeType === Node.ELEMENT_NODE) {
        const tagName = node.tagName.toLowerCase();
        
        const rawHtmlElements = ['svg', 'table', 'img', 'br', 'hr'];
        if (rawHtmlElements.includes(tagName)) {
          return (
            <span 
              key={`html-${index}`} 
              dangerouslySetInnerHTML={{ __html: node.outerHTML }}
            />
          );
        }
        
        const children = Array.from(node.childNodes).map((child, i) => 
          processNode(child, index * 100 + i)
        ).filter(Boolean);
        
        const props = { key: `elem-${index}` };
        if (node.className) props.className = node.className;
        if (node.id) props.id = node.id;
        
        const reactTagMap = {
          'div': 'div', 'p': 'p', 'span': 'span', 'strong': 'strong', 'b': 'b',
          'em': 'em', 'i': 'i', 'ol': 'ol', 'ul': 'ul', 'li': 'li',
          'h1': 'h1', 'h2': 'h2', 'h3': 'h3', 'h4': 'h4', 'h5': 'h5', 'h6': 'h6',
          'a': 'a', 'sup': 'sup', 'sub': 'sub'
        };
        
        const ReactTag = reactTagMap[tagName] || 'span';
        return React.createElement(ReactTag, props, children.length > 0 ? children : null);
      }
      
      return null;
    };
    
    const bodyChildren = Array.from(doc.body.childNodes).map((node, i) => 
      processNode(node, i)
    ).filter(Boolean);
    
    return bodyChildren;
  };

  return (
    <div className={`math-html-renderer ${className}`}>
      {renderMixedContent(html)}
    </div>
  );
};

const ExerciseGeneratorPage = () => {
  const { toast } = useToast();
  
  // État du catalogue
  const [catalog, setCatalog] = useState(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  
  // Mode d'affichage: "simple" (macro) ou "officiel" (micro)
  // Standard (programme) = mode par défaut pour tous
  const [viewMode, setViewMode] = useState("officiel");
  
  // Sélecteur de niveau
  const [selectedGrade, setSelectedGrade] = useState("6e");
  
  // États pour le formulaire
  const [selectedItem, setSelectedItem] = useState(""); // code_officiel ou label macro
  const [selectedDomaine, setSelectedDomaine] = useState("all");
  const [batchSize, setBatchSize] = useState(5); // Nombre d'exercices par lot (défaut 5)
  const [difficulte, setDifficulte] = useState("moyen");
  
  // États pour la génération en lot
  const [isGeneratingBatch, setIsGeneratingBatch] = useState(false);
  const [error, setError] = useState(null);
  const [exercises, setExercises] = useState([]);
  const [batchSeed, setBatchSeed] = useState(null); // Seed de base pour le lot actuel
  
  // États pour les variations
  const [loadingVariation, setLoadingVariation] = useState(false);
  
  // Historique des codes utilisés (pour rotation)
  const [usedCodes, setUsedCodes] = useState([]);
  
  // États PRO - Détection de l'utilisateur premium
  const [isPro, setIsPro] = useState(false);
  const [userEmail, setUserEmail] = useState("");
  
  // État pour le seed de génération GM07 (pour reproductibilité des variations)
  const [gm07Seed, setGm07Seed] = useState(null);
  
  // État pour le warning batch (pool insuffisant)
  const [batchWarning, setBatchWarning] = useState(null);
  
  // P3.0: États pour la sauvegarde d'exercices
  const [savedExercises, setSavedExercises] = useState(new Set()); // Set d'exercise_uid sauvegardés
  const [savingExerciseId, setSavingExerciseId] = useState(null); // exercise_uid en cours de sauvegarde
  
  // État pour la modal Premium Upsell
  
  // Track premium badges viewed (P2.2)
  useEffect(() => {
    exercises.forEach((exercise, index) => {
      if (exercise.metadata?.premium_available && 
          !exercise.metadata?.is_premium && 
          !isPro) {
        trackPremiumEvent('premium_badge_viewed', {
          exercise_id: exercise.id_exercice,
          generator_key: exercise.metadata?.generator_key,
          index: index
        });
      }
    });
  }, [exercises, isPro]); // eslint-disable-line react-hooks/exhaustive-deps
  
  // Initialiser l'authentification PRO
  useEffect(() => {
    const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    if (storedSessionToken && storedEmail && loginMethod === 'session') {
      setUserEmail(storedEmail);
      setIsPro(true);
      console.log('🌟 Mode PRO activé:', storedEmail);
      
      // P3.0: Charger les exercices sauvegardés pour marquer ceux déjà sauvegardés
      loadSavedExercises(storedSessionToken);
    }
  }, []);
  
  // P3.0: Charger les exercices sauvegardés pour vérifier lesquels sont déjà sauvegardés
  const loadSavedExercises = async (sessionToken) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/user/exercises`, {
        headers: {
          'X-Session-Token': sessionToken
        }
      });
      
      const savedUids = new Set(response.data.exercises.map(ex => ex.exercise_uid));
      setSavedExercises(savedUids);
      console.log('📚 Exercices sauvegardés chargés:', savedUids.size);
    } catch (error) {
      console.error('Erreur chargement exercices sauvegardés:', error);
      // Ne pas bloquer si erreur
    }
  };
  
  // P3.0: Sauvegarder un exercice
  const handleSaveExercise = async (exercise) => {
    const sessionToken = localStorage.getItem('lemaitremot_session_token');
    
    if (!sessionToken) {
      toast({
        title: "Authentification requise",
        description: "Veuillez vous connecter pour sauvegarder un exercice",
        variant: "destructive"
      });
      return;
    }
    
    // Vérifier si déjà sauvegardé
    if (savedExercises.has(exercise.id_exercice)) {
      toast({
        title: "Déjà sauvegardé",
        description: "Cet exercice est déjà dans votre bibliothèque",
        variant: "default"
      });
      return;
    }
    
    setSavingExerciseId(exercise.id_exercice);
    
    try {
      // Préparer les données pour la sauvegarde
      const saveData = {
        exercise_uid: exercise.id_exercice,
        generator_key: exercise.metadata?.generator_key || null,
        code_officiel: exercise.metadata?.code_officiel || selectedItem,
        difficulty: exercise.metadata?.difficulte || difficulte,
        seed: exercise.metadata?.seed || null,
        variables: exercise.metadata?.variables || {},
        enonce_html: exercise.enonce_html,
        solution_html: exercise.solution_html,
        metadata: {
          niveau: exercise.niveau,
          chapitre: exercise.chapitre,
          ...exercise.metadata
        }
      };
      
      const response = await axios.post(
        `${BACKEND_URL}/api/user/exercises`,
        saveData,
        {
          headers: {
            'X-Session-Token': sessionToken
          }
        }
      );
      
      // Marquer comme sauvegardé
      setSavedExercises(prev => new Set([...prev, exercise.id_exercice]));
      
      toast({
        title: "✅ Exercice sauvegardé",
        description: "L'exercice a été ajouté à votre bibliothèque",
        variant: "default"
      });
      
    } catch (error) {
      console.error('Erreur sauvegarde exercice:', error);
      
      if (error.response?.status === 401) {
        toast({
          title: "Session expirée",
          description: "Veuillez vous reconnecter",
          variant: "destructive"
        });
      } else if (error.response?.status === 409) {
        // Déjà sauvegardé
        setSavedExercises(prev => new Set([...prev, exercise.id_exercice]));
        toast({
          title: "Déjà sauvegardé",
          description: "Cet exercice est déjà dans votre bibliothèque",
          variant: "default"
        });
      } else {
        toast({
          title: "Erreur",
          description: "Impossible de sauvegarder l'exercice",
          variant: "destructive"
        });
      }
    } finally {
      setSavingExerciseId(null);
    }
  };

  // Charger le catalogue au montage et quand le niveau change
  useEffect(() => {
    fetchCatalog();
  }, [selectedGrade]);

  const fetchCatalog = async () => {
    setCatalogLoading(true);
    try {
      const response = await axios.get(`${CATALOG_API}/${selectedGrade}/catalog`);
      setCatalog(response.data);
      console.log(`✅ Catalogue chargé pour ${selectedGrade}:`, response.data.total_chapters, 'chapitres,', response.data.total_macro_groups, 'groupes macro');
      
      // Reset la sélection de chapitre si le code_officiel n'existe plus dans le nouveau catalogue
      if (selectedItem && !selectedItem.startsWith("macro:")) {
        const codeExists = response.data.domains.some(domain =>
          domain.chapters.some(ch => ch.code_officiel === selectedItem)
        );
        if (!codeExists) {
          setSelectedItem("");
          console.log(`⚠️ Chapitre ${selectedItem} n'existe plus pour ${selectedGrade}, sélection réinitialisée`);
        }
      }
    } catch (error) {
      console.error("Erreur lors du chargement du catalogue:", error);
      
      // Gérer 404 pour grade non supporté
      if (error.response?.status === 404) {
        toast({
          title: "Niveau non disponible",
          description: `Le niveau ${selectedGrade} n'est pas encore disponible. Revenant au niveau précédent.`,
          variant: "destructive"
        });
        // Revenir au dernier grade valide (6e par défaut)
        setSelectedGrade("6e");
      } else {
        setError("Impossible de charger le catalogue");
        toast({
          title: "Erreur",
          description: "Impossible de charger le catalogue. Veuillez réessayer.",
          variant: "destructive"
        });
      }
    } finally {
      setCatalogLoading(false);
    }
  };

  // Obtenir les items à afficher selon le mode
  const getDisplayItems = useCallback(() => {
    if (!catalog) return [];
    
    if (viewMode === "simple") {
      // Mode macro: retourne les macro_groups
      return catalog.macro_groups
        .filter(mg => mg.status !== "hidden")
        .map(mg => ({
          value: `macro:${mg.label}`,
          label: mg.label,
          description: mg.description,
          codes: mg.codes_officiels,
          status: mg.status,
          hasGenerators: mg.total_generators > 0
        }));
    } else {
      // Mode Standard: retourne les chapitres
      let chapters = [];
      catalog.domains.forEach(domain => {
        domain.chapters.forEach(ch => {
          if (ch.status !== "hidden") {
            chapters.push({
              value: ch.code_officiel,
              label: ch.libelle,
              domain: domain.name,
              code: ch.code_officiel,
              status: ch.status,
              hasSvg: ch.has_svg,
              hasGenerators: ch.generators.length > 0
            });
          }
        });
      });
      
      // Filtrer par domaine si sélectionné
      if (selectedDomaine !== "all") {
        chapters = chapters.filter(ch => ch.domain === selectedDomaine);
      }
      
      return chapters;
    }
  }, [catalog, viewMode, selectedDomaine]);

  // Obtenir les domaines disponibles
  const getDomaines = useCallback(() => {
    if (!catalog) return [];
    return catalog.domains.map(d => d.name);
  }, [catalog]);

  // Reset quand le mode change
  useEffect(() => {
    setSelectedItem("");
    setSelectedDomaine("all");
    setExercises([]);
    setError(null);
    setBatchSeed(null);
  }, [viewMode]);

  // ========================================================================
  // Tracking Premium (P2.2)
  // ========================================================================
  const trackPremiumEvent = useCallback((eventName, metadata = {}) => {
    console.log(`🎯 Premium Event: ${eventName}`, metadata);
    // TODO: Intégrer avec système de tracking existant (analytics, Mixpanel, etc.)
    // Pour l'instant, simple console.log
  }, []);

  // P2.3: Upgrade Pro Modal state
  const [showUpgradeModal, setShowUpgradeModal] = useState(false);
  const [upgradeContext, setUpgradeContext] = useState('generator');

  // Handlers modal Premium
  const handleOpenPremiumModal = useCallback((context = 'generator') => {
    trackPremiumEvent('premium_cta_clicked', { context });
    setUpgradeContext(context);
    setShowUpgradeModal(true);
  }, []);


  // ========================================================================
  // Fin Tracking Premium
  // ========================================================================

  // Fonction pour choisir un code_officiel depuis un macro group (avec rotation)
  const selectCodeFromMacro = useCallback((codes) => {
    if (!codes || codes.length === 0) return null;
    
    // Filtrer les codes déjà utilisés récemment
    const availableCodes = codes.filter(code => !usedCodes.includes(code));
    
    // Si tous les codes ont été utilisés, reset et recommencer
    const codesToChooseFrom = availableCodes.length > 0 ? availableCodes : codes;
    
    // Choisir aléatoirement
    const selectedCode = codesToChooseFrom[Math.floor(Math.random() * codesToChooseFrom.length)];
    
    // Mémoriser le code utilisé (garder les 10 derniers)
    setUsedCodes(prev => {
      const newUsed = [...prev, selectedCode].slice(-10);
      return newUsed;
    });
    
    return selectedCode;
  }, [usedCodes]);

  // Générer un lot d'exercices (séquentiel)
  const generateExercises = async () => {
    if (!selectedItem) {
      setError("Veuillez sélectionner un chapitre");
      return;
    }

    setIsGeneratingBatch(true);
    setError(null);
    setExercises([]);
    setBatchWarning(null);
    
    // Initialiser le seed de base pour ce lot (ou réutiliser batchSeed si régénération)
    const baseSeed = batchSeed || Date.now();
    setBatchSeed(baseSeed);

    try {
      // Déterminer le code_officiel à utiliser
      let codeOfficiel;
      
      if (selectedItem.startsWith("macro:")) {
        // Mode macro: choisir un code parmi le groupe
        const macroLabel = selectedItem.replace("macro:", "");
        const macroGroup = catalog.macro_groups.find(mg => mg.label === macroLabel);
        
        if (!macroGroup || macroGroup.codes_officiels.length === 0) {
          throw new Error(`Groupe sans codes officiels`);
        }
        
        codeOfficiel = selectCodeFromMacro(macroGroup.codes_officiels);
        console.log(`📦 Mode Simple "${macroLabel}" → code sélectionné: ${codeOfficiel}`);
      } else {
        // Mode Standard: utiliser directement le code
        codeOfficiel = selectedItem;
        console.log(`📋 Mode Standard → code: ${codeOfficiel}`);
      }
      
      if (!codeOfficiel) {
        throw new Error("Impossible de déterminer le code officiel");
      }

      // ========================================================================
      // GM07 BATCH: Utiliser l'endpoint batch pour garantir l'unicité
      // ========================================================================
      if (codeOfficiel.toUpperCase() === "6E_GM07") {
        const seed = Date.now();
        setGm07Seed(seed);
        
        const batchPayload = {
          code_officiel: "6e_GM07",
          nb_exercices: batchSize,
          difficulte: difficulte,
          offer: isPro ? "pro" : "free",
          seed: baseSeed
        };
        
        console.log('🎯 GM07 Batch Request:', batchPayload);
        
        const response = await axios.post(`${API_V1}/generate/batch/gm07`, batchPayload);
        const { exercises: batchExercises, batch_metadata } = response.data;
        
        // Vérifier si on a reçu moins que demandé
        if (batch_metadata.warning) {
          setBatchWarning(batch_metadata.warning);
          console.log('⚠️ GM07 Warning:', batch_metadata.warning);
        }
        
        setExercises(batchExercises);
        console.log(`✅ GM07 Batch: ${batchExercises.length} exercices générés (demandés: ${batch_metadata.requested}, disponibles: ${batch_metadata.available})`);
        
        return; // Sortir ici pour GM07
      }

      // ========================================================================
      // GM08 BATCH: Utiliser l'endpoint batch pour garantir l'unicité
      // ========================================================================
      if (codeOfficiel.toUpperCase() === "6E_GM08") {
        const seed = Date.now();
        setGm07Seed(seed); // Réutiliser le state existant pour le seed
        
        const batchPayload = {
          code_officiel: "6e_GM08",
          nb_exercices: batchSize,
          difficulte: difficulte,
          offer: isPro ? "pro" : "free",
          seed: baseSeed
        };
        
        console.log('🎯 GM08 Batch Request:', batchPayload);
        
        const response = await axios.post(`${API_V1}/generate/batch/gm08`, batchPayload);
        const { exercises: batchExercises, batch_metadata } = response.data;
        
        // Vérifier si on a reçu moins que demandé
        if (batch_metadata.warning) {
          setBatchWarning(batch_metadata.warning);
          console.log('⚠️ GM08 Warning:', batch_metadata.warning);
        }
        
        setExercises(batchExercises);
        console.log(`✅ GM08 Batch: ${batchExercises.length} exercices générés (demandés: ${batch_metadata.requested}, disponibles: ${batch_metadata.available})`);
        
        return; // Sortir ici pour GM08
      }

      // ========================================================================
      // AUTRES CHAPITRES: Génération séquentielle (appels un par un)
      // ========================================================================
      const generatedExercises = [];
      
      for (let i = 0; i < batchSize; i++) {
        try {
          // Seed déterministe: baseSeed + i
          const seed = baseSeed + i;
          
          // Construire le payload avec offer: "pro" si utilisateur PRO
          const payload = {
            code_officiel: codeOfficiel,
            difficulte: difficulte,
            seed: seed
          };
          
          // Ajouter offer: "pro" pour les utilisateurs PRO
          if (isPro) {
            payload.offer = "pro";
            console.log(`🌟 Mode PRO activé pour ${codeOfficiel}`);
          }
          
          const response = await axios.post(`${API_V1}/generate`, payload);
          generatedExercises.push(response.data);
          console.log(`✅ Exercice ${i + 1}/${batchSize} généré`);
          
        } catch (error) {
          console.error(`Erreur lors de la génération de l'exercice ${i + 1}:`, error);
          
          // Gestion des erreurs 422 structurées
          if (error.response?.status === 422) {
            const data = error.response.data;
            const detail = data.detail || data;
            
            if (detail.error_code) {
              const errorCode = detail.error_code;
              const errorMessage = detail.message || "Erreur lors de la génération";
              const hint = detail.hint;
              
              // Messages spécifiques selon error_code
              let toastMessage = errorMessage;
              let toastHint = hint;
              
              if (errorCode === "POOL_EMPTY") {
                toastMessage = "Aucun exercice disponible";
                toastHint = toastHint || `Aucun exercice dynamique trouvé pour ce chapitre avec les critères demandés. Essayez une autre difficulté.`;
              } else if (errorCode === "PLACEHOLDER_UNRESOLVED") {
                toastMessage = "Placeholders non résolus";
                const missing = detail.context?.missing || [];
                const missingList = missing.slice(0, 3).join(", ");
                const moreCount = missing.length > 3 ? ` et ${missing.length - 3} autre(s)` : "";
                toastHint = toastHint || `Les placeholders suivants n'ont pas pu être résolus : ${missingList}${moreCount}.`;
              } else if (errorCode === "ADMIN_TEMPLATE_MISMATCH") {
                toastMessage = "Placeholders incompatibles avec le générateur";
                const missingSummary = detail.context?.missing_summary || [];
                const missingList = missingSummary.slice(0, 3).join(", ");
                const moreCount = missingSummary.length > 3 ? ` et ${missingSummary.length - 3} autre(s)` : "";
                toastHint = toastHint || `Les placeholders suivants ne peuvent pas être résolus : ${missingList}${moreCount}.`;
              }
              
              // Afficher toast et arrêter le batch
              toast({
                title: toastMessage,
                description: toastHint || "Veuillez réessayer avec d'autres paramètres.",
                variant: "destructive"
              });
              
              // Arrêter le batch proprement
              break;
            }
          }
          
          // Erreur réseau/500: toast générique et arrêter
          if (error.response?.status >= 500 || !error.response) {
            toast({
              title: "Erreur serveur",
              description: `Erreur lors de la génération de l'exercice ${i + 1}. Le batch a été interrompu.`,
              variant: "destructive"
            });
            break;
          }
        }
      }
      
      // Sauvegarder les exercices générés (même si partiel)
      if (generatedExercises.length > 0) {
        setExercises(generatedExercises);
        console.log(`✅ Lot généré: ${generatedExercises.length}/${batchSize} exercices via ${codeOfficiel} ${isPro ? '(PRO)' : '(FREE)'}`);
      } else {
        // Aucun exercice généré: erreur déjà toastée
        setError("Aucun exercice n'a pu être généré");
      }
      
    } catch (error) {
      console.error("Erreur lors de la génération:", error);
      
      // Gestion défensive des erreurs : supporter plusieurs formats
      let errorMessage = "Erreur lors de la génération des exercices";
      let errorCode = null;
      let hint = null;
      
      if (error.response?.data) {
        const data = error.response.data;
        const detail = data.detail || data;
        
        // Format FastAPI avec error_code structuré
        if (detail.error_code) {
          errorCode = detail.error_code;
          errorMessage = detail.message || errorMessage;
          hint = detail.hint;
          
          // Messages spécifiques selon error_code
          if (errorCode === "POOL_EMPTY") {
            errorMessage = "Aucun exercice disponible";
            hint = hint || `Aucun exercice dynamique trouvé pour ce chapitre avec les critères demandés. Essayez une autre difficulté.`;
          } else if (errorCode === "VARIANT_ID_NOT_FOUND") {
            errorMessage = "Variant d'exercice introuvable";
            hint = hint || `Le variant demandé n'existe pas pour cet exercice.`;
      } else if (errorCode === "PLACEHOLDER_UNRESOLVED") {
        errorMessage = "Placeholders non résolus";
        const missing = detail.context?.missing || [];
        const missingList = missing.slice(0, 3).join(", ");
        const moreCount = missing.length > 3 ? ` et ${missing.length - 3} autre(s)` : "";
        hint = hint || `Les placeholders suivants n'ont pas pu être résolus : ${missingList}${moreCount}. Voir la console pour les détails complets.`;
        
        // Logger les détails complets dans la console
        console.error("🔴 PLACEHOLDER_UNRESOLVED - Détails complets:", {
          error_code: errorCode,
          chapter_code: detail.context?.chapter_code,
          template_id: detail.context?.template_id,
          generator_key: detail.context?.generator_key,
          missing_placeholders: missing,
          expected_placeholders: detail.context?.expected_placeholders,
          provided_keys: detail.context?.provided_keys
        });
      } else if (errorCode === "ADMIN_TEMPLATE_MISMATCH") {
        errorMessage = "Placeholders incompatibles avec le générateur";
        const missingSummary = detail.context?.missing_summary || [];
        const missingList = missingSummary.slice(0, 3).join(", ");
        const moreCount = missingSummary.length > 3 ? ` et ${missingSummary.length - 3} autre(s)` : "";
        hint = hint || `Les placeholders suivants ne peuvent pas être résolus par le générateur : ${missingList}${moreCount}. Vérifiez que le générateur fournit toutes les variables nécessaires.`;
        
        // Logger les détails complets dans la console
        console.error("🔴 ADMIN_TEMPLATE_MISMATCH - Détails complets:", {
          error_code: errorCode,
          generator_key: detail.context?.generator_key,
          missing_summary: missingSummary,
          mismatches: detail.context?.mismatches,
          placeholders_expected: detail.context?.placeholders_expected
        });
      }
          
          // Afficher toast avec message spécifique
          toast({
            title: errorMessage,
            description: hint || "Veuillez réessayer avec d'autres paramètres.",
            variant: "destructive"
          });
        }
        // Format nouveau JSON-safe : {success: false, message, error_code, details}
        else if (data.message) {
          errorMessage = data.message;
        }
        // Format FastAPI legacy : {detail: {message, ...} ou {detail: "string"}
        else if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (data.detail && data.detail.message) {
            errorMessage = data.detail.message;
      } else {
            errorMessage = "Chapitre invalide ou non disponible";
          }
        }
        // Format autre
        else if (data.error) {
          errorMessage = typeof data.error === 'string' ? data.error : (data.error.message || JSON.stringify(data.error));
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      // Afficher toast générique si pas de toast spécifique déjà affiché
      if (!errorCode) {
        toast({
          title: "Erreur",
          description: errorMessage,
          variant: "destructive"
        });
      }
      
      setError(errorMessage);
    } finally {
      setIsGeneratingBatch(false);
    }
  };

  // Régénérer le lot avec les mêmes paramètres (nouveau seed)
  const regenerateBatch = async () => {
    if (!selectedItem) return;
    
    // Nouveau seed pour régénération
    const newBaseSeed = Date.now();
    setBatchSeed(newBaseSeed);
    
    // Réutiliser la même logique de génération (qui utilisera le nouveau seed)
    await generateExercises();
  };

  // Effacer le lot
  const clearBatch = () => {
    setExercises([]);
    setBatchSeed(null);
    setError(null);
    setBatchWarning(null);
  };

  // Générer une variation
  const generateVariation = async (index) => {
    if (!selectedItem) return;

    setLoadingVariation(true);
    setBatchWarning(null);
    
    try {
      // Même logique que generateExercises pour déterminer le code
      let codeOfficiel;
      
      if (selectedItem.startsWith("macro:")) {
        const macroLabel = selectedItem.replace("macro:", "");
        const macroGroup = catalog.macro_groups.find(mg => mg.label === macroLabel);
        codeOfficiel = selectCodeFromMacro(macroGroup?.codes_officiels || []);
      } else {
        codeOfficiel = selectedItem;
      }
      
      // ========================================================================
      // GM07 VARIATION: Relancer le batch avec un nouveau seed
      // ========================================================================
      if (codeOfficiel.toUpperCase() === "6E_GM07") {
        // Nouveau seed pour une nouvelle liste
        const newSeed = Date.now();
        setGm07Seed(newSeed);
        
        // Respecter le statut premium de l'exercice courant
        const currentExerciseForVariation = exercises[index];
        const isCurrentPremium = currentExerciseForVariation?.metadata?.is_premium === true;
        
        const batchPayload = {
          code_officiel: "6e_GM07",
          nb_exercices: exercises.length, // Même nombre que la liste actuelle
          difficulte: difficulte,
          offer: isCurrentPremium ? "pro" : (isPro ? "pro" : "free"),
          seed: newSeed
        };
        
        console.log('🔄 GM07 Variation Batch:', batchPayload);
        
        const response = await axios.post(`${API_V1}/generate/batch/gm07`, batchPayload);
        const { exercises: batchExercises, batch_metadata } = response.data;
        
        if (batch_metadata.warning) {
          setBatchWarning(batch_metadata.warning);
        }
        
        setExercises(batchExercises);
        console.log(`✅ GM07 Variation: ${batchExercises.length} nouveaux exercices générés`);
        
        return; // Sortir ici pour GM07
      }

      // ========================================================================
      // GM08 VARIATION: Relancer le batch avec un nouveau seed
      // ========================================================================
      if (codeOfficiel.toUpperCase() === "6E_GM08") {
        // Nouveau seed pour une nouvelle liste
        const newSeed = Date.now();
        setGm07Seed(newSeed);
        
        // Respecter le statut premium de l'exercice courant
        const currentExerciseForVariation = exercises[index];
        const isCurrentPremium = currentExerciseForVariation?.metadata?.is_premium === true;
        
        const batchPayload = {
          code_officiel: "6e_GM08",
          nb_exercices: exercises.length, // Même nombre que la liste actuelle
          difficulte: difficulte,
          offer: isCurrentPremium ? "pro" : (isPro ? "pro" : "free"),
          seed: newSeed
        };
        
        console.log('🔄 GM08 Variation Batch:', batchPayload);
        
        const response = await axios.post(`${API_V1}/generate/batch/gm08`, batchPayload);
        const { exercises: batchExercises, batch_metadata } = response.data;
        
        if (batch_metadata.warning) {
          setBatchWarning(batch_metadata.warning);
        }
        
        setExercises(batchExercises);
        console.log(`✅ GM08 Variation: ${batchExercises.length} nouveaux exercices générés`);
        
        return; // Sortir ici pour GM08
      }
      
      // ========================================================================
      // AUTRES CHAPITRES: Comportement existant (variation single)
      // ========================================================================
      // Seed déterministe et reproductible (utiliser crypto si disponible, sinon Math.random)
      let seed;
      if (window.crypto && window.crypto.getRandomValues) {
        const array = new Uint32Array(1);
        window.crypto.getRandomValues(array);
        seed = array[0];
      } else {
        // Fallback: utiliser timestamp + index pour un seed unique mais stable
        seed = Date.now() + index * 1000;
      }
      
      // IMPORTANT: Pour une variation, on doit respecter le type de l'exercice COURANT
      // Si l'exercice courant est PREMIUM, la variation doit aussi être PREMIUM
      const currentExerciseForVariation = exercises[index];
      const isCurrentPremium = currentExerciseForVariation?.metadata?.is_premium === true;
      
      // Construire le payload
      const payload = {
        code_officiel: codeOfficiel,
        difficulte: difficulte,
        seed: seed
      };
      
      // Si l'exercice courant est PREMIUM, la variation DOIT être PREMIUM aussi
      // Sinon, on utilise le statut PRO de l'utilisateur pour les nouvelles générations
      if (isCurrentPremium) {
        payload.offer = "pro";
        console.log('🔄 Variation PREMIUM demandée (exercice courant est PREMIUM), seed:', seed);
      } else if (isPro) {
        // Utilisateur PRO mais exercice standard → génération standard (pas de forçage PREMIUM)
        // On NE MET PAS offer: "pro" pour garder la cohérence avec l'exercice d'origine
        console.log('🔄 Variation STANDARD demandée (exercice courant est standard), seed:', seed);
      } else {
        console.log('🔄 Variation STANDARD demandée, seed:', seed);
      }
      
      const response = await axios.post(`${API_V1}/generate`, payload);
      
      const newExercises = [...exercises];
      newExercises[index] = response.data;
      setExercises(newExercises);
      
      console.log('✅ Variation générée via', codeOfficiel, isCurrentPremium ? '(PREMIUM)' : '(STANDARD)');
      
    } catch (error) {
      console.error("Erreur lors de la génération de variation:", error);
      
      // Parsing robuste de l'erreur backend
      let errorMessage = "Erreur lors de la génération de la variation";
      
      if (error.response?.data) {
        const data = error.response.data;
        
        // Format nouveau JSON-safe : {error_code, message, ...}
        if (data.message) {
          errorMessage = data.message;
        }
        // Format FastAPI legacy : {detail: {message, ...} ou {detail: "string"}
        else if (data.detail) {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (data.detail && data.detail.message) {
            errorMessage = data.detail.message;
          } else if (data.detail && typeof data.detail === 'object') {
            // Essayer d'extraire un message lisible
            errorMessage = JSON.stringify(data.detail);
          }
        }
        // Format autre
        else if (data.error) {
          errorMessage = typeof data.error === 'string' ? data.error : (data.error.message || JSON.stringify(data.error));
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
    } finally {
      setLoadingVariation(false);
    }
  };

  // Export PDF (placeholder - conservé pour compatibilité future)
  const downloadPDF = (exercise) => {
    alert(`Export PDF pour l'exercice ${exercise.id_exercice}\n\nFonctionnalité en cours d'implémentation...`);
  };

  const displayItems = getDisplayItems();
  const domaines = getDomaines();

  // Loading du catalogue
  if (catalogLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Chargement du référentiel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <GraduationCap className="h-10 w-10 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">Générateur d&apos;exercices</h1>
            {/* Badge PRO si utilisateur connecté */}
            {isPro && (
              <Badge className="ml-3 bg-purple-600 text-white hover:bg-purple-700">
                ⭐ PRO
              </Badge>
            )}
          </div>
          {/* Sélecteur de niveau */}
          <div className="mb-3 flex items-center justify-center gap-3">
            <label className="text-sm font-medium text-gray-700">Niveau :</label>
            <Select value={selectedGrade} onValueChange={setSelectedGrade}>
              <SelectTrigger className="w-24">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="6e">6e</SelectItem>
                <SelectItem value="5e">5e</SelectItem>
                <SelectItem value="4e">4e</SelectItem>
                <SelectItem value="3e">3e</SelectItem>
              </SelectContent>
            </Select>
            <Badge variant="outline" className="text-base px-4 py-1.5 border-blue-300 text-blue-700 bg-blue-50">
              Niveau : {selectedGrade}
            </Badge>
          </div>
          <p className="text-lg text-gray-600">
            {catalog?.total_chapters || 0} chapitres disponibles
            {isPro && <span className="text-purple-600 ml-2">• Générateurs premium activés</span>}
          </p>
        </div>

        {/* Formulaire de configuration */}
        <Card className="mb-8">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <BookOpen className="h-5 w-5" />
                  Configuration
                </CardTitle>
                <CardDescription>
                  Sélectionnez un chapitre pour générer vos exercices
                </CardDescription>
              </div>
              
              {/* Toggle Mode Simple / Standard - Standard accessible à tous */}
              <div className="flex flex-col items-end gap-2">
                <div className="flex items-center gap-3 bg-gray-100 px-4 py-2 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Layers className="h-4 w-4 text-gray-500" />
                    <Label htmlFor="view-mode" className="text-sm text-gray-600">Simple</Label>
                  </div>
                  <Switch
                    id="view-mode"
                    checked={viewMode === "officiel"}
                    onCheckedChange={(checked) => setViewMode(checked ? "officiel" : "simple")}
                  />
                  <div className="flex items-center gap-2">
                    <Label htmlFor="view-mode" className="text-sm text-gray-600 cursor-pointer">
                      Standard (programme)
                    </Label>
                    <List className="h-4 w-4 text-gray-500" />
                  </div>
                </div>
                {/* Textes explicatifs sous le toggle */}
                <div className="flex items-center gap-4 text-xs text-gray-500">
                  <span>Simple : exercices guidés</span>
                  <span className="text-gray-300">|</span>
                  <span>Standard : difficulté normale</span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              {/* Filtre par domaine (mode Standard uniquement) */}
              {viewMode === "officiel" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Domaine
                  </label>
                  <Select value={selectedDomaine} onValueChange={setSelectedDomaine}>
                    <SelectTrigger>
                      <SelectValue placeholder="Tous les domaines" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Tous les domaines</SelectItem>
                      {domaines.map((domaine) => (
                        <SelectItem key={domaine} value={domaine}>
                          {domaine}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Sélecteur de chapitre / groupe macro */}
              <div className={viewMode === "officiel" ? "md:col-span-1" : "md:col-span-2"}>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {viewMode === "simple" ? "Thème" : "Chapitre officiel"}
                </label>
                <Select value={selectedItem} onValueChange={setSelectedItem}>
                  <SelectTrigger>
                    <SelectValue placeholder={viewMode === "simple" ? "Choisir un thème" : "Choisir un chapitre"} />
                  </SelectTrigger>
                  <SelectContent>
                    {displayItems.map((item) => (
                      <SelectItem 
                        key={item.value} 
                        value={item.value}
                        disabled={!item.hasGenerators}
                      >
                        <div className="flex items-center gap-2">
                          <span>{item.label}</span>
                          {item.hasSvg && (
                            <Badge variant="outline" className="text-xs">SVG</Badge>
                          )}
                          {item.status === "beta" && (
                            <Badge variant="secondary" className="text-xs">beta</Badge>
                          )}
                          {!item.hasGenerators && (
                            <Badge variant="destructive" className="text-xs">indispo</Badge>
                          )}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {/* Difficulté */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Difficulté
                </label>
                <Select value={difficulte} onValueChange={setDifficulte}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="facile">Facile</SelectItem>
                    <SelectItem value="moyen">Moyen</SelectItem>
                    <SelectItem value="difficile">Difficile</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Nombre d'exercices (batch size) */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre d&apos;exercices
                </label>
                <Select 
                  value={batchSize.toString()} 
                  onValueChange={(val) => setBatchSize(parseInt(val))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="3">3 exercices</SelectItem>
                    <SelectItem value="5">5 exercices</SelectItem>
                    <SelectItem value="10">10 exercices</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Info sur le mode sélectionné */}
            {selectedItem && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg text-sm text-blue-800">
                {selectedItem.startsWith("macro:") ? (
                  <>
                    <Settings2 className="h-4 w-4 inline mr-2" />
                    <strong>Mode Simple :</strong> Un chapitre sera sélectionné automatiquement parmi le groupe (exercices guidés)
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 inline mr-2" />
                    <strong>Mode Standard :</strong> Code officiel {selectedItem} (difficulté normale)
                  </>
                )}
              </div>
            )}

            {/* Boutons d'action */}
            <div className="flex gap-2">
              <Button 
                onClick={generateExercises}
                disabled={!selectedItem || isGeneratingBatch}
                className="flex-1"
                size="lg"
              >
                {isGeneratingBatch ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Génération en cours...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-4 w-4" />
                    Générer le lot ({batchSize})
                  </>
                )}
              </Button>
              
              {exercises.length > 0 && (
                <>
                  <Button 
                    onClick={regenerateBatch}
                    disabled={isGeneratingBatch}
                    variant="outline"
                    size="lg"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Régénérer
                  </Button>
                  <Button 
                    onClick={clearBatch}
                    disabled={isGeneratingBatch}
                    variant="outline"
                    size="lg"
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Effacer
                  </Button>
                </>
              )}
            </div>

            {isGeneratingBatch && (
              <div className="flex items-center justify-center mt-4 p-4 bg-blue-50 rounded-lg">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600 mr-3" />
                <span className="text-blue-800">
                  Génération du lot de {batchSize} exercice{batchSize > 1 ? 's' : ''} en cours...
                </span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Messages d'erreur */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Warning batch GM07 (pool insuffisant) */}
        {batchWarning && (
          <Alert className="mb-6 border-amber-300 bg-amber-50">
            <AlertCircle className="h-4 w-4 text-amber-600" />
            <AlertDescription className="text-amber-800">
              <strong>Information :</strong> {batchWarning}
            </AlertDescription>
          </Alert>
        )}

        {/* Affichage du lot d'exercices */}
        {exercises.length > 0 && (
          <div className="space-y-6">
            {/* Header du lot */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Lot de {exercises.length} exercice{exercises.length > 1 ? 's' : ''}
                  </CardTitle>
                  {isGeneratingBatch && (
                    <Badge variant="secondary" className="flex items-center gap-2">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Génération en cours...
                    </Badge>
                  )}
                </div>
              </CardHeader>
            </Card>

            {/* Liste des exercices */}
            {exercises.map((exercise, index) => (
              <Card key={exercise.id_exercice || `exercise-${index}`}>
                <CardContent className="pt-6">
                  {/* Header de l'exercice */}
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <Badge variant="secondary" className="px-3 py-1 text-base">
                        Exercice {index + 1}
                      </Badge>
                      <Badge>{exercise.niveau}</Badge>
                      <Badge variant="outline">{exercise.chapitre}</Badge>
                      {exercise.metadata?.difficulte && (
                        <Badge variant="secondary">{exercise.metadata.difficulte}</Badge>
                      )}
                      {exercise.metadata?.is_premium && (
                        <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100 border border-purple-300">
                          ⭐ PREMIUM
                        </Badge>
                      )}
                    </div>
                    
                    {/* P3.0: Bouton Sauvegarder */}
                    {isPro && (
                      <Button
                        onClick={() => handleSaveExercise(exercise)}
                        disabled={savingExerciseId === exercise.id_exercice || savedExercises.has(exercise.id_exercice)}
                        variant={savedExercises.has(exercise.id_exercice) ? "outline" : "default"}
                        size="sm"
                        className={savedExercises.has(exercise.id_exercice) ? "border-green-300 text-green-700" : ""}
                      >
                        {savingExerciseId === exercise.id_exercice ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Sauvegarde...
                          </>
                        ) : savedExercises.has(exercise.id_exercice) ? (
                          <>
                            <Check className="mr-2 h-4 w-4" />
                            Sauvegardé ✅
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 h-4 w-4" />
                            Sauvegarder
                          </>
                        )}
                      </Button>
                    )}
                  </div>

                  {/* Figure SVG Énoncé (nouvelle API ou compatibilité) */}
                  {(exercise.figure_svg_enonce || exercise.figure_svg) && (
                    <div className="mb-6">
                      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-900">
                        <svg className="h-4 w-4 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                          <circle cx="8.5" cy="8.5" r="1.5"/>
                          <polyline points="21 15 16 10 5 21"/>
                        </svg>
                        Figure
                      </h3>
                      <div 
                        className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm flex justify-center"
                        dangerouslySetInnerHTML={{ __html: exercise.figure_svg_enonce || exercise.figure_svg }}
                        style={{ maxWidth: '100%', overflow: 'hidden' }}
                      />
                    </div>
                  )}

                  {/* Énoncé */}
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-900">
                      <FileText className="h-4 w-4 text-blue-600" />
                      Énoncé
                    </h3>
                    <div className="prose prose-lg max-w-none bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                      <div className="text-base leading-relaxed text-gray-800 space-y-3">
                        <MathHtmlRenderer html={exercise.enonce_html} />
                      </div>
                    </div>
                  </div>

                  {/* Solution (repliable par défaut) */}
                  <Collapsible>
                    <CollapsibleTrigger className="w-full bg-green-50 p-4 rounded-lg border border-green-200 shadow-sm hover:bg-green-100 transition-colors">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 font-semibold text-green-900">
                          <CheckCircle className="h-4 w-4 text-green-600" />
                          Voir la correction
                        </div>
                        <ChevronRight className="h-4 w-4 text-green-600" />
                      </div>
                    </CollapsibleTrigger>
                    <CollapsibleContent className="mt-4">
                      <div className="bg-green-50 p-6 rounded-lg border border-green-200 shadow-sm">
                        {/* Figure SVG Solution (si présente) */}
                        {exercise.figure_svg_solution && (
                          <div className="mb-6">
                            <h4 className="text-base font-medium text-green-800 mb-3 flex items-center gap-2">
                              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                <circle cx="8.5" cy="8.5" r="1.5"/>
                                <polyline points="21 15 16 10 5 21"/>
                              </svg>
                              Figure corrigée
                            </h4>
                            <div 
                              className="bg-white p-4 rounded-lg border border-green-200 flex justify-center"
                              dangerouslySetInnerHTML={{ __html: exercise.figure_svg_solution }}
                              style={{ maxWidth: '100%', overflow: 'hidden' }}
                            />
                          </div>
                        )}
                        
                        <div className="prose prose-lg max-w-none">
                          <div className="text-base leading-relaxed text-gray-800 space-y-3">
                            <MathHtmlRenderer html={exercise.solution_html} />
                          </div>
                        </div>
                      </div>
                    </CollapsibleContent>
                  </Collapsible>

                  {/* ========================================================================
                      P2.2 - Badge Premium + CTA contextuel
                      Afficher UNIQUEMENT si :
                      - premium_available === true
                      - is_premium === false (exercice gratuit)
                      - isPro === false (utilisateur non Pro)
                      ======================================================================== */}
                  {exercise.metadata?.premium_available && 
                   !exercise.metadata?.is_premium && 
                   !isPro && (
                    <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
                      <div className="flex items-start gap-3">
                        <div className="mt-1 flex-shrink-0">
                          <Crown className="h-5 w-5 text-purple-600" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100 border border-purple-300">
                              💎 Version Premium disponible
                            </Badge>
                          </div>
                          <p className="text-sm text-gray-700 mb-3">
                            {exercise.metadata?.hint || "Certaines variantes avancées sont disponibles en version Pro."}
                          </p>
                          <Button
                            onClick={handleOpenPremiumModal}
                            variant="outline"
                            size="sm"
                            className="border-purple-300 text-purple-700 hover:bg-purple-100"
                          >
                            <Crown className="mr-2 h-4 w-4" />
                            Débloquer en Pro
                          </Button>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Message si aucun exercice */}
        {!isGeneratingBatch && exercises.length === 0 && !error && (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg">
                Sélectionnez un {viewMode === "simple" ? "thème" : "chapitre"}, puis cliquez sur Générer pour commencer
              </p>
              <p className="text-sm mt-2 text-gray-400">
                {viewMode === "simple" 
                  ? "Le mode Simple regroupe les chapitres par thème (exercices guidés)" 
                  : "Le mode Standard affiche les chapitres du programme (difficulté normale)"
                }
              </p>
            </CardContent>
          </Card>
        )}

        {/* P2.3 - Modal Upgrade Pro */}
        <UpgradeProModal
          isOpen={showUpgradeModal}
          onClose={() => setShowUpgradeModal(false)}
          context={upgradeContext}
        />
      </div>
    </div>
  );
};

export default ExerciseGeneratorPage;
