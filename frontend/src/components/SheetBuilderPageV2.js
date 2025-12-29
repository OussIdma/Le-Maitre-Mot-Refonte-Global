import React, { useState, useEffect, useMemo } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import Header from "./Header";
import { useToast } from "../hooks/use-toast";
import { useAuth } from "../hooks/useAuth";
import { useLogin } from "../contexts/LoginContext";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Alert, AlertDescription } from "./ui/alert";
import { Separator } from "./ui/separator";
import { 
  Download, 
  Loader2, 
  AlertCircle,
  Search,
  FileText,
  CheckCircle2
} from "lucide-react";
import { Switch } from "./ui/switch";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Niveaux disponibles (CP à Terminale)
const LEVELS = ["CP", "CE1", "CE2", "CM1", "CM2", "6e", "5e", "4e", "3e", "2nde", "1re", "Tle"];

function SheetBuilderPageV2() {
  const navigate = useNavigate();
  const { sessionToken, userEmail, isPro } = useAuth();
  const { toast } = useToast();
  const { openLogin } = useLogin();

  // ÉTAPE 1: Navigation par niveau
  const [selectedLevel, setSelectedLevel] = useState("");
  const [chapters, setChapters] = useState([]);
  const [chaptersLoading, setChaptersLoading] = useState(false);
  const [chapterSearch, setChapterSearch] = useState("");
  const [selectedChapter, setSelectedChapter] = useState(null);

  // ÉTAPE 2: Paramètres
  const [nbExercises, setNbExercises] = useState(5);
  const [difficulty, setDifficulty] = useState("moyen");
  const [pdfLayout, setPdfLayout] = useState("eco");

  // ÉTAPE 3: Preview et Export
  const [previewData, setPreviewData] = useState(null);
  const [isGeneratingPreview, setIsGeneratingPreview] = useState(false);
  const [isGeneratingPDF, setIsGeneratingPDF] = useState(false);
  const [sheetId, setSheetId] = useState(null);
  const [error, setError] = useState(null);

  // Filtrer les chapitres selon la recherche
  const filteredChapters = useMemo(() => {
    if (!chapterSearch) return chapters;
    const searchLower = chapterSearch.toLowerCase();
    return chapters.filter(ch => 
      ch.titre?.toLowerCase().includes(searchLower) ||
      ch.code_officiel?.toLowerCase().includes(searchLower) ||
      ch.domaine?.toLowerCase().includes(searchLower)
    );
  }, [chapters, chapterSearch]);

  // Charger les chapitres quand le niveau change
  useEffect(() => {
    if (selectedLevel) {
      loadChapters(selectedLevel);
    } else {
      setChapters([]);
      setSelectedChapter(null);
      setChapterSearch("");
    }
  }, [selectedLevel]);

  const loadChapters = async (niveau) => {
    try {
      setChaptersLoading(true);
      setError(null);
      
      // Essayer d'abord l'API curriculum (source DB)
      let transformedChapters = [];
      try {
        const response = await axios.get(`${API}/admin/curriculum/${niveau}`);
        const data = response.data;
        // Transformer les chapitres pour le format attendu
        const chaptersList = data.chapitres || [];
        transformedChapters = chaptersList.map(ch => ({
          id: ch.code_officiel || ch.id,
          code_officiel: ch.code_officiel || ch.id,
          titre: ch.titre,
          domaine: ch.domaine,
          niveau: ch.niveau || niveau,
          nb_exercises: ch.nb_exercises  // P0: Garder null/undefined pour afficher "—"
        }));
        setChapters(transformedChapters);
      } catch (err) {
        // Fallback sur l'API catalogue
        const response = await axios.get(`${API}/catalogue/levels/${niveau}/chapters`);
        transformedChapters = response.data || [];
        setChapters(transformedChapters);
      }
      
      console.log(`✅ ${transformedChapters.length} chapitres chargés pour ${niveau}`);
    } catch (error) {
      console.error('❌ Erreur chargement chapitres:', error);
      setError('Impossible de charger les chapitres. Vérifiez votre connexion.');
      setChapters([]);
    } finally {
      setChaptersLoading(false);
    }
  };

  // Générer le preview (3 clics)
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
        owner_id: userEmail || localStorage.getItem('lemaitremot_guest_id') || 'anonymous'
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

      // 4. Créer les items de la fiche
      for (let i = 0; i < selectedExercises.length; i++) {
        const exType = selectedExercises[i];
        await axios.post(`${API}/mathalea/sheets/${newSheetId}/items`, {
          sheet_id: newSheetId,
          exercise_type_id: exType.id,
          config: {
            nb_questions: exType.default_questions || 5,
            difficulty: difficulty,
            seed: Math.floor(Math.random() * 100000),
            options: {}
          },
          order: i
        });
      }

      // 5. Générer le preview
      const previewResponse = await axios.post(`${API}/mathalea/sheets/${newSheetId}/preview`);
      setPreviewData(previewResponse.data);

      toast({
        title: "Preview généré",
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

  // Exporter PDF
  // P0: Export nécessite un compte (Free ou Pro) - plus de guest
  const handleExportPDF = async (includeSolutions = false) => {
    if (!sheetId) {
      toast({
        title: "Erreur",
        description: "Aucune fiche générée",
        variant: "destructive"
      });
      return;
    }

    // P0: Vérifier si l'utilisateur est connecté
    if (!sessionToken) {
      toast({
        title: "Connexion requise",
        description: "Créez un compte gratuit pour exporter vos fiches en PDF",
        variant: "default"
      });
      openLogin('/sheet-builder');
      return;
    }

    setIsGeneratingPDF(true);
    setError(null);

    try {
      // P0: Toujours utiliser X-Session-Token (plus de X-Guest-ID)
      const config = {
        headers: { 'X-Session-Token': sessionToken }
      };

      const response = await axios.post(
        `${API}/mathalea/sheets/${sheetId}/export-standard?layout=${pdfLayout}`,
        {},
        config
      );

      const { student_pdf, correction_pdf, filename_base, metadata } = response.data;

      // Afficher info quota si utilisateur Free
      if (metadata?.exports_remaining !== null && metadata?.exports_remaining !== undefined) {
        console.log(`[EXPORT] Exports restants aujourd'hui: ${metadata.exports_remaining}`);
      }

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
        title: "PDF téléchargé",
        description: `Le fichier ${filename} a été téléchargé`,
        variant: "default"
      });

    } catch (error) {
      console.error('❌ Erreur export PDF:', error);
      const status = error.response?.status;
      const errorDetail = error.response?.data?.detail;

      // P0: Gérer les erreurs d'authentification
      if (status === 401) {
        const action = errorDetail?.action;
        if (action === 'show_login_modal') {
          toast({
            title: "Session expirée",
            description: "Veuillez vous reconnecter",
            variant: "destructive"
          });
          openLogin('/sheet-builder');
          return;
        }
      }

      // P0: Gérer le quota dépassé (429)
      if (status === 429) {
        toast({
          title: "Limite atteinte",
          description: errorDetail?.message || "Limite de 10 exports/jour atteinte. Passez à Pro pour des exports illimités.",
          variant: "destructive"
        });
        return;
      }

      const errorMessage = errorDetail?.message || error.message || 'Erreur lors de l\'export';
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

  const handleLogin = () => {
    window.location.href = '/';
  };

  const handleLogout = async () => {
    try {
      if (sessionToken) {
        await axios.post(`${API}/auth/logout`, {}, {
          headers: { 'X-Session-Token': sessionToken }
        });
      }
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
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
      
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Titre */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Générateur de fiches (3 clics)
          </h1>
          <p className="text-lg text-gray-600">
            Créez une fiche d'exercices en 30 secondes
          </p>
        </div>

        {/* ÉTAPE 1: Choix du chapitre */}
        <Card className="mb-6 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
            <CardTitle>Étape 1 : Choisir le chapitre</CardTitle>
            <CardDescription className="text-blue-50">
              Sélectionnez le niveau et le chapitre
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
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
            </div>

            {chaptersLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-blue-600 mr-2" />
                <span className="text-gray-600">Chargement des chapitres...</span>
              </div>
            ) : filteredChapters.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-96 overflow-y-auto">
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
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h4 className="font-semibold text-sm text-gray-900 mb-1">
                            {chapter.titre}
                          </h4>
                          <p className="text-xs text-gray-500">
                            {chapter.domaine} • {chapter.nb_exercises > 0 ? `${chapter.nb_exercises} exercices` : '—'}
                          </p>
                        </div>
                        {selectedChapter?.id === chapter.id && (
                          <CheckCircle2 className="h-5 w-5 text-blue-600" />
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

            {error && (
              <Alert className="mt-4 border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800 text-sm">
                  {error}
                </AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* ÉTAPE 2: Paramètres + Preview + Export */}
        {selectedChapter && (
          <Card className="mb-6 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-t-lg">
              <CardTitle>Étape 2 : Paramètres et génération</CardTitle>
              <CardDescription className="text-green-50">
                Configurez et générez votre fiche
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="space-y-2">
                  <Label>Nombre d'exercices</Label>
                  <Input
                    type="number"
                    min="1"
                    max="20"
                    value={nbExercises}
                    onChange={(e) => setNbExercises(parseInt(e.target.value) || 1)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Difficulté</Label>
                  <Select value={difficulty} onValueChange={setDifficulty}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="facile">Facile</SelectItem>
                      <SelectItem value="moyen">Moyen</SelectItem>
                      <SelectItem value="difficile">Difficile</SelectItem>
                      <SelectItem value="mix">Mixte</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Layout PDF</Label>
                  <div className="flex items-center justify-between p-2 bg-gray-50 rounded-md">
                    <Label htmlFor="pdf-layout-toggle" className="text-sm font-medium cursor-pointer">
                      Éco (2 colonnes)
                    </Label>
                    <Switch
                      id="pdf-layout-toggle"
                      checked={pdfLayout === "eco"}
                      onCheckedChange={(checked) => setPdfLayout(checked ? "eco" : "classic")}
                    />
                  </div>
                </div>
              </div>

              <Button
                onClick={handleGeneratePreview}
                disabled={isGeneratingPreview}
                className="w-full bg-green-600 hover:bg-green-700 mb-6"
                size="lg"
              >
                {isGeneratingPreview ? (
                  <>
                    <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                    Génération en cours...
                  </>
                ) : (
                  <>
                    <FileText className="h-5 w-5 mr-2" />
                    Générer la fiche (3 clics)
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

                  {/* Boutons Export */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Button
                      onClick={() => handleExportPDF(false)}
                      disabled={isGeneratingPDF}
                      className="w-full bg-blue-600 hover:bg-blue-700"
                      size="lg"
                    >
                      {isGeneratingPDF ? (
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      ) : (
                        <Download className="h-5 w-5 mr-2" />
                      )}
                      Télécharger PDF Sujet
                    </Button>

                    <Button
                      onClick={() => handleExportPDF(true)}
                      disabled={isGeneratingPDF}
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      size="lg"
                    >
                      {isGeneratingPDF ? (
                        <Loader2 className="h-5 w-5 mr-2 animate-spin" />
                      ) : (
                        <Download className="h-5 w-5 mr-2" />
                      )}
                      Télécharger PDF Corrigé
                    </Button>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}

export default SheetBuilderPageV2;

