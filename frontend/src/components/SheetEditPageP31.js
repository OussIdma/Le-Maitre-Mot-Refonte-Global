/**
 * SheetEditPageP31 - Page d'édition d'une fiche (P3.1)
 * 
 * Permet de :
 * - Voir et réorganiser les exercices (drag & drop)
 * - Ajouter des exercices depuis "Mes exercices"
 * - Aperçu de la fiche (sticky preview)
 * - Export PDF
 */
import React, { useState, useEffect, useRef } from "react";
import axios from "axios";
import { useParams, useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import Header from "./Header";
import {
  FileText,
  Download,
  Trash2,
  GripVertical,
  Plus,
  Loader2,
  Save,
  ArrowLeft,
  Eye,
  X
} from "lucide-react";
import { useToast } from "../hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function SheetEditPageP31() {
  const { sheet_uid } = useParams();
  const navigate = useNavigate();
  const { toast } = useToast();
  
  const [sheet, setSheet] = useState(null);
  const [exercises, setExercises] = useState([]); // Exercices complets depuis user_exercises
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [availableExercises, setAvailableExercises] = useState([]);
  const [loadingExercises, setLoadingExercises] = useState(false);
  const previewRef = useRef(null);
  const [pdfLayout, setPdfLayout] = useState("eco"); // "eco" ou "classic" - PR6

  useEffect(() => {
    const token = localStorage.getItem('lemaitremot_session_token');
    if (!token) {
      navigate('/mes-fiches');
      return;
    }
    setSessionToken(token);
    loadSheet();
  }, [sheet_uid]);

  const loadSheet = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('lemaitremot_session_token');
      
      // P3.1 HOTFIX: Charger la fiche avec withCredentials pour cookies httpOnly
      const sheetResponse = await axios.get(`${API}/user/sheets/${sheet_uid}`, {
        headers: { 'X-Session-Token': token },
        withCredentials: true
      });
      setSheet(sheetResponse.data);
      
      // Charger les exercices complets
      if (sheetResponse.data.exercises && sheetResponse.data.exercises.length > 0) {
        await loadExercisesDetails(sheetResponse.data.exercises);
      }
    } catch (error) {
      console.error('Erreur chargement fiche:', error);
      toast({
        title: "Erreur",
        description: "Impossible de charger la fiche",
        variant: "destructive"
      });
      navigate('/mes-fiches');
    } finally {
      setLoading(false);
    }
  };

  const loadExercisesDetails = async (sheetExercises) => {
    try {
      const token = localStorage.getItem('lemaitremot_session_token');
      
      // Charger tous les exercices de l'utilisateur
      const allExercisesResponse = await axios.get(`${API}/user/exercises`, {
        headers: { 'X-Session-Token': token },
        withCredentials: true
      });
      
      const allExercises = allExercisesResponse.data.exercises || [];
      
      // Mapper les exercices de la fiche avec leurs détails
      const exercisesWithDetails = sheetExercises
        .sort((a, b) => a.order - b.order)
        .map(sheetEx => {
          const fullExercise = allExercises.find(ex => ex.exercise_uid === sheetEx.exercise_uid);
          return fullExercise ? { ...fullExercise, order: sheetEx.order } : null;
        })
        .filter(Boolean);
      
      setExercises(exercisesWithDetails);
    } catch (error) {
      console.error('Erreur chargement détails exercices:', error);
    }
  };

  const handleDragStart = (index) => {
    setDraggedIndex(index);
  };

  const handleDragOver = (e, index) => {
    e.preventDefault();
  };

  const handleDrop = async (e, dropIndex) => {
    e.preventDefault();
    
    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null);
      return;
    }
    
    // Réorganiser les exercices
    const newExercises = [...exercises];
    const [draggedItem] = newExercises.splice(draggedIndex, 1);
    newExercises.splice(dropIndex, 0, draggedItem);
    
    // Mettre à jour les ordres
    const updatedExercises = newExercises.map((ex, idx) => ({
      exercise_uid: ex.exercise_uid,
      order: idx + 1
    }));
    
    setExercises(newExercises.map((ex, idx) => ({ ...ex, order: idx + 1 })));
    
    // Sauvegarder
    await saveSheetOrder(updatedExercises);
    
    setDraggedIndex(null);
  };

  const saveSheetOrder = async (exercisesOrder) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('lemaitremot_session_token');
      
      await axios.put(
        `${API}/user/sheets/${sheet_uid}`,
        { exercises: exercisesOrder },
        { 
          headers: { 'X-Session-Token': token },
          withCredentials: true
        }
      );
      
      toast({
        title: "✅ Ordre sauvegardé",
        description: "L'ordre des exercices a été mis à jour",
        variant: "default"
      });
    } catch (error) {
      console.error('Erreur sauvegarde ordre:', error);
      toast({
        title: "Erreur",
        description: "Impossible de sauvegarder l'ordre",
        variant: "destructive"
      });
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveExercise = async (exerciseUid) => {
    try {
      const token = localStorage.getItem('lemaitremot_session_token');
      
      await axios.delete(
        `${API}/user/sheets/${sheet_uid}/remove-exercise/${exerciseUid}`,
        { 
          headers: { 'X-Session-Token': token },
          withCredentials: true
        }
      );
      
      // Recharger la fiche
      await loadSheet();
      
      toast({
        title: "✅ Exercice retiré",
        description: "L'exercice a été retiré de la fiche",
        variant: "default"
      });
    } catch (error) {
      console.error('Erreur retrait exercice:', error);
      toast({
        title: "Erreur",
        description: "Impossible de retirer l'exercice",
        variant: "destructive"
      });
    }
  };

  const handleOpenAddDialog = async () => {
    setShowAddDialog(true);
    setLoadingExercises(true);
    
    try {
      const token = localStorage.getItem('lemaitremot_session_token');
      const response = await axios.get(`${API}/user/exercises`, {
        headers: { 'X-Session-Token': token },
        withCredentials: true
      });
      
      const allExercises = response.data.exercises || [];
      // Filtrer les exercices déjà dans la fiche
      const existingUids = exercises.map(ex => ex.exercise_uid);
      const available = allExercises.filter(ex => !existingUids.includes(ex.exercise_uid));
      
      setAvailableExercises(available);
    } catch (error) {
      console.error('Erreur chargement exercices:', error);
    } finally {
      setLoadingExercises(false);
    }
  };

  const handleAddExercise = async (exerciseUid) => {
    try {
      const token = localStorage.getItem('lemaitremot_session_token');
      
      await axios.post(
        `${API}/user/sheets/${sheet_uid}/add-exercise`,
        { exercise_uid: exerciseUid },
        { 
          headers: { 'X-Session-Token': token },
          withCredentials: true
        }
      );
      
      setShowAddDialog(false);
      await loadSheet();
      
      toast({
        title: "✅ Exercice ajouté",
        description: "L'exercice a été ajouté à la fiche",
        variant: "default"
      });
    } catch (error) {
      console.error('Erreur ajout exercice:', error);
      toast({
        title: "Erreur",
        description: "Impossible d'ajouter l'exercice",
        variant: "destructive"
      });
    }
  };

  const handleUpdateTitle = async (newTitle) => {
    try {
      const token = localStorage.getItem('lemaitremot_session_token');
      
      await axios.put(
        `${API}/user/sheets/${sheet_uid}`,
        { title: newTitle },
        { 
          headers: { 'X-Session-Token': token },
          withCredentials: true
        }
      );
      
      setSheet({ ...sheet, title: newTitle });
      
      toast({
        title: "✅ Titre mis à jour",
        variant: "default"
      });
    } catch (error) {
      console.error('Erreur mise à jour titre:', error);
    }
  };

  const handleExportPDF = async (includeSolutions = false) => {
    try {
      const token = localStorage.getItem('lemaitremot_session_token');
      
      // P3.1 HOTFIX: Export PDF avec withCredentials
      // PR6: Ajouter le paramètre layout (eco par défaut)
      const response = await axios.post(
        `${API}/user/sheets/${sheet_uid}/export-pdf?include_solutions=${includeSolutions}&layout=${pdfLayout}`,
        {},
        {
          headers: { 'X-Session-Token': token },
          responseType: 'blob',
          withCredentials: true
        }
      );
      
      // Créer un blob et télécharger
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${sheet.title || 'fiche'}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      toast({
        title: "✅ PDF généré",
        description: "Le PDF a été téléchargé",
        variant: "default"
      });
    } catch (error) {
      console.error('Erreur export PDF:', error);
      toast({
        title: "Erreur",
        description: "Impossible de générer le PDF",
        variant: "destructive"
      });
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
        <Header />
        <div className="container mx-auto px-4 py-8">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">Chargement...</span>
          </div>
        </div>
      </div>
    );
  }

  if (!sheet) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header />
      
      <div className="container mx-auto px-4 py-8">
        {/* En-tête */}
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="outline"
              onClick={() => navigate('/mes-fiches')}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour
            </Button>
            <Input
              value={sheet.title}
              onChange={(e) => setSheet({ ...sheet, title: e.target.value })}
              onBlur={(e) => handleUpdateTitle(e.target.value)}
              className="text-2xl font-bold border-none shadow-none focus-visible:ring-0"
            />
          </div>
          <div className="flex items-center gap-4">
            {/* Toggle Layout PDF - PR6 */}
            <div className="flex items-center gap-2 p-2 bg-gray-50 rounded-md">
              <Label htmlFor="pdf-layout-toggle-edit" className="text-sm font-medium cursor-pointer">
                Éco (2 colonnes)
              </Label>
              <Switch
                id="pdf-layout-toggle-edit"
                checked={pdfLayout === "eco"}
                onCheckedChange={(checked) => setPdfLayout(checked ? "eco" : "classic")}
              />
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => handleExportPDF(false)}
              >
                <Download className="h-4 w-4 mr-2" />
                PDF Sujet
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExportPDF(true)}
              >
                <Download className="h-4 w-4 mr-2" />
                PDF Corrigé
              </Button>
            </div>
          </div>
        </div>

        {/* Layout 2 colonnes */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Colonne gauche : Liste des exercices */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Exercices</CardTitle>
                <Button
                  size="sm"
                  onClick={handleOpenAddDialog}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Ajouter
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {exercises.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                  <p>Aucun exercice dans cette fiche</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleOpenAddDialog}
                    className="mt-4"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Ajouter un exercice
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {exercises.map((exercise, index) => (
                    <div
                      key={exercise.exercise_uid}
                      draggable
                      onDragStart={() => handleDragStart(index)}
                      onDragOver={(e) => handleDragOver(e, index)}
                      onDrop={(e) => handleDrop(e, index)}
                      className={`
                        flex items-center gap-3 p-3 border rounded-lg cursor-move
                        hover:bg-gray-50 transition-colors
                        ${draggedIndex === index ? 'opacity-50' : ''}
                      `}
                    >
                      <GripVertical className="h-5 w-5 text-gray-400" />
                      <div className="flex-1">
                        <div className="font-medium">
                          Exercice {index + 1}
                        </div>
                        <div className="text-sm text-gray-500">
                          {exercise.code_officiel || 'Sans code'}
                        </div>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleRemoveExercise(exercise.exercise_uid)}
                      >
                        <Trash2 className="h-4 w-4 text-red-600" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Colonne droite : Aperçu (sticky) */}
          <div className="lg:sticky lg:top-4 lg:self-start">
            <Card>
              <CardHeader>
                <CardTitle>Aperçu</CardTitle>
                <CardDescription>
                  {exercises.length} exercice{exercises.length > 1 ? 's' : ''}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div ref={previewRef} className="space-y-6 max-h-[600px] overflow-y-auto">
                  {exercises.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">
                      Ajoutez des exercices pour voir l'aperçu
                    </p>
                  ) : (
                    exercises.map((exercise, index) => (
                      <div key={exercise.exercise_uid} className="border-b pb-6 last:border-0">
                        <div className="mb-2 flex items-center justify-between">
                          <h4 className="font-semibold">Exercice {index + 1}</h4>
                          <Badge variant="outline">{exercise.difficulty}</Badge>
                        </div>
                        <div
                          className="prose prose-sm max-w-none"
                          dangerouslySetInnerHTML={{ __html: exercise.enonce_html || '' }}
                        />
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Dialog ajouter exercice */}
      <Dialog open={showAddDialog} onOpenChange={setShowAddDialog}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Ajouter un exercice</DialogTitle>
            <DialogDescription>
              Sélectionnez un exercice depuis "Mes exercices"
            </DialogDescription>
          </DialogHeader>
          
          {loadingExercises ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
            </div>
          ) : availableExercises.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Aucun exercice disponible</p>
              <p className="text-sm mt-2">
                Créez d'abord des exercices depuis "Mes exercices"
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {availableExercises.map((exercise) => (
                <div
                  key={exercise.exercise_uid}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div>
                    <div className="font-medium">{exercise.code_officiel || 'Sans code'}</div>
                    <div className="text-sm text-gray-500">{exercise.difficulty}</div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => handleAddExercise(exercise.exercise_uid)}
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Ajouter
                  </Button>
                </div>
              ))}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default SheetEditPageP31;

