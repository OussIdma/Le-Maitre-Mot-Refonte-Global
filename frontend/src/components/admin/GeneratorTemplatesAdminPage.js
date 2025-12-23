import React, { useState, useEffect } from 'react';
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
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { 
  Search, 
  Filter, 
  RefreshCw, 
  Plus,
  Pencil,
  Trash2,
  Copy,
  Eye,
  FileCode2,
  AlertCircle,
  CheckCircle,
  Loader2
} from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import axios from 'axios';
import TemplateEditorModal from './TemplateEditorModal';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

/**
 * Page d'administration des templates éditables pour générateurs
 * 
 * Permet de:
 * - Lister tous les templates avec filtres
 * - Créer/Éditer/Dupliquer/Supprimer des templates
 * - Prévisualiser les templates avec validation
 */
const GeneratorTemplatesAdminPage = () => {
  const { toast } = useToast();

  // État principal
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filtres
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedGenerator, setSelectedGenerator] = useState('all');
  const [selectedVariant, setSelectedVariant] = useState('all');
  const [selectedGrade, setSelectedGrade] = useState('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');

  // Générateurs disponibles
  const [availableGenerators, setAvailableGenerators] = useState([]);

  // Modal éditeur
  const [isEditorOpen, setIsEditorOpen] = useState(false);
  const [editorMode, setEditorMode] = useState('create'); // 'create' | 'edit' | 'duplicate'
  const [editingTemplate, setEditingTemplate] = useState(null);

  // Modal suppression
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [templateToDelete, setTemplateToDelete] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false);

  // ============================================================================
  // CHARGEMENT INITIAL
  // ============================================================================

  useEffect(() => {
    loadTemplates();
    loadAvailableGenerators();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(`${BACKEND_URL}/api/v1/admin/generator-templates`);
      setTemplates(response.data || []);
    } catch (err) {
      console.error('Erreur chargement templates:', err);
      setError(err.response?.data?.detail?.message || err.message);
      toast({
        title: "Erreur de chargement",
        description: "Impossible de charger les templates",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableGenerators = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/v1/exercises/generators`);
      const generators = response.data || [];
      
      // Filtrer uniquement les générateurs dynamiques
      const dynamicGenerators = generators.filter(g => g.meta?.is_dynamic === true);
      setAvailableGenerators(dynamicGenerators);
    } catch (err) {
      console.error('Erreur chargement générateurs:', err);
    }
  };

  // ============================================================================
  // ACTIONS CRUD
  // ============================================================================

  const handleCreate = () => {
    setEditorMode('create');
    setEditingTemplate(null);
    setIsEditorOpen(true);
  };

  const handleEdit = (template) => {
    setEditorMode('edit');
    setEditingTemplate(template);
    setIsEditorOpen(true);
  };

  const handleDuplicate = (template) => {
    setEditorMode('duplicate');
    setEditingTemplate({
      ...template,
      id: null, // Pas d'ID pour duplication
      variant_id: template.variant_id + '_copy'
    });
    setIsEditorOpen(true);
  };

  const handleDeleteClick = (template) => {
    setTemplateToDelete(template);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!templateToDelete) return;

    try {
      setIsDeleting(true);
      
      await axios.delete(
        `${BACKEND_URL}/api/v1/admin/generator-templates/${templateToDelete.id}`
      );

      toast({
        title: "Template supprimé",
        description: `Le template pour ${templateToDelete.generator_key} a été supprimé.`,
      });

      // Recharger la liste
      await loadTemplates();
      setDeleteConfirmOpen(false);
      setTemplateToDelete(null);
    } catch (err) {
      console.error('Erreur suppression template:', err);
      toast({
        title: "Erreur de suppression",
        description: err.response?.data?.detail?.message || err.message,
        variant: "destructive"
      });
    } finally {
      setIsDeleting(false);
    }
  };

  const handleEditorSave = async () => {
    // Recharger la liste après sauvegarde
    await loadTemplates();
    setIsEditorOpen(false);
    setEditingTemplate(null);
  };

  // ============================================================================
  // FILTRAGE
  // ============================================================================

  const filteredTemplates = templates.filter(template => {
    // Recherche textuelle
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      if (
        !template.generator_key.toLowerCase().includes(search) &&
        !template.variant_id.toLowerCase().includes(search)
      ) {
        return false;
      }
    }

    // Filtre générateur
    if (selectedGenerator !== 'all' && template.generator_key !== selectedGenerator) {
      return false;
    }

    // Filtre variant
    if (selectedVariant !== 'all' && template.variant_id !== selectedVariant) {
      return false;
    }

    // Filtre grade
    if (selectedGrade !== 'all') {
      if (selectedGrade === 'none' && template.grade !== null) return false;
      if (selectedGrade !== 'none' && template.grade !== selectedGrade) return false;
    }

    // Filtre difficulty
    if (selectedDifficulty !== 'all') {
      if (selectedDifficulty === 'none' && template.difficulty !== null) return false;
      if (selectedDifficulty !== 'none' && template.difficulty !== selectedDifficulty) return false;
    }

    return true;
  });

  // Extraire les valeurs uniques pour les filtres
  const uniqueGenerators = [...new Set(templates.map(t => t.generator_key))];
  const uniqueVariants = [...new Set(templates.map(t => t.variant_id))];
  const uniqueGrades = [...new Set(templates.map(t => t.grade).filter(Boolean))];
  const uniqueDifficulties = [...new Set(templates.map(t => t.difficulty).filter(Boolean))];

  // ============================================================================
  // RENDU
  // ============================================================================

  return (
    <div className="container mx-auto py-8 px-4">
      {/* En-tête */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <FileCode2 className="h-6 w-6" />
                Templates Éditables
              </CardTitle>
              <CardDescription className="mt-2">
                Gérez les templates de rédaction (énoncés/solutions) pour les générateurs dynamiques
              </CardDescription>
            </div>
            <Button onClick={handleCreate} className="flex items-center gap-2">
              <Plus className="h-4 w-4" />
              Nouveau Template
            </Button>
          </div>
        </CardHeader>
      </Card>

      {/* Filtres */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="h-5 w-5" />
            Filtres
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {/* Recherche */}
            <div>
              <Label>Recherche</Label>
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Générateur, variant..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Générateur */}
            <div>
              <Label>Générateur</Label>
              <Select value={selectedGenerator} onValueChange={setSelectedGenerator}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  {uniqueGenerators.map(gen => (
                    <SelectItem key={gen} value={gen}>{gen}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Variant */}
            <div>
              <Label>Variant</Label>
              <Select value={selectedVariant} onValueChange={setSelectedVariant}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  {uniqueVariants.map(variant => (
                    <SelectItem key={variant} value={variant}>{variant}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Grade */}
            <div>
              <Label>Niveau</Label>
              <Select value={selectedGrade} onValueChange={setSelectedGrade}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tous</SelectItem>
                  <SelectItem value="none">Aucun (générique)</SelectItem>
                  {uniqueGrades.map(grade => (
                    <SelectItem key={grade} value={grade}>{grade}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Difficulté */}
            <div>
              <Label>Difficulté</Label>
              <Select value={selectedDifficulty} onValueChange={setSelectedDifficulty}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Toutes</SelectItem>
                  <SelectItem value="none">Aucune (générique)</SelectItem>
                  {uniqueDifficulties.map(diff => (
                    <SelectItem key={diff} value={diff}>{diff}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-muted-foreground">
              {filteredTemplates.length} template(s) trouvé(s) sur {templates.length}
            </div>
            <Button variant="outline" size="sm" onClick={loadTemplates} className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              Actualiser
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Liste des templates */}
      <Card>
        <CardContent className="pt-6">
          {loading && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {!loading && !error && filteredTemplates.length === 0 && (
            <div className="text-center py-12">
              <FileCode2 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">
                {templates.length === 0 
                  ? "Aucun template créé. Créez-en un pour commencer."
                  : "Aucun template ne correspond aux filtres."}
              </p>
            </div>
          )}

          {!loading && !error && filteredTemplates.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Générateur</TableHead>
                  <TableHead>Variant</TableHead>
                  <TableHead>Niveau</TableHead>
                  <TableHead>Difficulté</TableHead>
                  <TableHead>Variables HTML</TableHead>
                  <TableHead>Modifié</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredTemplates.map(template => (
                  <TableRow key={template.id}>
                    <TableCell className="font-medium">
                      {template.generator_key}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{template.variant_id}</Badge>
                    </TableCell>
                    <TableCell>
                      {template.grade ? (
                        <Badge>{template.grade}</Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">Tous</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {template.difficulty ? (
                        <Badge variant="secondary">{template.difficulty}</Badge>
                      ) : (
                        <span className="text-muted-foreground text-sm">Toutes</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {template.allowed_html_vars && template.allowed_html_vars.length > 0 ? (
                        <div className="flex gap-1 flex-wrap">
                          {template.allowed_html_vars.map(v => (
                            <Badge key={v} variant="outline" className="text-xs">
                              {v}
                            </Badge>
                          ))}
                        </div>
                      ) : (
                        <span className="text-muted-foreground text-sm">Aucune</span>
                      )}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {new Date(template.updated_at).toLocaleDateString('fr-FR', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric'
                      })}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleEdit(template)}
                          className="flex items-center gap-1"
                        >
                          <Pencil className="h-4 w-4" />
                          Éditer
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDuplicate(template)}
                          className="flex items-center gap-1"
                        >
                          <Copy className="h-4 w-4" />
                          Dupliquer
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDeleteClick(template)}
                          className="flex items-center gap-1 text-destructive hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                          Supprimer
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Modal Éditeur */}
      {isEditorOpen && (
        <TemplateEditorModal
          isOpen={isEditorOpen}
          onClose={() => {
            setIsEditorOpen(false);
            setEditingTemplate(null);
          }}
          mode={editorMode}
          template={editingTemplate}
          availableGenerators={availableGenerators}
          onSave={handleEditorSave}
        />
      )}

      {/* Modal Confirmation Suppression */}
      <Dialog open={deleteConfirmOpen} onOpenChange={setDeleteConfirmOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Confirmer la suppression</DialogTitle>
            <DialogDescription>
              Êtes-vous sûr de vouloir supprimer ce template ?
              <br />
              <strong>{templateToDelete?.generator_key}</strong> ({templateToDelete?.variant_id})
              <br />
              <br />
              Cette action est irréversible.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button
              variant="outline"
              onClick={() => setDeleteConfirmOpen(false)}
              disabled={isDeleting}
            >
              Annuler
            </Button>
            <Button
              variant="destructive"
              onClick={handleDeleteConfirm}
              disabled={isDeleting}
              className="flex items-center gap-2"
            >
              {isDeleting && <Loader2 className="h-4 w-4 animate-spin" />}
              Supprimer
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default GeneratorTemplatesAdminPage;

