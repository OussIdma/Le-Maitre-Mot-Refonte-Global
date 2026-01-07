/**
 * SheetBuilderPageV2 - Parcours "3 clics" pour générer une fiche
 * 
 * PR9: Parcours simplifié pour les profs
 * - Section 1: Choisir un chapitre (niveau + recherche)
 * - Section 2: Ma fiche (paramètres + preview + export)
 * 
 * Utilise les gates PR7.1 (compte requis) et PR8 (Éco = Premium)
 */

import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { useToast } from "../hooks/use-toast";
import { useAuth } from "../hooks/useAuth";
import { useLogin } from "../contexts/LoginContext";
import { useExportPdfGate } from "../lib/exportPdfUtils";
import { useCurriculumChapters } from "../hooks/useCurriculumChapters";
import PremiumEcoModal from "./PremiumEcoModal";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Separator } from "./ui/separator";
import { Badge } from "./ui/badge";
import { Switch } from "./ui/switch";
import { 
  Download, 
  Loader2, 
  AlertCircle,
  Search,
  FileText,
  CheckCircle2,
  RefreshCw,
  Save,
  Eye
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Niveaux disponibles (CP à Terminale)
const LEVELS = ["CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e", "2nde", "1re", "Tle"];

function SheetBuilderPageV2() {
  const navigate = useNavigate();
  const { sessionToken, userEmail, isPro } = useAuth();
  const { toast } = useToast();
  const { openLogin, openRegister } = useLogin();
  
  // PR7.1 + PR8: Utiliser les gates d'export
  const { canExport, checkBeforeExport, handleExportError, isPro: isProFromGate } = useExportPdfGate();
  const isProUser = isPro || isProFromGate;

  // SECTION 1: Choisir un chapitre
  const [selectedLevel, setSelectedLevel] = useState("");
  const [chapterSearch, setChapterSearch] = useState("");
  const [selectedChapter, setSelectedChapter] = useState(null);

  // Utiliser le hook curriculum
  const { chapters, loading: chaptersLoading, error: chaptersError, search: searchChapters, source: chaptersSource, warning: chaptersWarning } = useCurriculumChapters(selectedLevel);

  // Filtrer les chapitres selon la recherche
  const filteredChapters = useMemo(() => {
    if (!chapterSearch.trim()) return chapters;
    return searchChapters(chapterSearch, selectedLevel);
  }, [chapters, chapterSearch, selectedLevel, searchChapters]);

  // SECTION 2: Ma fiche
  const [nbExercises, setNbExercises] = useState(5);
  const [difficulty, setDifficulty] = useState("mix");
  const [pdfLayout, setPdfLayout] = useState("classic"); // PR8: Classic par défaut (Éco = Premium)
  const [seed, setSeed] = useState(Date.now()); // PR9: Seed pour déterminisme

  // Preview et Export
  const [previewData, setPreviewData] = useState(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [sheetId, setSheetId] = useState(null);
  const [error, setError] = useState(null);

  // PR8: Modal premium pour layout Éco
  const [showPremiumEcoModal, setShowPremiumEcoModal] = useState(false);

  // Réinitialiser quand le chapitre change
  useEffect(() => {
    if (selectedChapter) {
      setPreviewData(null);
      setSheetId(null);
      setError(null);
      setSeed(Date.now()); // Nouveau seed pour nouveau chapitre
    }
  }, [selectedChapter]);

  // Générer le preview (PR9: avec seed)
  const handleGeneratePreview = async () => {
    if (!selectedChapter) {
      toast({
        title: "Chapitre requis",
        description: "Veuillez sélectionner un chapitre",
        variant: "destructive"
      });
      return;
    }

    setIsGeneratingPreview(true);
    setError(null);
    setPreviewData(null);

    try {
      // 1. Créer une fiche temporaire
      const sheetResponse = await axios.post(`${API}/mathalea/sheets`, {
        titre: `Fiche ${selectedChapter.titre}`,
        niveau: selectedLevel,
        description: `Fiche générée rapidement`,
        owner_id: userEmail || 'anonymous'
      });
      
      const newSheetId = sheetResponse.data.id;
      setSheetId(newSheetId);

      // 2. Récupérer les types d'exercices du chapitre
      const exerciseTypesResponse = await axios.get(
        `${API}/mathalea/chapters/${selectedChapter.code_officiel}/exercise-types?limit=100`
      );
      
      const exerciseTypes = exerciseTypesResponse.data.items || [];
      
      if (exerciseTypes.length === 0) {
        throw new Error(`Aucun exercice disponible pour le chapitre ${selectedChapter.titre}`);
      }

      // 3. Sélectionner les exercices (premiers N disponibles)
      const selectedExercises = exerciseTypes.slice(0, nbExercises);

      // 4. Créer les items de la fiche avec seed déterminé
      for (let i = 0; i < selectedExercises.length; i++) {
        const exType = selectedExercises[i];
        // PR9: Utiliser seed + index pour avoir des seeds différents mais déterministes
        const exerciseSeed = seed + i;
        
        await axios.post(`${API}/mathalea/sheets/${newSheetId}/items`, {
          sheet_id: newSheetId,
          exercise_type_id: exType.id,
          config: {
            nb_questions: exType.default_questions || 5,
            difficulty: difficulty === "mix" ? null : difficulty, // "mix" = null pour variété
            seed: exerciseSeed,
            options: {}
          },
          order: i
        });
      }

      // 5. Générer le preview
      const previewResponse = await axios.post(`${API}/mathalea/sheets/${newSheetId}/preview`);
      setPreviewData(previewResponse.data);

      toast({
        title: "✅ Preview généré",
        description: `${selectedExercises.length} exercice(s) généré(s)`,
        variant: "default"
      });

    } catch (error) {
      console.error('❌ Erreur génération preview:', error);
      const errorMessage = error.response?.data?.detail || error.message || 'Erreur lors de la génération';
      setError(errorMessage);
      toast({
        title: "Erreur",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsGeneratingPreview(false);
    }
  };

  // PR9: Regénérer avec nouveau seed
  const handleRegenerate = () => {
    const newSeed = Date.now();
    setSeed(newSeed);
    handleGeneratePreview();
  };

  // Sauvegarder la fiche (si connecté)
  const handleSave = async () => {
    if (!sheetId) {
      toast({
        title: "Aucune fiche",
        description: "Générez d'abord une preview",
        variant: "destructive"
      });
      return;
    }

    // PR7.1: Vérifier si l'utilisateur est connecté
    if (!checkBeforeExport(() => handleSave())) {
      // Modal "Créer un compte" ouverte
      return;
    }

    try {
      // TODO: Implémenter la sauvegarde dans /mes-fiches
      toast({
        title: "Fiche sauvegardée",
        description: "Votre fiche a été sauvegardée dans Mes fiches",
        variant: "default"
      });
      navigate(`/mes-fiches/${sheetId}`);
    } catch (error) {
      console.error('Erreur sauvegarde:', error);
      toast({
        title: "Erreur",
        description: "Impossible de sauvegarder la fiche",
        variant: "destructive"
      });
    }
  };

  // Exporter PDF (PR7.1 + PR8)
  const handleExportPDF = async (includeSolutions = false) => {
    if (!sheetId) {
      toast({
        title: "Aucune fiche",
        description: "Générez d'abord une preview",
        variant: "destructive"
      });
      return;
    }

    // PR7.1: Vérifier si l'utilisateur peut exporter (compte requis)
    if (!checkBeforeExport(() => handleExportPDF(includeSolutions))) {
      // Modal "Créer un compte" ouverte, ne pas appeler l'API
      return;
    }

    setIsGeneratingPDF(true);
    setError(null);

    try {
      const config = {
        headers: { 'X-Session-Token': sessionToken }
      };

      const response = await axios.post(
        `${API}/mathalea/sheets/${sheetId}/export-standard?layout=${pdfLayout}`,
        {},
        config
      );

      const { student_pdf, correction_pdf, filename_base } = response.data;

      // Télécharger le PDF approprié
      const pdfBase64 = includeSolutions ? correction_pdf : student_pdf;
      const filename = includeSolutions
        ? `${filename_base}_corrige.pdf`
        : `${filename_base}_sujet.pdf`;

      // Convertir base64 en blob et télécharger
      const byteCharacters = atob(pdfBase64);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], { type: 'application/pdf' });

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: "✅ PDF téléchargé",
        description: `Le fichier ${filename} a été téléchargé`,
        variant: "default"
      });

    } catch (error) {
      console.error('❌ Erreur export PDF:', error);
      
      // PR7.1 + PR8: Gérer les erreurs d'authentification et premium
      if (handleExportError(error, () => setShowPremiumEcoModal(true), { type: 'export_pdf' })) {
        // Erreur gérée (modal ouverte), ne pas afficher d'autre message
        setIsGeneratingPDF(false);
        return;
      }
      
      // PR8: Gérer erreur 403 PREMIUM_REQUIRED_ECO
      if (error.response?.status === 403) {
        const errorDetail = error.response?.data?.detail;
        const errorCode = typeof errorDetail === 'object' ? errorDetail.code || errorDetail.error : null;
        if (errorCode === 'PREMIUM_REQUIRED_ECO' || errorDetail?.error === 'premium_required') {
          setShowPremiumEcoModal(true);
          setIsGeneratingPDF(false);
          return;
        }
      }

      const errorMessage = error.response?.data?.detail?.message || error.message || 'Erreur lors de l\'export';
      setError(errorMessage);
      toast({
        title: "Erreur",
        description: errorMessage,
        variant: "destructive"
      });
    } finally {
      setIsGeneratingPDF(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Note: Header est géré par AppWithNav dans App.js */}
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Titre */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Générateur de fiches
          </h1>
          <p className="text-lg text-gray-600">
            Créez une fiche d'exercices en 30 secondes
          </p>
        </div>

        {/* Layout: 2 colonnes (desktop) ou empilé (mobile) */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          
          {/* SECTION 1: Choisir un chapitre */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
              <CardTitle>Choisir un chapitre</CardTitle>
              <CardDescription className="text-blue-50">
                Sélectionnez le niveau et recherchez un chapitre
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                {/* Select Niveau */}
                <div className="space-y-2">
                  <Label>Niveau</Label>
                  <Select value={selectedLevel} onValueChange={setSelectedLevel}>
                    <SelectTrigger>
                      <SelectValue placeholder="Choisir un niveau" />
                    </SelectTrigger>
                    <SelectContent>
                      {LEVELS.map(level => (
                        <SelectItem key={level} value={level}>
                          {level}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Recherche chapitre */}
                <div className="space-y-2">
                  <Label>Rechercher un chapitre</Label>
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                    <Input
                      placeholder="Rechercher par titre, code ou domaine..."
                      value={chapterSearch}
                      onChange={(e) => setChapterSearch(e.target.value)}
                      className="pl-10"
                      disabled={!selectedLevel || chaptersLoading}
                    />
                  </div>
                </div>

                {/* Liste chapitres */}
                {chaptersLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
                    <span className="text-gray-600">Chargement...</span>
                  </div>
                ) : filteredChapters.length > 0 ? (
                  <div className="max-h-96 overflow-y-auto space-y-2">
                    {filteredChapters.map(chapter => (
                      <Card
                        key={chapter.id}
                        className={`cursor-pointer transition-all ${
                          selectedChapter?.id === chapter.id
                            ? 'border-blue-500 bg-blue-50'
                            : 'hover:border-blue-300'
                        }`}
                        onClick={() => setSelectedChapter(chapter)}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <h4 className="font-semibold text-sm text-gray-900 mb-1">
                                {chapter.titre}
                              </h4>
                              <p className="text-xs text-gray-500">
                                {chapter.domaine} • {chapter.nb_exercises > 0 ? `${chapter.nb_exercises} exercices` : '—'}
                              </p>
                              {chapter.code_officiel && (
                                <p className="text-xs text-gray-400 mt-1">
                                  Code: {chapter.code_officiel}
                                </p>
                              )}
                            </div>
                            {selectedChapter?.id === chapter.id && (
                              <CheckCircle2 className="h-5 w-5 text-blue-600 flex-shrink-0" />
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : selectedLevel ? (
                  <div className="text-center py-8 text-gray-500">
                    <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                    <p>Aucun chapitre trouvé</p>
                  </div>
                ) : (
                  <div className="text-center py-8 text-gray-500">
                    <p>Sélectionnez un niveau pour voir les chapitres disponibles</p>
                  </div>
                )}

                {/* Résumé chapitre sélectionné */}
                {selectedChapter && (
                  <Alert className="bg-blue-50 border-blue-200">
                    <CheckCircle2 className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-900">
                      <strong>{selectedChapter.titre}</strong>
                      {selectedChapter.code_officiel && (
                        <span className="block text-xs text-blue-700 mt-1">
                          Code officiel: {selectedChapter.code_officiel}
                        </span>
                      )}
                    </AlertDescription>
                  </Alert>
                )}

                {chaptersWarning && (
                  <Alert className="bg-yellow-50 border-yellow-200">
                    <AlertCircle className="h-4 w-4 text-yellow-600" />
                    <AlertDescription className="text-yellow-900">
                      {chaptersWarning}
                    </AlertDescription>
                  </Alert>
                )}

                {chaptersError && (
                  <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{chaptersError}</AlertDescription>
                  </Alert>
                )}
              </div>
            </CardContent>
          </Card>

          {/* SECTION 2: Ma fiche */}
          <Card className="shadow-lg">
            <CardHeader className="bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-t-lg">
              <CardTitle>Ma fiche</CardTitle>
              <CardDescription className="text-green-50">
                Configurez et générez votre fiche
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              {!selectedChapter ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg font-medium mb-2">Sélectionnez un chapitre</p>
                  <p className="text-sm">Choisissez un chapitre dans la section de gauche pour commencer</p>
                </div>
              ) : (
                <>
                  {/* Paramètres */}
                  <div className="space-y-4 mb-6">
                    {/* Nb exercices */}
                    <div className="space-y-2">
                      <Label>Nombre d'exercices</Label>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setNbExercises(Math.max(1, nbExercises - 1))}
                          disabled={nbExercises <= 1}
                        >
                          −
                        </Button>
                        <Input
                          type="number"
                          min="1"
                          max="20"
                          value={nbExercises}
                          onChange={(e) => setNbExercises(Math.max(1, Math.min(20, parseInt(e.target.value) || 1)))}
                          className="text-center w-20"
                        />
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setNbExercises(Math.min(20, nbExercises + 1))}
                          disabled={nbExercises >= 20}
                        >
                          +
                        </Button>
                      </div>
                    </div>

                    {/* Difficulté */}
                    <div className="space-y-2">
                      <Label>Difficulté</Label>
                      <Select value={difficulty} onValueChange={setDifficulty}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="mix">Mix</SelectItem>
                          <SelectItem value="facile">Facile</SelectItem>
                          <SelectItem value="moyen">Moyen</SelectItem>
                          <SelectItem value="difficile">Difficile</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    {/* Layout PDF - PR8: Éco = Premium uniquement */}
                    <div className="space-y-2">
                      <Label>Mise en page PDF</Label>
                      <div 
                        className={`flex items-center justify-between p-2 rounded-md ${
                          !isProUser ? 'bg-gray-100 opacity-60' : 'bg-gray-50'
                        }`}
                        onClick={() => {
                          if (!isProUser && pdfLayout === "eco") {
                            setShowPremiumEcoModal(true);
                          }
                        }}
                        style={{ cursor: !isProUser ? 'pointer' : 'default' }}
                      >
                        <div className="flex items-center gap-2">
                          <Label htmlFor="pdf-layout-toggle" className="text-sm font-medium cursor-pointer">
                            Éco (2 colonnes)
                          </Label>
                          {!isProUser && (
                            <Badge variant="secondary" className="text-xs bg-yellow-100 text-yellow-800">
                              Premium
                            </Badge>
                          )}
                        </div>
                        <Switch
                          id="pdf-layout-toggle"
                          checked={pdfLayout === "eco"}
                          disabled={!isProUser}
                          onCheckedChange={(checked) => {
                            if (isProUser) {
                              setPdfLayout(checked ? "eco" : "classic");
                            } else {
                              setShowPremiumEcoModal(true);
                            }
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Bouton principal: Générer la preview */}
                  <Button
                    onClick={handleGeneratePreview}
                    disabled={isGeneratingPreview}
                    className="w-full bg-green-600 hover:bg-green-700 mb-4"
                    size="lg"
                  >
                    {isGeneratingPreview ? (
                      <>
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                        Génération en cours...
                      </>
                    ) : (
                      <>
                        <Eye className="h-5 w-5 mr-2" />
                        Générer la preview
                      </>
                    )}
                  </Button>

                  {/* Preview intégré */}
                  {previewData && (
                    <>
                      <Separator className="my-6" />
                      <div className="mb-6">
                        <h3 className="text-xl font-semibold mb-4">Aperçu de la fiche</h3>
                        <div className="bg-white border rounded-lg p-6 max-h-[600px] overflow-y-auto">
                          {previewData.items?.map((item, idx) => (
                            <div key={item.item_id || idx} className="mb-6 last:mb-0">
                              <div className="mb-2">
                                <h4 className="font-semibold text-lg">
                                  Exercice {idx + 1} : {item.exercise_type_summary?.titre}
                                </h4>
                                <p className="text-sm text-gray-500">
                                  {item.exercise_type_summary?.domaine} • {item.exercise_type_summary?.niveau}
                                </p>
                              </div>
                              <div 
                                className="prose prose-sm max-w-none"
                                dangerouslySetInnerHTML={{ 
                                  __html: item.generated?.enonce_html || '<p>Aucun énoncé disponible</p>' 
                                }}
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Boutons secondaires */}
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        <Button
                          onClick={handleRegenerate}
                          disabled={isGeneratingPreview}
                          variant="outline"
                          className="w-full"
                        >
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Regénérer
                        </Button>

                        <Button
                          onClick={() => handleExportPDF(false)}
                          disabled={isGeneratingPDF || !canExport}
                          className="w-full bg-blue-600 hover:bg-blue-700"
                        >
                          {isGeneratingPDF ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          ) : (
                            <Download className="h-4 w-4 mr-2" />
                          )}
                          Exporter PDF
                        </Button>

                        <Button
                          onClick={handleSave}
                          disabled={!canExport}
                          variant="outline"
                          className="w-full"
                        >
                          <Save className="h-4 w-4 mr-2" />
                          Sauvegarder
                        </Button>
                      </div>
                    </>
                  )}

                  {error && (
                    <Alert variant="destructive" className="mt-4">
                      <AlertCircle className="h-4 w-4" />
                      <AlertDescription>{error}</AlertDescription>
                    </Alert>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* PR8: Modal Premium pour layout Éco */}
      <PremiumEcoModal
        isOpen={showPremiumEcoModal}
        onClose={() => setShowPremiumEcoModal(false)}
        onStayClassic={() => setPdfLayout("classic")}
      />
    </div>
  );
}

export default SheetBuilderPageV2;
