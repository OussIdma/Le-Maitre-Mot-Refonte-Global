import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '../ui/card';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Textarea } from '../ui/textarea';
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '../ui/select';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from '../ui/table';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Switch } from '../ui/switch';
import { 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  ChevronLeft,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  Loader2,
  BookOpen,
  Eye,
  ExternalLink,
  ArrowLeft,
  Sparkles,
  PlayCircle
} from 'lucide-react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import GeneratorVariablesPanel from './GeneratorVariablesPanel';
import DynamicPreviewModal from './DynamicPreviewModal';
import GeneratorParamsForm from './GeneratorParamsForm';
import { apiCall, fetchGeneratorsList } from '../../lib/adminApi';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Page d'administration des exercices d'un chapitre
 * Permet le CRUD sur les exercices figés des chapitres pilotes
 */
const ChapterExercisesAdminPage = () => {
  const { chapterCode } = useParams();
  const navigate = useNavigate();
  
  // État principal
  const [exercises, setExercises] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  // Types d'exercices disponibles (chargés depuis l'API)
  const [exerciseTypes, setExerciseTypes] = useState([]);
  
  // Filtres
  const [filterOffer, setFilterOffer] = useState('all');
  const [filterDifficulty, setFilterDifficulty] = useState('all');
  
  // Modal d'édition
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [editingExercise, setEditingExercise] = useState(null);
  const [formData, setFormData] = useState({
    family: 'CONVERSION',
    exercise_type: '',
    difficulty: 'facile',
    offer: 'free',
    enonce_html: '',
    solution_html: '',
    needs_svg: false,
    svg_enonce_brief: '',
    svg_solution_brief: '',
    // Champs pour exercices dynamiques
    is_dynamic: false,
    generator_key: '',
    enonce_template_html: '',
    solution_template_html: '',
    variables: null
  });
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  
  // Générateurs disponibles
  const [availableGenerators, setAvailableGenerators] = useState([]);
  
  // Modal de prévisualisation
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewExercise, setPreviewExercise] = useState(null);
  
  // Confirmation suppression
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [exerciseToDelete, setExerciseToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  
  // Messages
  const [operationMessage, setOperationMessage] = useState(null);
  
  // Preview dynamique (P2)
  const [dynamicPreviewOpen, setDynamicPreviewOpen] = useState(false);
  
  // Schéma du générateur sélectionné (P0.2)
  const [generatorSchema, setGeneratorSchema] = useState(null);
  
  // Familles disponibles (étendues pour dynamique)
  const families = ['CONVERSION', 'COMPARAISON', 'PERIMETRE', 'PROBLEME', 'DUREES', 'LECTURE_HORLOGE', 'CALCUL_DUREE', 'AGRANDISSEMENT_REDUCTION'];
  
  // Charger les types d'exercices et générateurs
  useEffect(() => {
    const fetchExerciseTypes = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/admin/exercises/pilot-chapters`);
        if (response.ok) {
          const data = await response.json();
          setExerciseTypes(data.exercise_types || []);
        }
      } catch (err) {
        console.error('Erreur chargement types:', err);
      }
    };
    
    const fetchGenerators = async () => {
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/exercises/generators`);
        if (response.ok) {
          const data = await response.json();
          // Gérer les deux formats: liste d'objets ou liste de strings
          const generators = data.generators || [];
          const keys = generators.map(g => typeof g === 'string' ? g : g.key);
          // Ajouter SYMETRIE_AXIALE_V2 si non présent (nouveau générateur)
          if (!keys.includes('SYMETRIE_AXIALE_V2')) {
            keys.push('SYMETRIE_AXIALE_V2');
          }
          setAvailableGenerators(keys);
        }
      } catch (err) {
        console.error('Erreur chargement générateurs:', err);
        setAvailableGenerators(['THALES_V1', 'SYMETRIE_AXIALE_V2']); // Fallback avec les deux
      }
    };
    
    fetchExerciseTypes();
    fetchGenerators();
  }, []);
  
  // Charger les exercices
  const fetchExercises = useCallback(async () => {
    if (!chapterCode) return;
    
    setLoading(true);
    setError(null);
    
    try {
      let url = `${BACKEND_URL}/api/admin/chapters/${chapterCode}/exercises`;
      const params = new URLSearchParams();
      
      if (filterOffer !== 'all') params.append('offer', filterOffer);
      if (filterDifficulty !== 'all') params.append('difficulty', filterDifficulty);
      
      if (params.toString()) url += `?${params.toString()}`;
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setExercises(data.exercises || []);
      setStats(data.stats || null);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [chapterCode, filterOffer, filterDifficulty]);
  
  useEffect(() => {
    fetchExercises();
  }, [fetchExercises]);
  
  // Effacer les messages
  useEffect(() => {
    if (operationMessage) {
      const timer = setTimeout(() => setOperationMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [operationMessage]);
  
  // Couleurs
  const getDifficultyColor = (difficulty) => {
    const colors = {
      'facile': 'bg-green-100 text-green-800',
      'moyen': 'bg-yellow-100 text-yellow-800',
      'difficile': 'bg-red-100 text-red-800'
    };
    return colors[difficulty] || 'bg-gray-100 text-gray-800';
  };
  
  const getOfferColor = (offer) => {
    return offer === 'pro' 
      ? 'bg-purple-100 text-purple-800 border-purple-300' 
      : 'bg-blue-100 text-blue-800 border-blue-300';
  };
  
  // Ouvrir modal création
  const handleOpenCreate = () => {
    setModalMode('create');
    setEditingExercise(null);
    setFormData({
      family: 'CONVERSION',
      exercise_type: '',
      difficulty: 'facile',
      offer: 'free',
      enonce_html: '',
      solution_html: getSolutionTemplate(),
      needs_svg: false,
      svg_enonce_brief: '',
      svg_solution_brief: '',
      is_dynamic: false,
      generator_key: '',
      enonce_template_html: '',
      solution_template_html: '',
      variables: null
    });
    setFormErrors({});
    setIsModalOpen(true);
  };
  
  // Template solution 4 étapes
  const getSolutionTemplate = () => {
    return `<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> </li>
  <li><strong>Méthode :</strong> </li>
  <li><strong>Calculs :</strong> </li>
  <li><strong>Conclusion :</strong> </li>
</ol>`;
  };
  
  // Template pour exercice dynamique
  const getDynamicTemplates = (generatorKey) => {
    if (generatorKey === 'THALES_V1' || generatorKey === 'THALES_V2') {
      return {
        enonce: `<p><strong>Agrandissement d'{{figure_type_article}} :</strong></p>
<p>On considère {{figure_type_article}} de côté <strong>{{cote_initial}} cm</strong>.</p>
<p>On effectue un <strong>{{transformation}}</strong> de coefficient <strong>{{coefficient_str}}</strong>.</p>
<p><em>Question :</em> Quelle est la mesure du côté de la figure obtenue ?</p>`,
        solution: `<h4>Correction détaillée</h4>
<ol>
  <li><strong>Compréhension :</strong> On a {{figure_type_article}} qu'on {{transformation_verbe}}.</li>
  <li><strong>Méthode :</strong> Multiplier chaque dimension par le coefficient.</li>
  <li><strong>Calculs :</strong> {{cote_initial}} × {{coefficient_str}} = <strong>{{cote_final}} cm</strong></li>
  <li><strong>Conclusion :</strong> La figure mesure <strong>{{cote_final}} cm</strong>.</li>
</ol>`
      };
    }
    if (generatorKey === 'SYMETRIE_AXIALE_V2') {
      return {
        enonce: `<p><strong>Symétrie axiale</strong></p>
<p>Soit {{figure_description}} <strong>{{points_labels}}</strong> et la droite {{axe_label}} d'équation <strong>{{axe_equation}}</strong>.</p>
<p><em>Construire le symétrique de {{points_labels}} par rapport à {{axe_label}}.</em></p>`,
        solution: `<h4>Correction</h4>
<ol>
  <li><strong>Méthode :</strong> Pour chaque point, tracer la perpendiculaire à {{axe_label}} passant par ce point.</li>
  <li><strong>Report des distances :</strong> Reporter la même distance de l'autre côté de l'axe.</li>
  <li><strong>Résultat :</strong> Les symétriques sont : <strong>{{points_symmetric_labels}}</strong></li>
</ol>`
      };
    }
    return { enonce: '', solution: '' };
  };
  
  // Ouvrir modal édition
  const handleOpenEdit = (exercise) => {
    setModalMode('edit');
    setEditingExercise(exercise);
    setFormData({
      family: exercise.family,
      exercise_type: exercise.exercise_type || '',
      difficulty: exercise.difficulty,
      offer: exercise.offer,
      enonce_html: exercise.enonce_html || '',
      solution_html: exercise.solution_html || '',
      needs_svg: exercise.needs_svg || false,
      svg_enonce_brief: exercise.svg_enonce_brief || '',
      svg_solution_brief: exercise.svg_solution_brief || '',
      is_dynamic: exercise.is_dynamic || false,
      generator_key: exercise.generator_key || '',
      enonce_template_html: exercise.enonce_template_html || '',
      solution_template_html: exercise.solution_template_html || '',
      variables: exercise.variables || null
    });
    setFormErrors({});
    setIsModalOpen(true);
  };
  
  // Fermer modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingExercise(null);
    setFormErrors({});
  };
  
  // Prévisualiser
  const handlePreview = (exercise) => {
    setPreviewExercise(exercise);
    setPreviewOpen(true);
  };
  
  // Valider le formulaire
  const validateForm = () => {
    const errors = {};
    
    // Validation pour exercices STATIQUES
    if (!formData.is_dynamic) {
      if (!formData.enonce_html.trim()) {
        errors.enonce_html = "L'énoncé est requis";
      }
      
      if (!formData.solution_html.trim()) {
        errors.solution_html = 'La solution est requise';
      }
      
      // Vérifier pas de LaTeX
      if (formData.enonce_html.includes('$') || formData.solution_html.includes('$')) {
        errors.latex = 'Le contenu ne doit pas contenir de LaTeX ($). Utilisez du HTML pur.';
      }
      
      // Vérifier structure solution
      if (!formData.solution_html.includes('<ol>') || !formData.solution_html.includes('<li>')) {
        errors.solution_html = 'La solution doit contenir une structure en 4 étapes (<ol><li>...)';
      }
    }
    
    // Validation pour exercices DYNAMIQUES
    if (formData.is_dynamic) {
      if (!formData.generator_key) {
        errors.generator_key = 'Le générateur est requis pour les exercices dynamiques';
      }
      
      if (!formData.enonce_template_html?.trim()) {
        errors.enonce_template_html = 'Le template énoncé est requis';
      }
      
      if (!formData.solution_template_html?.trim()) {
        errors.solution_template_html = 'Le template solution est requis';
      }
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // Soumettre avec gestion robuste des erreurs (P0.1)
  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setSaving(true);
    
    // Timeout controller
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);
    
    try {
      const url = modalMode === 'create'
        ? `${BACKEND_URL}/api/admin/chapters/${chapterCode}/exercises`
        : `${BACKEND_URL}/api/admin/chapters/${chapterCode}/exercises/${editingExercise.id}`;
      
      const method = modalMode === 'create' ? 'POST' : 'PUT';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail?.message || data.detail || 'Erreur lors de la sauvegarde');
      }
      
      setOperationMessage({
        type: 'success',
        text: data.message || `Exercice ${modalMode === 'create' ? 'créé' : 'modifié'} avec succès`
      });
      
      handleCloseModal();
      fetchExercises();
      
    } catch (err) {
      clearTimeout(timeoutId);
      
      let errorMessage = err.message;
      if (err.name === 'AbortError') {
        errorMessage = 'La requête a expiré. Vérifiez votre connexion et réessayez.';
      }
      
      setOperationMessage({
        type: 'error',
        text: errorMessage,
        showRetry: true
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Ouvrir confirmation suppression
  const handleOpenDelete = (exercise) => {
    setExerciseToDelete(exercise);
    setDeleteConfirmOpen(true);
  };
  
  // Confirmer suppression
  const handleConfirmDelete = async () => {
    if (!exerciseToDelete) return;
    
    setDeleting(true);
    
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/admin/chapters/${chapterCode}/exercises/${exerciseToDelete.id}`,
        { method: 'DELETE' }
      );
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail || 'Erreur lors de la suppression');
      }
      
      setOperationMessage({
        type: 'success',
        text: data.message || 'Exercice supprimé avec succès'
      });
      
      setDeleteConfirmOpen(false);
      setExerciseToDelete(null);
      fetchExercises();
      
    } catch (err) {
      setOperationMessage({
        type: 'error',
        text: err.message
      });
    } finally {
      setDeleting(false);
    }
  };
  
  // Tronquer le texte HTML
  const truncateHtml = (html, maxLength = 80) => {
    const text = html.replace(/<[^>]*>/g, '');
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
  };
  
  // Ouvrir la page élève avec le chapitre pré-sélectionné
  const handleOpenStudentView = () => {
    const url = `/generate?code_officiel=${chapterCode}&difficulte=moyen`;
    window.open(url, '_blank');
  };
  
  // Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Chargement des exercices...</p>
        </div>
      </div>
    );
  }
  
  // Erreur
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <div className="mt-4 flex gap-2">
            <Button onClick={() => navigate('/admin/curriculum')}>
              <ChevronLeft className="h-4 w-4 mr-2" />
              Retour au curriculum
            </Button>
            <Button onClick={fetchExercises}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Réessayer
            </Button>
          </div>
        </div>
      </div>
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Bouton Retour amélioré */}
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => navigate('/admin/curriculum')}
                className="flex items-center gap-1"
              >
                <ArrowLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Retour curriculum</span>
              </Button>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <BookOpen className="h-5 w-5 text-blue-600" />
                  Exercices {chapterCode}
                </h1>
                <p className="text-sm text-gray-500">
                  Gestion des exercices figés • {exercises.length} exercice{exercises.length > 1 ? 's' : ''}
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              {/* Bouton Ouvrir côté élève */}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={handleOpenStudentView}
                className="flex items-center gap-1"
              >
                <ExternalLink className="h-4 w-4" />
                <span className="hidden sm:inline">👀 Côté élève</span>
              </Button>
              <Button variant="outline" size="sm" onClick={fetchExercises}>
                <RefreshCw className="h-4 w-4 mr-1" />
                <span className="hidden sm:inline">Actualiser</span>
              </Button>
              <Button size="sm" onClick={handleOpenCreate}>
                <Plus className="h-4 w-4 mr-1" />
                Ajouter
              </Button>
            </div>
          </div>
        </div>
      </header>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Message avec bouton Réessayer (P0.1) */}
        {operationMessage && (
          <Alert 
            className={`mb-4 ${operationMessage.type === 'success' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}
          >
            {operationMessage.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription className={`flex items-center justify-between ${operationMessage.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
              <span>{operationMessage.text}</span>
              {operationMessage.showRetry && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSubmit}
                  className="ml-4"
                >
                  <RefreshCw className="h-3 w-3 mr-1" />
                  Réessayer
                </Button>
              )}
            </AlertDescription>
          </Alert>
        )}
        
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">Total</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stats.total}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">Free</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-blue-600">{stats.by_offer?.free || 0}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">Pro</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-purple-600">{stats.by_offer?.pro || 0}</div>
              </CardContent>
            </Card>
            
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-gray-500">Familles</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-gray-900">
                  {Object.keys(stats.by_family || {}).length}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
        
        {/* Filtres */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="w-full sm:w-48">
                <Label className="text-xs text-gray-500 mb-1 block">Offre</Label>
                <Select value={filterOffer} onValueChange={setFilterOffer}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes les offres</SelectItem>
                    <SelectItem value="free">Free</SelectItem>
                    <SelectItem value="pro">Pro</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div className="w-full sm:w-48">
                <Label className="text-xs text-gray-500 mb-1 block">Difficulté</Label>
                <Select value={filterDifficulty} onValueChange={setFilterDifficulty}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Toutes</SelectItem>
                    <SelectItem value="facile">Facile</SelectItem>
                    <SelectItem value="moyen">Moyen</SelectItem>
                    <SelectItem value="difficile">Difficile</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
        
        {/* Tableau */}
        <Card>
          <CardHeader>
            <CardTitle>Liste des exercices</CardTitle>
            <CardDescription>
              Cliquez sur un exercice pour le modifier
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">ID</TableHead>
                    <TableHead className="w-32">Famille</TableHead>
                    <TableHead className="w-24">Difficulté</TableHead>
                    <TableHead className="w-20">Offre</TableHead>
                    <TableHead>Énoncé (aperçu)</TableHead>
                    <TableHead className="w-16 text-center">SVG</TableHead>
                    <TableHead className="w-32 text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {exercises.map((exercise) => (
                    <TableRow key={exercise.id} className="hover:bg-gray-50">
                      <TableCell className="font-mono font-medium">
                        #{exercise.id}
                      </TableCell>
                      
                      <TableCell>
                        <Badge variant="outline" className="font-mono text-xs">
                          {exercise.family}
                        </Badge>
                      </TableCell>
                      
                      <TableCell>
                        <Badge className={`${getDifficultyColor(exercise.difficulty)} text-xs`}>
                          {exercise.difficulty}
                        </Badge>
                      </TableCell>
                      
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={`${getOfferColor(exercise.offer)} text-xs`}
                        >
                          {exercise.offer}
                        </Badge>
                      </TableCell>
                      
                      <TableCell className="text-sm text-gray-600">
                        {truncateHtml(exercise.enonce_html)}
                      </TableCell>
                      
                      <TableCell className="text-center">
                        {exercise.needs_svg ? (
                          <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                        ) : (
                          <span className="text-gray-300">—</span>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center justify-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handlePreview(exercise)}
                            className="h-8 w-8 p-0"
                            title="Prévisualiser"
                          >
                            <Eye className="h-4 w-4 text-gray-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenEdit(exercise)}
                            className="h-8 w-8 p-0"
                            title="Modifier"
                          >
                            <Pencil className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenDelete(exercise)}
                            className="h-8 w-8 p-0"
                            title="Supprimer"
                          >
                            <Trash2 className="h-4 w-4 text-red-600" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            
            {exercises.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <BookOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>Aucun exercice pour ce chapitre</p>
                <Button onClick={handleOpenCreate} className="mt-4">
                  <Plus className="h-4 w-4 mr-2" />
                  Créer le premier exercice
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
      
      {/* Modal Création/Édition */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {modalMode === 'create' ? 'Créer un exercice' : `Modifier l'exercice #${editingExercise?.id}`}
            </DialogTitle>
            <DialogDescription>
              Contenu en HTML pur uniquement. Pas de LaTeX, pas de Markdown.
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            {/* Famille, Difficulté, Offer sur une ligne */}
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label className="text-sm">Famille *</Label>
                <Select 
                  value={formData.family} 
                  onValueChange={(v) => setFormData(p => ({...p, family: v}))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {families.map(f => (
                      <SelectItem key={f} value={f}>{f}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label className="text-sm">Difficulté *</Label>
                <Select 
                  value={formData.difficulty} 
                  onValueChange={(v) => setFormData(p => ({...p, difficulty: v}))}
                >
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
              
              <div>
                <Label className="text-sm">Offre *</Label>
                <Select 
                  value={formData.offer} 
                  onValueChange={(v) => setFormData(p => ({...p, offer: v}))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="free">Free (1-10)</SelectItem>
                    <SelectItem value="pro">Pro (11-20)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {/* Toggle Exercice Dynamique */}
            <div className="p-4 bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg border border-purple-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-lg">🎲</span>
                  <Label className="text-sm font-medium text-purple-800">Exercice dynamique (template)</Label>
                </div>
                <Switch
                  checked={formData.is_dynamic}
                  onCheckedChange={(checked) => {
                    setFormData(p => ({
                      ...p, 
                      is_dynamic: checked,
                      generator_key: checked ? 'THALES_V1' : '',
                      enonce_template_html: checked ? getDynamicTemplates('THALES_V1').enonce : '',
                      solution_template_html: checked ? getDynamicTemplates('THALES_V1').solution : ''
                    }));
                  }}
                />
              </div>
              
              {formData.is_dynamic && (
                <div className="space-y-4 mt-4">
                  <div className="text-xs text-purple-600 bg-purple-100 p-2 rounded">
                    💡 Les exercices dynamiques utilisent des templates avec variables <code>{'{{variable}}'}</code> 
                    et génèrent des variantes infinies.
                  </div>
                  
                  {/* Sélecteur de générateur */}
                  <div>
                    <Label className="text-sm">Générateur *</Label>
                    <Select 
                      value={formData.generator_key || 'THALES_V1'} 
                      onValueChange={(v) => {
                        const templates = getDynamicTemplates(v);
                        setFormData(p => ({
                          ...p, 
                          generator_key: v,
                          enonce_template_html: templates.enonce,
                          solution_template_html: templates.solution
                        }));
                      }}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Choisir un générateur..." />
                      </SelectTrigger>
                      <SelectContent>
                        {availableGenerators.map(g => (
                          <SelectItem key={g} value={g}>
                            {g === 'THALES_V1' ? '🔺 THALES_V1 - Agrandissements/Réductions' : 
                             g === 'SYMETRIE_AXIALE_V2' ? '📐 SYMETRIE_AXIALE_V2 - Symétrie Axiale' :
                             g === 'THALES_V2' ? '🔺 THALES_V2 - Agrandissements/Réductions' : g}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  {/* Panneau des variables disponibles (P0.2) */}
                  {formData.generator_key && (
                    <GeneratorVariablesPanel 
                      generatorKey={formData.generator_key}
                      onTemplatesLoaded={(templates) => {
                        // Ne mettre à jour que si les templates sont vides
                        if (!formData.enonce_template_html && !formData.solution_template_html) {
                          setFormData(p => ({
                            ...p,
                            enonce_template_html: templates.enonce,
                            solution_template_html: templates.solution
                          }));
                        }
                      }}
                    />
                  )}
                  
                  {/* Template énoncé */}
                  <div>
                    <Label className="text-sm">Template énoncé *</Label>
                    <Textarea
                      value={formData.enonce_template_html}
                      onChange={(e) => setFormData(p => ({...p, enonce_template_html: e.target.value}))}
                      placeholder="<p>Exercice avec {{variable}}...</p>"
                      className="font-mono text-sm min-h-[100px] bg-white"
                    />
                    {formErrors.enonce_template_html && (
                      <p className="text-xs text-red-500 mt-1">{formErrors.enonce_template_html}</p>
                    )}
                  </div>
                  
                  {/* Template solution */}
                  <div>
                    <Label className="text-sm">Template solution *</Label>
                    <Textarea
                      value={formData.solution_template_html}
                      onChange={(e) => setFormData(p => ({...p, solution_template_html: e.target.value}))}
                      placeholder="<h4>Correction</h4>..."
                      className="font-mono text-sm min-h-[100px] bg-white"
                    />
                    {formErrors.solution_template_html && (
                      <p className="text-xs text-red-500 mt-1">{formErrors.solution_template_html}</p>
                    )}
                  </div>
                  
                  {/* Bouton Preview (P2) */}
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => setDynamicPreviewOpen(true)}
                    className="w-full border-purple-300 text-purple-700 hover:bg-purple-50"
                    disabled={!formData.enonce_template_html || !formData.solution_template_html}
                  >
                    <PlayCircle className="h-4 w-4 mr-2" />
                    Prévisualiser un exemple généré
                  </Button>
                </div>
              )}
            </div>
            
            {/* Type d'exercice (optionnel) - seulement si non dynamique */}
            {!formData.is_dynamic && (
              <div>
                <Label className="text-sm">Type exercice (optionnel)</Label>
                <Select 
                  value={formData.exercise_type || ''} 
                  onValueChange={(v) => setFormData(p => ({...p, exercise_type: v === 'none' ? '' : v}))}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Sélectionner un type..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">-- Aucun (auto) --</SelectItem>
                    {exerciseTypes.map(t => (
                      <SelectItem key={t.value} value={t.value}>
                        {t.label} - {t.description}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <p className="text-xs text-gray-500 mt-1">
                  Le type pilote automatiquement le comportement des figures (énoncé / solution).
                </p>
              </div>
            )}
            
            {/* Énoncé - seulement si non dynamique */}
            {!formData.is_dynamic && (
              <div>
                <Label className="text-sm">Énoncé HTML *</Label>
                <Textarea
                  value={formData.enonce_html}
                  onChange={(e) => setFormData(p => ({...p, enonce_html: e.target.value}))}
                  placeholder="<p><strong>Titre :</strong> Description de l'exercice...</p>"
                  className={`font-mono text-sm min-h-[120px] ${formErrors.enonce_html ? 'border-red-500' : ''}`}
                />
                {formErrors.enonce_html && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.enonce_html}</p>
                )}
              </div>
            )}
            
            {/* Solution - seulement si non dynamique */}
            {!formData.is_dynamic && (
              <div>
                <Label className="text-sm">Solution HTML (4 étapes) *</Label>
                <Textarea
                  value={formData.solution_html}
                  onChange={(e) => setFormData(p => ({...p, solution_html: e.target.value}))}
                  placeholder={getSolutionTemplate()}
                  className={`font-mono text-sm min-h-[200px] ${formErrors.solution_html ? 'border-red-500' : ''}`}
                />
                {formErrors.solution_html && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.solution_html}</p>
                )}
              </div>
            )}
            
            {/* Erreur LaTeX */}
            {formErrors.latex && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{formErrors.latex}</AlertDescription>
              </Alert>
            )}
            
            {/* SVG requis */}
            <div className="flex items-center gap-2">
              <Switch
                checked={formData.needs_svg}
                onCheckedChange={(checked) => setFormData(p => ({...p, needs_svg: checked}))}
              />
              <Label className="text-sm">Nécessite un SVG (schéma)</Label>
              {formData.is_dynamic && (
                <Badge variant="outline" className="ml-2 text-purple-600 border-purple-300">
                  Auto-généré par {formData.generator_key || 'THALES_V1'}
                </Badge>
              )}
            </div>
            
            {/* Champs SVG conditionnels - affichés uniquement si needs_svg est true ET non dynamique */}
            {formData.needs_svg && !formData.is_dynamic && (
              <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                  <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                    <circle cx="8.5" cy="8.5" r="1.5"/>
                    <polyline points="21 15 16 10 5 21"/>
                  </svg>
                  Configuration des figures SVG
                </div>
                
                <div>
                  <Label className="text-sm">Brief SVG pour l'énoncé</Label>
                  <Input
                    value={formData.svg_enonce_brief}
                    onChange={(e) => setFormData(p => ({...p, svg_enonce_brief: e.target.value}))}
                    placeholder="Ex: Horloge sans aiguilles, Rectangle 6cm × 4cm..."
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Laissez vide pour utiliser le comportement par défaut du type d'exercice.
                  </p>
                </div>
                
                <div>
                  <Label className="text-sm">Brief SVG pour la solution</Label>
                  <Input
                    value={formData.svg_solution_brief}
                    onChange={(e) => setFormData(p => ({...p, svg_solution_brief: e.target.value}))}
                    placeholder="Ex: Horloge avec aiguilles à 9h20, Figure symétrique complète..."
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Si absent, utilise le brief de l'énoncé ou le comportement par défaut.
                  </p>
                </div>
                
                {/* Info sur le type sélectionné */}
                {formData.exercise_type && (
                  <div className="text-xs text-blue-700 bg-blue-50 p-2 rounded">
                    💡 Type <strong>{formData.exercise_type}</strong> : 
                    {formData.exercise_type === 'PLACER_AIGUILLES' && " Figure vide (énoncé) → Figure complète (solution)"}
                    {formData.exercise_type === 'LECTURE_HEURE' && " Figure avec aiguilles dans l'énoncé uniquement"}
                    {formData.exercise_type === 'SYMETRIE_AXIALE' && " Axe seul (énoncé) → Figure symétrique (solution)"}
                    {formData.exercise_type === 'PERIMETRE' && " Forme géométrique dans l'énoncé"}
                  </div>
                )}
              </div>
            )}
            
            {/* Aide */}
            <div className="bg-blue-50 p-3 rounded-md text-sm text-blue-800">
              <p className="font-medium mb-1">💡 Rappel HTML :</p>
              <ul className="list-disc list-inside text-xs space-y-1">
                <li><code>&lt;strong&gt;</code> pour le gras, <code>&lt;em&gt;</code> pour italique</li>
                <li><code>×</code> pour la multiplication, <code>÷</code> pour la division</li>
                <li>Structure solution : <code>&lt;ol&gt;&lt;li&gt;Étape 1&lt;/li&gt;...&lt;/ol&gt;</code></li>
              </ul>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={handleCloseModal}>
              <X className="h-4 w-4 mr-2" />
              Annuler
            </Button>
            <Button onClick={handleSubmit} disabled={saving}>
              {saving ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-2" />
              )}
              {modalMode === 'create' ? 'Créer' : 'Enregistrer'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Modal Prévisualisation */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="sm:max-w-[700px] max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Eye className="h-5 w-5" />
              Exercice #{previewExercise?.id}
            </DialogTitle>
            <DialogDescription>
              <div className="flex gap-2 mt-2">
                <Badge className={getDifficultyColor(previewExercise?.difficulty)}>
                  {previewExercise?.difficulty}
                </Badge>
                <Badge variant="outline" className={getOfferColor(previewExercise?.offer)}>
                  {previewExercise?.offer}
                </Badge>
                <Badge variant="outline">{previewExercise?.family}</Badge>
              </div>
            </DialogDescription>
          </DialogHeader>
          
          {previewExercise && (
            <div className="space-y-4 py-4">
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Énoncé</h4>
                <div 
                  className="bg-gray-50 p-4 rounded-md prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: previewExercise.enonce_html }}
                />
              </div>
              
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Solution</h4>
                <div 
                  className="bg-green-50 p-4 rounded-md prose prose-sm max-w-none"
                  dangerouslySetInnerHTML={{ __html: previewExercise.solution_html }}
                />
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setPreviewOpen(false)}>
              Fermer
            </Button>
            <Button onClick={() => { setPreviewOpen(false); handleOpenEdit(previewExercise); }}>
              <Pencil className="h-4 w-4 mr-2" />
              Modifier
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Dialog Suppression */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="text-red-600">Confirmer la suppression</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer exercice #{exerciseToDelete?.id} ?
              <br />
              <span className="text-red-500">Cette action est irréversible.</span>
            </DialogDescription>
          </DialogHeader>
          
          {exerciseToDelete && (
            <div className="py-4">
              <div className="bg-gray-50 p-3 rounded-md text-sm">
                <p className="text-gray-600">{truncateHtml(exerciseToDelete.enonce_html, 150)}</p>
              </div>
            </div>
          )}
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteConfirmOpen(false)}>
              Annuler
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleConfirmDelete}
              disabled={deleting}
            >
              {deleting ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4 mr-2" />
              )}
              Supprimer
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      
      {/* Modal Preview Dynamique (P2) */}
      <DynamicPreviewModal
        open={dynamicPreviewOpen}
        onOpenChange={setDynamicPreviewOpen}
        generatorKey={formData.generator_key}
        enonceTemplate={formData.enonce_template_html}
        solutionTemplate={formData.solution_template_html}
        difficulty={formData.difficulty}
      />
    </div>
  );
};

export default ChapterExercisesAdminPage;
