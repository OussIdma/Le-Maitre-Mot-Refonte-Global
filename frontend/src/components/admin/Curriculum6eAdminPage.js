import React, { useState, useEffect, useMemo, useCallback } from 'react';
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
  Search, 
  Filter, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  FileCode2, 
  LayoutGrid,
  ChevronLeft,
  Plus,
  Pencil,
  Trash2,
  Save,
  X,
  Loader2,
  BookOpen
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Page d'administration du curriculum 6e
 * Version 2.0 - Lecture et Édition
 */
const Curriculum6eAdminPage = () => {
  const navigate = useNavigate();
  
  // Chapitres pilotes chargés dynamiquement depuis l'API
  const [pilotChapterCodes, setPilotChapterCodes] = useState(new Set());
  
  // État principal
  const [curriculum, setCurriculum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomaine, setSelectedDomaine] = useState('all');
  
  // État pour les options disponibles
  const [availableOptions, setAvailableOptions] = useState({
    generators: [],
    domaines: [],
    statuts: ['prod', 'beta', 'hidden']
  });
  
  // État pour le modal d'édition
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' ou 'edit'
  const [editingChapter, setEditingChapter] = useState(null);
  const [formData, setFormData] = useState({
    code_officiel: '',
    libelle: '',
    domaine: 'Nombres et calculs',
    chapitre_backend: '',
    exercise_types: [],
    schema_requis: false,
    difficulte_min: 1,
    difficulte_max: 3,
    statut: 'beta',
    tags: []
  });
  const [formErrors, setFormErrors] = useState({});
  const [saving, setSaving] = useState(false);
  
  // État pour la confirmation de suppression
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [chapterToDelete, setChapterToDelete] = useState(null);
  const [deleting, setDeleting] = useState(false);
  
  // État pour le succès/erreur des opérations
  const [operationMessage, setOperationMessage] = useState(null);
  
  // Charger les données au montage
  useEffect(() => {
    fetchCurriculum();
    fetchAvailableOptions();
    fetchPilotChapters();
  }, []);
  
  // Charger la liste des chapitres pilotes depuis l'API
  const fetchPilotChapters = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/exercises/pilot-chapters`);
      if (response.ok) {
        const data = await response.json();
        const codes = new Set(data.pilot_chapters.map(ch => ch.code));
        setPilotChapterCodes(codes);
      }
    } catch (err) {
      console.error('Erreur chargement chapitres pilotes:', err);
      // Fallback en dur si l'API échoue
      setPilotChapterCodes(new Set(['6e_GM07', '6e_GM08']));
    }
  };
  
  // Helpers pour déterminer si un chapitre est pilote/éditable
  const isPilotChapter = (code) => pilotChapterCodes.has(code);
  const isEditableChapter = (code) => isPilotChapter(code); // Pour l'instant, éditable = pilote
  
  // Effacer le message après 5 secondes
  useEffect(() => {
    if (operationMessage) {
      const timer = setTimeout(() => setOperationMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [operationMessage]);
  
  const fetchCurriculum = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/curriculum/6e`);
      
      if (!response.ok) {
        if (response.status === 403) {
          throw new Error("Accès admin désactivé. Contactez l'administrateur.");
        }
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      setCurriculum(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const fetchAvailableOptions = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/admin/curriculum/options`);
      if (response.ok) {
        const data = await response.json();
        setAvailableOptions(data);
      }
    } catch (err) {
      console.error('Erreur chargement options:', err);
    }
  };
  
  // Filtrer les chapitres
  const filteredChapitres = useMemo(() => {
    if (!curriculum?.chapitres) return [];
    
    return curriculum.chapitres.filter(chapitre => {
      const matchesSearch = searchTerm === '' || 
        chapitre.code_officiel.toLowerCase().includes(searchTerm.toLowerCase()) ||
        chapitre.libelle.toLowerCase().includes(searchTerm.toLowerCase());
      
      const matchesDomaine = selectedDomaine === 'all' || 
        chapitre.domaine === selectedDomaine;
      
      return matchesSearch && matchesDomaine;
    });
  }, [curriculum, searchTerm, selectedDomaine]);
  
  // Liste des domaines uniques
  const domaines = useMemo(() => {
    if (!curriculum?.chapitres) return [];
    return [...new Set(curriculum.chapitres.map(c => c.domaine))];
  }, [curriculum]);
  
  // Couleurs
  const getDomaineColor = (domaine) => {
    const colors = {
      'Nombres et calculs': 'bg-blue-100 text-blue-800 border-blue-200',
      'Géométrie': 'bg-green-100 text-green-800 border-green-200',
      'Grandeurs et mesures': 'bg-orange-100 text-orange-800 border-orange-200',
      'Organisation et gestion de données': 'bg-purple-100 text-purple-800 border-purple-200'
    };
    return colors[domaine] || 'bg-gray-100 text-gray-800 border-gray-200';
  };
  
  const getStatusColor = (statut) => {
    const colors = {
      'prod': 'bg-green-100 text-green-800',
      'beta': 'bg-yellow-100 text-yellow-800',
      'hidden': 'bg-gray-100 text-gray-500'
    };
    return colors[statut] || 'bg-gray-100 text-gray-800';
  };
  
  // Ouvrir le modal pour créer
  const handleOpenCreate = () => {
    setModalMode('create');
    setEditingChapter(null);
    setFormData({
      code_officiel: '',
      libelle: '',
      domaine: 'Nombres et calculs',
      chapitre_backend: '',
      exercise_types: [],
      schema_requis: false,
      difficulte_min: 1,
      difficulte_max: 3,
      statut: 'beta',
      tags: []
    });
    setFormErrors({});
    setIsModalOpen(true);
  };
  
  // Ouvrir le modal pour éditer
  const handleOpenEdit = (chapitre) => {
    setModalMode('edit');
    setEditingChapter(chapitre);
    setFormData({
      code_officiel: chapitre.code_officiel,
      libelle: chapitre.libelle,
      domaine: chapitre.domaine,
      chapitre_backend: chapitre.chapitre_backend || '',
      exercise_types: chapitre.generateurs || [],
      schema_requis: chapitre.schema_requis || false,
      difficulte_min: chapitre.difficulte_min || 1,
      difficulte_max: chapitre.difficulte_max || 3,
      statut: chapitre.statut,
      tags: chapitre.tags || []
    });
    setFormErrors({});
    setIsModalOpen(true);
  };
  
  // Fermer le modal
  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingChapter(null);
    setFormErrors({});
  };
  
  // Valider le formulaire
  const validateForm = () => {
    const errors = {};
    
    // En mode édition, le code_officiel est read-only donc pas de validation
    if (modalMode === 'create') {
      if (!formData.code_officiel.trim()) {
        errors.code_officiel = 'Le code officiel est requis';
      } else if (!/^(6e|5e|4e|3e|2nde|1ere|term)_[A-Z0-9]+(_[A-Z0-9]+)*$/i.test(formData.code_officiel)) {
        errors.code_officiel = 'Format invalide (ex: 6e_N01, 6e_GM07, 6e_TESTS_DYN)';
      }
    }
    
    if (!formData.libelle.trim()) {
      errors.libelle = 'Le libellé est requis';
    }
    
    if (formData.difficulte_min > formData.difficulte_max) {
      errors.difficulte = 'La difficulté min doit être ≤ difficulté max';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };
  
  // Soumettre le formulaire
  const handleSubmit = async () => {
    if (!validateForm()) return;
    
    setSaving(true);
    
    try {
      const url = modalMode === 'create'
        ? `${BACKEND_URL}/api/admin/curriculum/6e/chapters`
        : `${BACKEND_URL}/api/admin/curriculum/6e/chapters/${editingChapter.code_officiel}`;
      
      const method = modalMode === 'create' ? 'POST' : 'PUT';
      
      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail?.message || data.detail || 'Erreur lors de la sauvegarde');
      }
      
      setOperationMessage({
        type: 'success',
        text: data.message || `Chapitre ${modalMode === 'create' ? 'créé' : 'modifié'} avec succès`
      });
      
      handleCloseModal();
      fetchCurriculum();
      
    } catch (err) {
      setOperationMessage({
        type: 'error',
        text: err.message
      });
    } finally {
      setSaving(false);
    }
  };
  
  // Ouvrir la confirmation de suppression
  const handleOpenDelete = (chapitre) => {
    setChapterToDelete(chapitre);
    setDeleteConfirmOpen(true);
  };
  
  // Confirmer la suppression
  const handleConfirmDelete = async () => {
    if (!chapterToDelete) return;
    
    setDeleting(true);
    
    try {
      const response = await fetch(
        `${BACKEND_URL}/api/admin/curriculum/6e/chapters/${chapterToDelete.code_officiel}`,
        { method: 'DELETE' }
      );
      
      const data = await response.json();
      
      if (!response.ok) {
        throw new Error(data.detail?.message || data.detail || 'Erreur lors de la suppression');
      }
      
      setOperationMessage({
        type: 'success',
        text: data.message || 'Chapitre supprimé avec succès'
      });
      
      setDeleteConfirmOpen(false);
      setChapterToDelete(null);
      fetchCurriculum();
      
    } catch (err) {
      setOperationMessage({
        type: 'error',
        text: err.message
      });
    } finally {
      setDeleting(false);
    }
  };
  
  // Gérer le changement de générateurs (multiselect simple)
  const handleGeneratorToggle = (generator) => {
    setFormData(prev => ({
      ...prev,
      exercise_types: prev.exercise_types.includes(generator)
        ? prev.exercise_types.filter(g => g !== generator)
        : [...prev.exercise_types, generator]
    }));
  };
  
  // Affichage loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Chargement du référentiel...</p>
        </div>
      </div>
    );
  }
  
  // Affichage erreur
  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
          <Button onClick={fetchCurriculum} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Réessayer
          </Button>
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
              <Link to="/" className="text-gray-500 hover:text-gray-700">
                <ChevronLeft className="h-5 w-5" />
              </Link>
              <div>
                <h1 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                  <LayoutGrid className="h-5 w-5 text-blue-600" />
                  Administration Curriculum 6e
                </h1>
                <p className="text-sm text-gray-500">
                  Référentiel pédagogique • V2 - Édition
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-blue-50 text-blue-700">
                {curriculum?.total_chapitres || 0} chapitres
              </Badge>
              <Button variant="outline" size="sm" onClick={fetchCurriculum}>
                <RefreshCw className="h-4 w-4 mr-1" />
                Actualiser
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
        {/* Message de succès/erreur */}
        {operationMessage && (
          <Alert 
            className={`mb-4 ${operationMessage.type === 'success' ? 'border-green-500 bg-green-50' : 'border-red-500 bg-red-50'}`}
          >
            {operationMessage.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription className={operationMessage.type === 'success' ? 'text-green-800' : 'text-red-800'}>
              {operationMessage.text}
            </AlertDescription>
          </Alert>
        )}
        
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Total chapitres
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {curriculum?.total_chapitres || 0}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Avec schémas
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {curriculum?.stats?.with_diagrams || 0}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                Domaines
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {Object.keys(curriculum?.stats?.by_domaine || {}).length}
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-500">
                En production
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-gray-900">
                {curriculum?.stats?.by_status?.prod || 0}
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* Filtres */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Rechercher par code ou libellé..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              
              <div className="w-full sm:w-64">
                <Select value={selectedDomaine} onValueChange={setSelectedDomaine}>
                  <SelectTrigger>
                    <Filter className="h-4 w-4 mr-2 text-gray-400" />
                    <SelectValue placeholder="Filtrer par domaine" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Tous les domaines</SelectItem>
                    {domaines.map(domaine => (
                      <SelectItem key={domaine} value={domaine}>
                        {domaine}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="mt-3 text-sm text-gray-500">
              {filteredChapitres.length} chapitre{filteredChapitres.length > 1 ? 's' : ''} affiché{filteredChapitres.length > 1 ? 's' : ''}
              {searchTerm || selectedDomaine !== 'all' ? ' (filtré)' : ''}
            </div>
          </CardContent>
        </Card>
        
        {/* Tableau des chapitres */}
        <Card>
          <CardHeader>
            <CardTitle>Référentiel des chapitres</CardTitle>
            <CardDescription>
              Liste complète des chapitres du programme officiel de 6e - Cliquez sur un chapitre pour le modifier
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-24">Code</TableHead>
                    <TableHead className="w-40">Domaine</TableHead>
                    <TableHead>Libellé</TableHead>
                    <TableHead className="w-48">Générateurs</TableHead>
                    <TableHead className="w-16 text-center">Schéma</TableHead>
                    <TableHead className="w-16 text-center">Statut</TableHead>
                    <TableHead className="w-24 text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredChapitres.map((chapitre) => (
                    <TableRow key={chapitre.code_officiel} className="hover:bg-gray-50">
                      <TableCell className="font-mono text-sm font-medium">
                        <div className="flex items-center gap-2">
                          {chapitre.code_officiel}
                          {isPilotChapter(chapitre.code_officiel) && (
                            <Badge className="bg-blue-100 text-blue-700 text-[10px] px-1.5 py-0">
                              Pilote
                            </Badge>
                          )}
                          {isEditableChapter(chapitre.code_officiel) && (
                            <Badge className="bg-green-100 text-green-700 text-[10px] px-1.5 py-0">
                              Éditable
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      
                      <TableCell>
                        <Badge 
                          variant="outline" 
                          className={`${getDomaineColor(chapitre.domaine)} text-xs`}
                        >
                          {chapitre.domaine}
                        </Badge>
                      </TableCell>
                      
                      <TableCell className="text-sm">
                        <div className="font-medium text-gray-900">
                          {chapitre.libelle}
                        </div>
                        {chapitre.chapitre_backend && (
                          <div className="text-xs text-gray-500 mt-0.5">
                            → {chapitre.chapitre_backend}
                          </div>
                        )}
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {chapitre.generateurs.slice(0, 2).map((gen) => (
                            <Badge 
                              key={gen} 
                              variant="secondary" 
                              className="text-xs font-mono"
                            >
                              {gen}
                            </Badge>
                          ))}
                          {chapitre.generateurs.length > 2 && (
                            <Badge variant="outline" className="text-xs">
                              +{chapitre.generateurs.length - 2}
                            </Badge>
                          )}
                        </div>
                      </TableCell>
                      
                      <TableCell className="text-center">
                        {chapitre.has_diagramme || chapitre.schema_requis ? (
                          <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                        ) : (
                          <span className="text-gray-300">—</span>
                        )}
                      </TableCell>
                      
                      <TableCell className="text-center">
                        <Badge className={`${getStatusColor(chapitre.statut)} text-xs`}>
                          {chapitre.statut}
                        </Badge>
                      </TableCell>
                      
                      <TableCell>
                        <div className="flex items-center justify-center gap-1">
                          {/* Bouton Exercices pour les chapitres éditables */}
                          {isEditableChapter(chapitre.code_officiel) && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => navigate(`/admin/curriculum/${chapitre.code_officiel}/exercises`)}
                              className="h-8 w-8 p-0"
                              title="📗 Gérer les exercices"
                            >
                              <BookOpen className="h-4 w-4 text-green-600" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenEdit(chapitre)}
                            className="h-8 w-8 p-0"
                            title="Modifier le chapitre"
                          >
                            <Pencil className="h-4 w-4 text-blue-600" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleOpenDelete(chapitre)}
                            className="h-8 w-8 p-0"
                            title="Supprimer le chapitre"
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
            
            {filteredChapitres.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <FileCode2 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>Aucun chapitre ne correspond à vos critères</p>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Footer info */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>
            Version 2.0 • Édition activée
          </p>
        </div>
      </main>
      
      {/* Modal d'édition/création */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {modalMode === 'create' ? 'Ajouter un chapitre' : 'Modifier le chapitre'}
            </DialogTitle>
            <DialogDescription>
              {modalMode === 'create' 
                ? 'Créez un nouveau chapitre dans le référentiel 6e'
                : `Modification de ${editingChapter?.code_officiel}`
              }
            </DialogDescription>
          </DialogHeader>
          
          <div className="grid gap-4 py-4">
            {/* Code officiel */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="code_officiel" className="text-right text-sm">
                Code officiel *
              </Label>
              <div className="col-span-3">
                <Input
                  id="code_officiel"
                  value={formData.code_officiel || ''}
                  onChange={(e) => setFormData(prev => ({ ...prev, code_officiel: e.target.value }))}
                  placeholder="6e_N01, 6e_GM07, 6e_TESTS_DYN..."
                  disabled={modalMode === 'edit'}
                  className={`${formErrors.code_officiel ? 'border-red-500' : ''} ${modalMode === 'edit' ? 'bg-gray-100 text-gray-600' : ''}`}
                />
                {modalMode === 'edit' && (
                  <p className="text-xs text-gray-500 mt-1">Le code officiel ne peut pas être modifié.</p>
                )}
                {formErrors.code_officiel && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.code_officiel}</p>
                )}}
              </div>
            </div>
            
            {/* Libellé */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="libelle" className="text-right text-sm">
                Libellé *
              </Label>
              <div className="col-span-3">
                <Input
                  id="libelle"
                  value={formData.libelle}
                  onChange={(e) => setFormData(prev => ({ ...prev, libelle: e.target.value }))}
                  placeholder="Lire et écrire les nombres entiers"
                  className={formErrors.libelle ? 'border-red-500' : ''}
                />
                {formErrors.libelle && (
                  <p className="text-xs text-red-500 mt-1">{formErrors.libelle}</p>
                )}
              </div>
            </div>
            
            {/* Domaine */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="domaine" className="text-right text-sm">
                Domaine
              </Label>
              <div className="col-span-3">
                <Select 
                  value={formData.domaine} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, domaine: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {availableOptions.domaines.map(domaine => (
                      <SelectItem key={domaine} value={domaine}>
                        {domaine}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {/* Chapitre backend */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="chapitre_backend" className="text-right text-sm">
                Chapitre backend
              </Label>
              <div className="col-span-3">
                <Input
                  id="chapitre_backend"
                  value={formData.chapitre_backend}
                  onChange={(e) => setFormData(prev => ({ ...prev, chapitre_backend: e.target.value }))}
                  placeholder="Nombres entiers et décimaux"
                />
              </div>
            </div>
            
            {/* Statut */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="statut" className="text-right text-sm">
                Statut
              </Label>
              <div className="col-span-3">
                <Select 
                  value={formData.statut} 
                  onValueChange={(value) => setFormData(prev => ({ ...prev, statut: value }))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="prod">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-green-500"></span>
                        Production
                      </span>
                    </SelectItem>
                    <SelectItem value="beta">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-yellow-500"></span>
                        Beta
                      </span>
                    </SelectItem>
                    <SelectItem value="hidden">
                      <span className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                        Hidden
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {/* Schéma requis */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="schema_requis" className="text-right text-sm">
                Schéma requis
              </Label>
              <div className="col-span-3 flex items-center gap-2">
                <Switch
                  id="schema_requis"
                  checked={formData.schema_requis}
                  onCheckedChange={(checked) => setFormData(prev => ({ ...prev, schema_requis: checked }))}
                />
                <span className="text-sm text-gray-500">
                  {formData.schema_requis ? 'Oui' : 'Non'}
                </span>
              </div>
            </div>
            
            {/* Difficulté */}
            <div className="grid grid-cols-4 items-center gap-4">
              <Label className="text-right text-sm">
                Difficulté
              </Label>
              <div className="col-span-3 flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <Label className="text-xs text-gray-500">Min</Label>
                  <Select 
                    value={formData.difficulte_min.toString()} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, difficulte_min: parseInt(value) }))}
                  >
                    <SelectTrigger className="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1</SelectItem>
                      <SelectItem value="2">2</SelectItem>
                      <SelectItem value="3">3</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="flex items-center gap-2">
                  <Label className="text-xs text-gray-500">Max</Label>
                  <Select 
                    value={formData.difficulte_max.toString()} 
                    onValueChange={(value) => setFormData(prev => ({ ...prev, difficulte_max: parseInt(value) }))}
                  >
                    <SelectTrigger className="w-20">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="1">1</SelectItem>
                      <SelectItem value="2">2</SelectItem>
                      <SelectItem value="3">3</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              {formErrors.difficulte && (
                <p className="col-span-4 text-xs text-red-500 text-right">{formErrors.difficulte}</p>
              )}
            </div>
            
            {/* Générateurs */}
            <div className="grid grid-cols-4 items-start gap-4">
              <Label className="text-right text-sm pt-2">
                Générateurs
              </Label>
              <div className="col-span-3">
                <div className="border rounded-md p-3 max-h-40 overflow-y-auto">
                  <div className="flex flex-wrap gap-2">
                    {availableOptions.generators.slice(0, 30).map(gen => (
                      <Badge
                        key={gen}
                        variant={formData.exercise_types.includes(gen) ? 'default' : 'outline'}
                        className={`cursor-pointer text-xs ${
                          formData.exercise_types.includes(gen) 
                            ? 'bg-blue-600 hover:bg-blue-700' 
                            : 'hover:bg-gray-100'
                        }`}
                        onClick={() => handleGeneratorToggle(gen)}
                      >
                        {gen}
                      </Badge>
                    ))}
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {formData.exercise_types.length} générateur(s) sélectionné(s)
                </p>
              </div>
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
      
      {/* Dialog de confirmation de suppression */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="text-red-600">Confirmer la suppression</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer le chapitre{' '}
              <strong>{chapterToDelete?.code_officiel}</strong> ?
              <br />
              <span className="text-red-500">Cette action est irréversible.</span>
            </DialogDescription>
          </DialogHeader>
          
          {chapterToDelete && (
            <div className="py-4">
              <div className="bg-gray-50 p-3 rounded-md">
                <p className="font-medium">{chapterToDelete.libelle}</p>
                <p className="text-sm text-gray-500">{chapterToDelete.domaine}</p>
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
    </div>
  );
};

export default Curriculum6eAdminPage;
