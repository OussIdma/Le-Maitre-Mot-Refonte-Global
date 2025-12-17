/**
 * ExerciseGeneratorPage - Générateur d'exercice (V2)
 * 
 * Migration vers le référentiel officiel:
 * - Charge le catalogue depuis /api/v1/curriculum/6e/catalog
 * - Toggle Mode Simple / Mode Officiel
 * - Génère toujours via code_officiel
 * 
 * Mode Simple: chapitres macro regroupés
 * Mode Officiel: 27 chapitres officiels du programme
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
  List
} from "lucide-react";
import MathRenderer from "./MathRenderer";

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
  // État du catalogue
  const [catalog, setCatalog] = useState(null);
  const [catalogLoading, setCatalogLoading] = useState(true);
  
  // Mode d'affichage: "simple" (macro) ou "officiel" (micro)
  const [viewMode, setViewMode] = useState("simple");
  
  // États pour le formulaire
  const [selectedItem, setSelectedItem] = useState(""); // code_officiel ou label macro
  const [selectedDomaine, setSelectedDomaine] = useState("all");
  const [nbExercices, setNbExercices] = useState(1);
  const [difficulte, setDifficulte] = useState("moyen");
  
  // États pour la génération
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [exercises, setExercises] = useState([]);
  
  // États pour la pagination
  const [currentIndex, setCurrentIndex] = useState(0);
  
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
  
  // Initialiser l'authentification PRO
  useEffect(() => {
    const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    if (storedSessionToken && storedEmail && loginMethod === 'session') {
      setUserEmail(storedEmail);
      setIsPro(true);
      console.log('🌟 Mode PRO activé:', storedEmail);
    }
  }, []);

  // Charger le catalogue au montage
  useEffect(() => {
    fetchCatalog();
  }, []);

  const fetchCatalog = async () => {
    setCatalogLoading(true);
    try {
      const response = await axios.get(`${CATALOG_API}/6e/catalog`);
      setCatalog(response.data);
      console.log('✅ Catalogue chargé:', response.data.total_chapters, 'chapitres,', response.data.total_macro_groups, 'groupes macro');
    } catch (error) {
      console.error("Erreur lors du chargement du catalogue:", error);
      setError("Impossible de charger le catalogue");
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
      // Mode officiel: retourne les chapitres
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
    setCurrentIndex(0);
    setError(null);
  }, [viewMode]);

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

  // Générer les exercices
  const generateExercises = async () => {
    if (!selectedItem) {
      setError("Veuillez sélectionner un chapitre");
      return;
    }

    setLoading(true);
    setError(null);
    setExercises([]);
    setCurrentIndex(0);
    setBatchWarning(null);

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
        console.log(`📦 Mode macro "${macroLabel}" → code sélectionné: ${codeOfficiel}`);
      } else {
        // Mode officiel: utiliser directement le code
        codeOfficiel = selectedItem;
        console.log(`📋 Mode officiel → code: ${codeOfficiel}`);
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
          nb_exercices: nbExercices,
          difficulte: difficulte,
          offer: isPro ? "pro" : "free",
          seed: seed
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
          nb_exercices: nbExercices,
          difficulte: difficulte,
          offer: isPro ? "pro" : "free",
          seed: seed
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
      // AUTRES CHAPITRES: Comportement existant (appels parallèles)
      // ========================================================================
      const promises = [];
      for (let i = 0; i < nbExercices; i++) {
        const seed = Date.now() + i;
        
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
        
        const promise = axios.post(`${API_V1}/generate`, payload);
        
        promises.push(promise);
      }

      const responses = await Promise.all(promises);
      const generatedExercises = responses.map(response => response.data);
      
      setExercises(generatedExercises);
      console.log('✅ Exercices générés:', generatedExercises.length, 'via', codeOfficiel, isPro ? '(PRO)' : '(FREE)');
      
    } catch (error) {
      console.error("Erreur lors de la génération:", error);
      
      if (error.response?.status === 422) {
        const detail = error.response.data.detail;
        setError(detail.message || "Chapitre invalide ou non disponible");
      } else {
        setError(error.message || "Erreur lors de la génération des exercices");
      }
    } finally {
      setLoading(false);
    }
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
      const seed = Date.now() + Math.random() * 1000;
      
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
        console.log('🔄 Variation PREMIUM demandée (exercice courant est PREMIUM)');
      } else if (isPro) {
        // Utilisateur PRO mais exercice standard → génération standard (pas de forçage PREMIUM)
        // On NE MET PAS offer: "pro" pour garder la cohérence avec l'exercice d'origine
        console.log('🔄 Variation STANDARD demandée (exercice courant est standard)');
      }
      
      const response = await axios.post(`${API_V1}/generate`, payload);
      
      const newExercises = [...exercises];
      newExercises[index] = response.data;
      setExercises(newExercises);
      
      console.log('✅ Variation générée via', codeOfficiel, isCurrentPremium ? '(PREMIUM)' : '(STANDARD)');
      
    } catch (error) {
      console.error("Erreur lors de la génération de variation:", error);
      setError("Erreur lors de la génération de la variation");
    } finally {
      setLoadingVariation(false);
    }
  };

  // Navigation
  const goToPrevious = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const goToNext = () => {
    if (currentIndex < exercises.length - 1) setCurrentIndex(currentIndex + 1);
  };

  // Export PDF (placeholder)
  const downloadPDF = (exercise) => {
    alert(`Export PDF pour l'exercice ${exercise.id_exercice}\n\nFonctionnalité en cours d'implémentation...`);
  };

  const currentExercise = exercises[currentIndex];
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
          <p className="text-lg text-gray-600">
            Programme officiel de 6e • {catalog?.total_chapters || 0} chapitres disponibles
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
              
              {/* Toggle Mode Simple / Officiel */}
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
                  <Label htmlFor="view-mode" className="text-sm text-gray-600">Officiel</Label>
                  <List className="h-4 w-4 text-gray-500" />
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              {/* Filtre par domaine (mode officiel uniquement) */}
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

              {/* Nombre d'exercices */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nombre
                </label>
                <Select 
                  value={nbExercices.toString()} 
                  onValueChange={(val) => setNbExercices(parseInt(val))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 exercice</SelectItem>
                    <SelectItem value="3">3 exercices</SelectItem>
                    <SelectItem value="5">5 exercices</SelectItem>
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
                    <strong>Mode simple :</strong> Un chapitre sera sélectionné automatiquement parmi le groupe
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4 inline mr-2" />
                    <strong>Code officiel :</strong> {selectedItem}
                  </>
                )}
              </div>
            )}

            {/* Bouton Générer */}
            <Button 
              onClick={generateExercises}
              disabled={!selectedItem || loading}
              className="w-full"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Génération en cours...
                </>
              ) : (
                <>
                  <FileText className="mr-2 h-4 w-4" />
                  Générer {nbExercices} exercice{nbExercices > 1 ? 's' : ''}
                </>
              )}
            </Button>

            {loading && (
              <div className="flex items-center justify-center mt-4 p-4 bg-blue-50 rounded-lg">
                <Loader2 className="h-5 w-5 animate-spin text-blue-600 mr-3" />
                <span className="text-blue-800">
                  Génération de {nbExercices} exercice{nbExercices > 1 ? 's' : ''} en cours...
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

        {/* Affichage des exercices */}
        {exercises.length > 0 && currentExercise && (
          <div className="space-y-6">
            <Card>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-4">
                  {/* Pagination */}
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={goToPrevious}
                      disabled={currentIndex === 0}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    
                    <Badge variant="secondary" className="px-4 py-2">
                      Exercice {currentIndex + 1} / {exercises.length}
                    </Badge>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={goToNext}
                      disabled={currentIndex === exercises.length - 1}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => generateVariation(currentIndex)}
                      disabled={loadingVariation}
                    >
                      {loadingVariation ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Shuffle className="h-4 w-4" />
                      )}
                      <span className="ml-2">Variation</span>
                    </Button>
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => downloadPDF(currentExercise)}
                      disabled={true}
                      className="opacity-60 cursor-not-allowed"
                      title="Export PDF bientôt disponible"
                    >
                      <Download className="h-4 w-4" />
                      <span className="ml-2">PDF (bientôt)</span>
                    </Button>
                  </div>
                </div>

                {/* Informations de l'exercice */}
                <div className="flex flex-wrap gap-2 mb-4">
                  <Badge>{currentExercise.niveau}</Badge>
                  <Badge variant="outline">{currentExercise.chapitre}</Badge>
                  {currentExercise.metadata?.difficulte && (
                    <Badge variant="secondary">{currentExercise.metadata.difficulte}</Badge>
                  )}
                  {/* Badge PREMIUM si l'exercice est généré en mode PRO */}
                  {currentExercise.metadata?.is_premium && (
                    <Badge className="bg-purple-100 text-purple-800 hover:bg-purple-100 border border-purple-300">
                      ⭐ PREMIUM
                    </Badge>
                  )}
                  {currentExercise.metadata?.is_fallback === false ? (
                    <Badge className="bg-green-100 text-green-800 hover:bg-green-100">
                      ✓ Générateur dédié
                    </Badge>
                  ) : currentExercise.metadata?.is_fallback === true ? (
                    <Badge className="bg-amber-100 text-amber-800 hover:bg-amber-100">
                      ⚠ Exercice générique (beta)
                    </Badge>
                  ) : null}
                  {currentExercise.metadata?.generator_code && (
                    <Badge 
                      variant="outline" 
                      className="text-xs text-gray-500"
                      title={`Code: ${currentExercise.metadata.generator_code}`}
                    >
                      {currentExercise.metadata.generator_code}
                    </Badge>
                  )}
                </div>

                {/* Figure SVG Énoncé (nouvelle API ou compatibilité) */}
                {(currentExercise.figure_svg_enonce || currentExercise.figure_svg) && (
                  <div className="mb-6">
                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                      <svg className="h-5 w-5 text-blue-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                        <circle cx="8.5" cy="8.5" r="1.5"/>
                        <polyline points="21 15 16 10 5 21"/>
                      </svg>
                      Figure
                    </h3>
                    <div 
                      className="bg-white p-4 rounded-lg border flex justify-center"
                      dangerouslySetInnerHTML={{ __html: currentExercise.figure_svg_enonce || currentExercise.figure_svg }}
                      style={{ maxWidth: '100%', overflow: 'hidden' }}
                    />
                  </div>
                )}

                {/* Énoncé */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                    <FileText className="h-5 w-5" />
                    Énoncé
                  </h3>
                  <div className="prose max-w-none bg-white p-4 rounded-lg border">
                    <MathHtmlRenderer html={currentExercise.enonce_html} />
                  </div>
                </div>

                {/* Solution */}
                <details className="bg-green-50 p-4 rounded-lg border border-green-200">
                  <summary className="cursor-pointer font-semibold text-green-900 flex items-center gap-2">
                    <CheckCircle className="h-5 w-5" />
                    Voir la correction
                  </summary>
                  
                  {/* Figure SVG Solution (si présente) */}
                  {currentExercise.figure_svg_solution && (
                    <div className="mt-4 mb-4">
                      <h4 className="text-sm font-medium text-green-800 mb-2 flex items-center gap-2">
                        <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                          <circle cx="8.5" cy="8.5" r="1.5"/>
                          <polyline points="21 15 16 10 5 21"/>
                        </svg>
                        Figure corrigée
                      </h4>
                      <div 
                        className="bg-white p-4 rounded-lg border border-green-200 flex justify-center"
                        dangerouslySetInnerHTML={{ __html: currentExercise.figure_svg_solution }}
                        style={{ maxWidth: '100%', overflow: 'hidden' }}
                      />
                    </div>
                  )}
                  
                  <div className="mt-4 prose max-w-none">
                    <MathHtmlRenderer html={currentExercise.solution_html} />
                  </div>
                </details>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Message si aucun exercice */}
        {!loading && exercises.length === 0 && !error && (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p className="text-lg">
                Sélectionnez un {viewMode === "simple" ? "thème" : "chapitre"}, puis cliquez sur Générer pour commencer
              </p>
              <p className="text-sm mt-2 text-gray-400">
                {viewMode === "simple" 
                  ? "Le mode simple regroupe les chapitres par thème" 
                  : "Le mode officiel affiche les 28 chapitres du programme"
                }
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default ExerciseGeneratorPage;
