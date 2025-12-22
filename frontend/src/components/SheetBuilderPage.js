import React, { useState, useEffect } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import Header from "./Header";
import SheetPreviewModal from "./SheetPreviewModal";
import PdfDownloadModal from "./PdfDownloadModal";
import ProExportModal from "./ProExportModal";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Separator } from "./ui/separator";
import { 
  BookOpen, 
  Plus, 
  Trash2, 
  Download, 
  Eye, 
  Loader2, 
  ChevronUp, 
  ChevronDown,
  Crown,
  AlertCircle,
  Sparkles,
  FileText
} from "lucide-react";
import { Switch } from "./ui/switch";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SheetBuilderPage() {
  // Router hooks
  const { sheetId: urlSheetId } = useParams();
  const navigate = useNavigate();
  
  // États pour le catalogue
  const [levels, setLevels] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState("");
  const [chapters, setChapters] = useState([]);
  const [selectedChapter, setSelectedChapter] = useState("");
  const [exercises, setExercises] = useState([]);
  const [loadingCatalogue, setLoadingCatalogue] = useState(false);
  
  // États pour la fiche (panier)
  const [sheetTitle, setSheetTitle] = useState("Nouvelle fiche d'exercices");
  const [sheetItems, setSheetItems] = useState([]);
  const [isLoadingSheet, setIsLoadingSheet] = useState(false);
  
  // États pour l'utilisateur et Pro
  const [userEmail, setUserEmail] = useState("");
  const [isPro, setIsPro] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  
  // États pour génération/export
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [sheetId, setSheetId] = useState(urlSheetId || null);
  
  // États pour le modal de preview
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  
  // États pour le modal de téléchargement PDF
  const [showPdfModal, setShowPdfModal] = useState(false);
  const [pdfResult, setPdfResult] = useState(null);
  
  // États pour le modal d'export Pro
  const [showProExportModal, setShowProExportModal] = useState(false);
  
  // États pour filtres
  const [selectedDomain, setSelectedDomain] = useState("");
  const [selectedGeneratorKind, setSelectedGeneratorKind] = useState("");
  const [availableDomains, setAvailableDomains] = useState([]);

  // Initialiser l'authentification
  useEffect(() => {
    const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    if (storedSessionToken && storedEmail && loginMethod === 'session') {
      setSessionToken(storedSessionToken);
      setUserEmail(storedEmail);
      setIsPro(true);
      console.log('✅ Session Pro détectée:', storedEmail);
    }
  }, []);

  // Charger une fiche existante depuis l'URL
  useEffect(() => {
    if (urlSheetId) {
      loadExistingSheet(urlSheetId);
    }
  }, [urlSheetId]);

  // Charger les niveaux au montage
  useEffect(() => {
    loadLevels();
  }, []);

  // Charger les chapitres quand le niveau change
  useEffect(() => {
    if (selectedLevel) {
      loadChapters(selectedLevel);
    }
  }, [selectedLevel]);

  // Charger les exercices quand le chapitre change
  useEffect(() => {
    if (selectedLevel && selectedChapter) {
      loadExercises(selectedLevel, selectedChapter);
    }
  }, [selectedLevel, selectedChapter, selectedDomain, selectedGeneratorKind]);

  const loadLevels = async () => {
    try {
      const response = await axios.get(`${API}/catalogue/levels`);
      setLevels(response.data);
      console.log('📚 Niveaux chargés:', response.data);
    } catch (error) {
      console.error('Erreur chargement niveaux:', error);
    }
  };

  const loadChapters = async (niveau) => {
    try {
      setLoadingCatalogue(true);
      const response = await axios.get(`${API}/catalogue/levels/${niveau}/chapters`);
      const chaptersData = response.data;
      setChapters(chaptersData);
      console.log('📖 Chapitres chargés pour', niveau, ':', chaptersData.length);
      
      // Charger les domaines disponibles depuis les chapitres
      const domains = [...new Set(chaptersData.map(ch => ch.domaine).filter(Boolean))];
      setAvailableDomains(domains);
      console.log('📐 Domaines disponibles pour', niveau, ':', domains);
    } catch (error) {
      console.error('Erreur chargement chapitres:', error);
      setAvailableDomains([]);
    } finally {
      setLoadingCatalogue(false);
    }
  };

  const loadExercises = async (niveau, chapterCodeOrId) => {
    try {
      setLoadingCatalogue(true);
      
      // Utiliser le nouvel endpoint dédié chapter_code si disponible
      // Le chapter_code suit le format : niveau_DXXXX (ex: 6e_G07, 4e_N02)
      const isChapterCode = chapterCodeOrId && chapterCodeOrId.includes('_');
      
      let url;
      if (isChapterCode) {
        // Nouveau système : utiliser l'endpoint dédié
        url = `${API}/mathalea/chapters/${chapterCodeOrId}/exercise-types?limit=100`;
        
        if (selectedDomain) {
          url += `&domaine=${encodeURIComponent(selectedDomain)}`;
        }
        
        if (selectedGeneratorKind) {
          url += `&generator_kind=${selectedGeneratorKind}`;
        }
      } else {
        // Ancien système (fallback) : utiliser chapitre_id
        url = `${API}/catalogue/exercise-types?niveau=${niveau}&chapitre_id=${chapterCodeOrId}`;
        
        if (selectedDomain) {
          url += `&domaine=${encodeURIComponent(selectedDomain)}`;
        }
        
        if (selectedGeneratorKind) {
          url += `&generator_kind=${selectedGeneratorKind}`;
        }
      }
      
      console.log('📡 Chargement exercices depuis:', url);
      const response = await axios.get(url);
      
      // L'endpoint dédié retourne {total, items}
      const exercisesList = response.data.items || response.data;
      setExercises(exercisesList);
      console.log('📝 Exercices chargés:', exercisesList.length);
    } catch (error) {
      console.error('❌ Erreur chargement exercices:', error);
      console.error('   URL appelée:', error.config?.url);
      setExercises([]);
    } finally {
      setLoadingCatalogue(false);
    }
  };

  // NOUVELLE FONCTION : Charger une fiche existante depuis le backend
  const loadExistingSheet = async (id) => {
    try {
      setIsLoadingSheet(true);
      console.log('🔄 Chargement de la fiche:', id);
      
      // Charger les infos de la fiche
      const sheetResponse = await axios.get(`${API}/mathalea/sheets/${id}`);
      const sheet = sheetResponse.data;
      
      console.log('✅ Fiche chargée:', sheet);
      setSheetTitle(sheet.title || "Fiche d'exercices");
      setSheetId(id);
      
      // Charger les items de la fiche
      const itemsResponse = await axios.get(`${API}/mathalea/sheets/${id}/items`);
      const items = itemsResponse.data.items || [];
      
      console.log('✅ Items chargés:', items.length);
      
      // Transformer les items pour le format attendu par le builder
      const transformedItems = items.map(item => ({
        id: item.id,
        exercise_type_id: item.exercise_type_id,
        exercise: item.exercise_type_summary || {
          id: item.exercise_type_id,
          titre: item.exercise_type_summary?.titre || "Exercice",
          domaine: item.exercise_type_summary?.domaine || "",
          niveau: item.exercise_type_summary?.niveau || ""
        },
        config: {
          nb_questions: item.config?.nb_questions || 5,
          difficulty: item.config?.difficulty || "moyen",
          seed: item.config?.seed || Math.floor(Math.random() * 100000),
          options: item.config?.options || {},
          ai_enonce: item.config?.ai_enonce || false,
          ai_correction: item.config?.ai_correction || false
        },
        order: item.order
      }));
      
      setSheetItems(transformedItems);
      
      // Mettre à jour localStorage comme secours
      localStorage.setItem('current_sheet_id', id);
      
    } catch (error) {
      console.error('❌ Erreur chargement fiche:', error);
      alert('Impossible de charger cette fiche. Elle a peut-être été supprimée.');
      navigate('/builder');
    } finally {
      setIsLoadingSheet(false);
    }
  };


  const addExerciseToSheet = (exercise) => {
    const newItem = {
      id: `item_${Date.now()}_${Math.random()}`,
      exercise_type_id: exercise.id,
      exercise: exercise,
      config: {
        nb_questions: exercise.default_questions || 5,
        difficulty: "moyen",
        seed: Math.floor(Math.random() * 100000),
        options: {},
        ai_enonce: false,
        ai_correction: false
      },
      order: sheetItems.length
    };
    
    setSheetItems([...sheetItems, newItem]);
    console.log('➕ Exercice ajouté:', exercise.titre);
  };

  const removeItemFromSheet = (itemId) => {
    setSheetItems(sheetItems.filter(item => item.id !== itemId));
  };

  const moveItemUp = (index) => {
    if (index === 0) return;
    const newItems = [...sheetItems];
    [newItems[index - 1], newItems[index]] = [newItems[index], newItems[index - 1]];
    newItems.forEach((item, idx) => item.order = idx);
    setSheetItems(newItems);
  };

  const moveItemDown = (index) => {
    if (index === sheetItems.length - 1) return;
    const newItems = [...sheetItems];
    [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
    newItems.forEach((item, idx) => item.order = idx);
    setSheetItems(newItems);
  };

  const updateItemConfig = (itemId, field, value) => {
    setSheetItems(sheetItems.map(item => {
      if (item.id === itemId) {
        return {
          ...item,
          config: {
            ...item.config,
            [field]: value
          }
        };
      }
      return item;
    }));
  };

  const createSheet = async () => {
    try {
      const response = await axios.post(`${API}/mathalea/sheets`, {
        titre: sheetTitle,
        niveau: selectedLevel,
        description: `Fiche créée avec Le Maître Mot`,
        owner_id: userEmail || localStorage.getItem('lemaitremot_guest_id') || 'anonymous'
      });
      
      const newSheetId = response.data.id;
      setSheetId(newSheetId);
      
      // Mettre à jour l'URL pour inclure le sheetId
      navigate(`/builder/${newSheetId}`, { replace: true });
      
      // Sauvegarder dans localStorage comme secours
      localStorage.setItem('current_sheet_id', newSheetId);
      
      // Créer les items
      for (const item of sheetItems) {
        await axios.post(`${API}/mathalea/sheets/${newSheetId}/items`, {
          sheet_id: newSheetId,
          exercise_type_id: item.exercise_type_id,
          config: item.config
        });
      }
      
      console.log('✅ Fiche créée:', newSheetId);
      return newSheetId;
    } catch (error) {
      console.error('Erreur création fiche:', error);
      throw error;
    }
  };

  const saveSheet = async () => {
    try {
      let currentSheetId = sheetId;
      
      // Si pas de sheetId, créer une nouvelle fiche
      if (!currentSheetId) {
        return await createSheet();
      }
      
      // Mettre à jour le titre si nécessaire
      if (sheetTitle) {
        await axios.patch(`${API}/mathalea/sheets/${currentSheetId}`, {
          titre: sheetTitle
        });
      }
      
      // Supprimer tous les items existants
      try {
        const existingItems = await axios.get(`${API}/mathalea/sheet-items?sheet_id=${currentSheetId}`);
        const itemsToDelete = existingItems.data.items || [];
        
        for (const item of itemsToDelete) {
          await axios.delete(`${API}/mathalea/sheet-items/${item.id}`);
        }
      } catch (error) {
        console.warn('Erreur suppression items existants (peut-être aucun item):', error);
      }
      
      // Créer les nouveaux items
      for (let i = 0; i < sheetItems.length; i++) {
        const item = sheetItems[i];
        await axios.post(`${API}/mathalea/sheets/${currentSheetId}/items`, {
          sheet_id: currentSheetId,
          exercise_type_id: item.exercise_type_id,
          config: item.config,
          order: i
        });
      }
      
      console.log('✅ Fiche sauvegardée:', currentSheetId, `(${sheetItems.length} items)`);
      return currentSheetId;
    } catch (error) {
      console.error('❌ Erreur sauvegarde fiche:', error);
      throw error;
    }
  };

  const handlePreview = async () => {
    if (sheetItems.length === 0) {
      alert('Veuillez ajouter au moins un exercice à la fiche');
      return;
    }
    
    setIsGeneratingPreview(true);
    
    try {
      // ⚠️ SAUVEGARDER LA FICHE AVANT PREVIEW (garantit que modifications sont prises en compte)
      console.log('💾 Sauvegarde de la fiche avant preview...');
      const currentSheetId = await saveSheet();
      
      console.log('📡 Génération du preview...');
      const response = await axios.post(`${API}/mathalea/sheets/${currentSheetId}/preview`);
      
      console.log('👁️ Preview généré:', response.data);
      
      // Store preview data and open modal
      setPreviewData(response.data);
      setShowPreviewModal(true);
      
    } catch (error) {
      console.error('❌ Erreur preview:', error);
      
      // Improved error handling
      let errorMessage = 'Impossible de générer la prévisualisation. ';
      
      if (error.response) {
        // Server responded with error status
        if (error.response.status >= 400 && error.response.status < 500) {
          errorMessage += error.response.data?.detail || 'Merci de vérifier la configuration des exercices.';
        } else if (error.response.status >= 500) {
          errorMessage += 'Erreur serveur. Merci de réessayer plus tard.';
        }
      } else if (error.request) {
        // Request was made but no response received
        errorMessage += 'Impossible de contacter le serveur. Vérifiez votre connexion.';
      } else {
        // Something else happened
        errorMessage += 'Une erreur inattendue s\'est produite.';
      }
      
      alert(errorMessage);
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  const handleGeneratePDF = async () => {
    if (sheetItems.length === 0) {
      alert('Veuillez ajouter au moins un exercice à la fiche');
      return;
    }
    
    setIsGeneratingPDF(true);
    
    try {
      // ⚠️ SAUVEGARDER LA FICHE AVANT EXPORT (garantit que modifications sont prises en compte)
      console.log('💾 Sauvegarde de la fiche avant export PDF...');
      const currentSheetId = await saveSheet();
      
      const config = {};
      if (sessionToken) {
        config.headers = {
          'X-Session-Token': sessionToken
        };
      }
      
      // Le backend retourne un JSON avec 2 PDFs en base64
      const response = await axios.post(
        `${API}/mathalea/sheets/${currentSheetId}/export-standard`,
        {},
        config
      );
      
      // Le backend retourne { student_pdf, correction_pdf, base_filename } en base64
      const { student_pdf, correction_pdf, base_filename } = response.data;
      
      // Vérifier que les 2 PDFs sont présents
      if (!student_pdf || !correction_pdf) {
        throw new Error('PDFs incomplets reçus du serveur');
      }
      
      // Stocker les résultats et ouvrir la modale
      setPdfResult({
        student_pdf,
        correction_pdf,
        base_filename,
        sheetTitle
      });
      setShowPdfModal(true);
      
      console.log('✅ 2 PDFs générés et prêts à télécharger');
      
    } catch (error) {
      console.error('Erreur génération PDF:', error);
      
      // Improved error handling
      let errorMessage = 'Erreur lors de la génération du PDF. ';
      
      if (error.response) {
        if (error.response.status >= 400 && error.response.status < 500) {
          errorMessage += error.response.data?.detail || 'Merci de vérifier la configuration des exercices.';
        } else if (error.response.status >= 500) {
          errorMessage += 'Erreur serveur. Merci de réessayer plus tard.';
        }
      } else if (error.request) {
        errorMessage += 'Impossible de contacter le serveur. Vérifiez votre connexion.';
      } else {
        errorMessage += error.message || 'Une erreur inattendue s\'est produite.';
      }
      
      alert(errorMessage);
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  // Obtenir les domaines uniques des exercices disponibles
  // availableDomains est maintenant un état chargé depuis les chapitres (voir loadChapters)

  const handleLogin = () => {
    window.location.href = '/';
  };

  const handleLogout = async () => {
    try {
      if (sessionToken) {
        await axios.post(`${API}/auth/logout`, {}, {
          headers: {
            'X-Session-Token': sessionToken
          }
        });
      }
      
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
      setSessionToken("");
      setUserEmail("");
      setIsPro(false);
      
      console.log('✅ Déconnexion réussie');
      
    } catch (error) {
      console.error('Erreur déconnexion:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header 
        isPro={isPro}
        userEmail={userEmail}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />
      
      <div className="container mx-auto px-4 py-8">
        {/* Page title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Générateur de fiches
          </h1>
          <p className="text-lg text-gray-600">
            Créez des fiches d'exercices personnalisées
          </p>
          
          {isPro && userEmail && (
            <Alert className="max-w-md mx-auto mt-4 border-blue-200 bg-blue-50">
              <Crown className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800">
                <strong>Mode Pro :</strong> Fonctionnalités IA disponibles
              </AlertDescription>
            </Alert>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Colonne gauche : Catalogue */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="shadow-lg">
              <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
                <CardTitle>Catalogue d'exercices</CardTitle>
                <CardDescription className="text-blue-50">
                  Sélectionnez le niveau et le chapitre
                </CardDescription>
              </CardHeader>
              <CardContent className="p-6">
                {/* Sélecteurs */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  <div className="space-y-2">
                    <Label>Niveau</Label>
                    <Select value={selectedLevel} onValueChange={setSelectedLevel}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choisir un niveau" />
                      </SelectTrigger>
                      <SelectContent>
                        {levels.map(level => (
                          <SelectItem key={level} value={level}>
                            {level}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="space-y-2">
                    <Label>Chapitre</Label>
                    <Select 
                      value={selectedChapter} 
                      onValueChange={setSelectedChapter}
                      disabled={!selectedLevel}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choisir un chapitre" />
                      </SelectTrigger>
                      <SelectContent>
                        {chapters.map(chapter => (
                          <SelectItem key={chapter.id} value={chapter.id}>
                            {chapter.titre} ({chapter.nb_exercises} exercices)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Filtres additionnels */}
                {selectedChapter && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    <div className="space-y-2">
                      <Label>Domaine</Label>
                      <Select value={selectedDomain || "all"} onValueChange={(val) => setSelectedDomain(val === "all" ? "" : val)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Tous les domaines" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tous les domaines</SelectItem>
                          {availableDomains.map(domain => (
                            <SelectItem key={domain} value={domain}>
                              {domain}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>Type de générateur</Label>
                      <Select value={selectedGeneratorKind || "all"} onValueChange={(val) => setSelectedGeneratorKind(val === "all" ? "" : val)}>
                        <SelectTrigger>
                          <SelectValue placeholder="Tous les types" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="all">Tous les types</SelectItem>
                          <SelectItem value="template">Template</SelectItem>
                          <SelectItem value="legacy">Legacy</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}

                <Separator className="my-6" />

                {/* Liste des exercices */}
                {loadingCatalogue ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
                    <span className="ml-3 text-gray-600">Chargement...</span>
                  </div>
                ) : exercises.length > 0 ? (
                  <div className="space-y-3">
                    {exercises.map(exercise => (
                      <Card key={exercise.id} className="border hover:border-blue-300 transition-colors">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="font-semibold text-gray-900">{exercise.titre}</h4>
                                <Badge variant="outline" className="text-xs">
                                  {exercise.code_ref}
                                </Badge>
                              </div>
                              
                              <div className="flex flex-wrap gap-2 mb-2">
                                <Badge variant="secondary" className="text-xs">
                                  {exercise.is_legacy ? '🔧 Legacy' : '📝 Template'}
                                </Badge>
                                <Badge variant="outline" className="text-xs">
                                  📐 {exercise.domaine}
                                </Badge>
                                {exercise.supports_ai_enonce && isPro && (
                                  <Badge className="text-xs bg-purple-100 text-purple-700">
                                    <Sparkles className="h-3 w-3 mr-1" />
                                    IA disponible
                                  </Badge>
                                )}
                              </div>
                              
                              <p className="text-xs text-gray-500">
                                {exercise.min_questions}-{exercise.max_questions} questions • Niveau: {exercise.niveau}
                              </p>
                            </div>
                            
                            <Button
                              size="sm"
                              onClick={() => addExerciseToSheet(exercise)}
                              className="ml-4"
                            >
                              <Plus className="h-4 w-4 mr-1" />
                              Ajouter
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : selectedChapter ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>Aucun exercice disponible pour cette sélection</p>
                  </div>
                ) : (
                  <div className="text-center py-12 text-gray-500">
                    <BookOpen className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>Sélectionnez un niveau et un chapitre pour voir les exercices disponibles</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Colonne droite : Panier (Fiche en cours) */}
          <div className="space-y-6">
            <Card className="shadow-lg sticky top-4">
              <CardHeader className="bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-t-lg">
                <CardTitle>Ma fiche</CardTitle>
                <CardDescription className="text-green-50">
                  {sheetItems.length} exercice(s)
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                {/* Titre de la fiche */}
                <div className="mb-4">
                  <Label>Titre de la fiche</Label>
                  <Input
                    value={sheetTitle}
                    onChange={(e) => setSheetTitle(e.target.value)}
                    placeholder="Titre de votre fiche"
                    className="mt-1"
                  />
                </div>

                <Separator className="my-4" />

                {/* Liste des items */}
                {sheetItems.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <p className="text-sm">Votre fiche est vide</p>
                    <p className="text-xs mt-1">Ajoutez des exercices depuis le catalogue</p>
                  </div>
                ) : (
                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {sheetItems.map((item, index) => (
                      <Card key={item.id} className="border">
                        <CardContent className="p-3">
                          <div className="space-y-3">
                            {/* En-tête */}
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <p className="font-medium text-sm text-gray-900">
                                  {index + 1}. {item.exercise.titre}
                                </p>
                                <p className="text-xs text-gray-500 mt-1">
                                  {item.exercise.niveau} • {item.exercise.domaine}
                                </p>
                              </div>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeItemFromSheet(item.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>

                            {/* Configuration */}
                            <div className="space-y-2">
                              <div className="flex items-center gap-2">
                                <Label className="text-xs">Questions:</Label>
                                <Input
                                  type="number"
                                  value={item.config.nb_questions}
                                  onChange={(e) => updateItemConfig(item.id, 'nb_questions', parseInt(e.target.value) || 1)}
                                  min={item.exercise.min_questions}
                                  max={item.exercise.max_questions}
                                  className="h-7 w-16 text-xs"
                                />
                              </div>
                              
                              <div className="flex items-center gap-2">
                                <Label className="text-xs">Seed:</Label>
                                <Input
                                  type="number"
                                  value={item.config.seed}
                                  onChange={(e) => updateItemConfig(item.id, 'seed', parseInt(e.target.value) || 0)}
                                  className="h-7 w-20 text-xs"
                                />
                              </div>

                              {/* Options IA */}
                              {item.exercise.supports_ai_enonce && (
                                <div className="flex items-center justify-between">
                                  <Label className="text-xs flex items-center">
                                    <Sparkles className="h-3 w-3 mr-1 text-purple-600" />
                                    IA Énoncé
                                  </Label>
                                  <Switch
                                    checked={item.config.ai_enonce}
                                    onCheckedChange={(checked) => updateItemConfig(item.id, 'ai_enonce', checked)}
                                    disabled={!isPro}
                                  />
                                  {!isPro && (
                                    <Crown className="h-3 w-3 text-yellow-600 ml-1" title="Pro uniquement" />
                                  )}
                                </div>
                              )}
                              
                              {item.exercise.supports_ai_correction && (
                                <div className="flex items-center justify-between">
                                  <Label className="text-xs flex items-center">
                                    <Sparkles className="h-3 w-3 mr-1 text-purple-600" />
                                    IA Correction
                                  </Label>
                                  <Switch
                                    checked={item.config.ai_correction}
                                    onCheckedChange={(checked) => updateItemConfig(item.id, 'ai_correction', checked)}
                                    disabled={!isPro}
                                  />
                                  {!isPro && (
                                    <Crown className="h-3 w-3 text-yellow-600 ml-1" title="Pro uniquement" />
                                  )}
                                </div>
                              )}
                            </div>

                            {/* Boutons de réordonnancement */}
                            <div className="flex gap-1">
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => moveItemUp(index)}
                                disabled={index === 0}
                                className="h-6 text-xs"
                              >
                                <ChevronUp className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => moveItemDown(index)}
                                disabled={index === sheetItems.length - 1}
                                className="h-6 text-xs"
                              >
                                <ChevronDown className="h-3 w-3" />
                              </Button>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}

                {/* Actions */}
                {sheetItems.length > 0 && (
                  <>
                    <Separator className="my-4" />
                    <div className="space-y-2">
                      <Button
                        onClick={handlePreview}
                        disabled={isGeneratingPreview}
                        variant="outline"
                        className="w-full"
                      >
                        {isGeneratingPreview ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Eye className="h-4 w-4 mr-2" />
                        )}
                        Prévisualiser
                      </Button>
                      
                      <Button
                        onClick={handleGeneratePDF}
                        disabled={isGeneratingPDF}
                        className="w-full bg-green-600 hover:bg-green-700"
                      >
                        {isGeneratingPDF ? (
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                          <Download className="h-4 w-4 mr-2" />
                        )}
                        Générer PDF
                      </Button>
                      
                      {/* Bouton Export Pro - visible uniquement pour les Pro */}
                      {isPro && (
                        <Button
                          onClick={() => setShowProExportModal(true)}
                          disabled={!sheetId}
                          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700"
                        >
                          <Crown className="h-4 w-4 mr-2" />
                          Export Pro personnalisé
                        </Button>
                      )}
                    </div>

                    {!isPro && (
                      <Alert className="mt-4 border-orange-200 bg-orange-50">
                        <AlertCircle className="h-4 w-4 text-orange-600" />
                        <AlertDescription className="text-orange-800 text-xs">
                          Les fonctionnalités IA nécessitent un compte Pro
                        </AlertDescription>
                      </Alert>
                    )}
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
      
      {/* Preview Modal */}
      <SheetPreviewModal
        isOpen={showPreviewModal}
        onClose={() => setShowPreviewModal(false)}
        previewData={previewData}
      />
      
      {/* PDF Download Modal */}
      <PdfDownloadModal
        isOpen={showPdfModal}
        onClose={() => setShowPdfModal(false)}
        pdfResult={pdfResult}
      />
      
      {/* Pro Export Modal */}
      <ProExportModal
        isOpen={showProExportModal}
        onClose={() => setShowProExportModal(false)}
        sheetId={sheetId}
        sheetTitle={sheetTitle}
        sessionToken={sessionToken}
      />
    </div>
  );
}

export default SheetBuilderPage;
