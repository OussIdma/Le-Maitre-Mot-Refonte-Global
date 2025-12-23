import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Label } from '../ui/label';
import { Input } from '../ui/input';
import { Textarea } from '../ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue
} from '../ui/select';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import {
  Loader2,
  Save,
  Eye,
  AlertCircle,
  CheckCircle,
  Code2,
  X
} from 'lucide-react';
import { useToast } from '../../hooks/use-toast';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

/**
 * Modal d'édition/création de template avec prévisualisation
 */
const TemplateEditorModal = ({
  isOpen,
  onClose,
  mode, // 'create' | 'edit' | 'duplicate'
  template,
  availableGenerators,
  onSave
}) => {
  const { toast } = useToast();

  // État du formulaire
  const [formData, setFormData] = useState({
    generator_key: '',
    variant_id: 'default',
    grade: '',
    difficulty: '',
    enonce_template_html: '',
    solution_template_html: '',
    allowed_html_vars: []
  });

  // État de validation
  const [validationResult, setValidationResult] = useState(null);
  const [isValidating, setIsValidating] = useState(false);
  const [validationErrors, setValidationErrors] = useState([]);

  // État de sauvegarde
  const [isSaving, setIsSaving] = useState(false);

  // État de preview
  const [showPreview, setShowPreview] = useState(false);

  // Variable HTML à ajouter
  const [newHtmlVar, setNewHtmlVar] = useState('');

  // ============================================================================
  // INITIALISATION
  // ============================================================================

  useEffect(() => {
    if (template) {
      setFormData({
        generator_key: template.generator_key || '',
        variant_id: template.variant_id || 'default',
        grade: template.grade || '',
        difficulty: template.difficulty || '',
        enonce_template_html: template.enonce_template_html || '',
        solution_template_html: template.solution_template_html || '',
        allowed_html_vars: template.allowed_html_vars || []
      });
    } else {
      // Nouveau template : valeurs par défaut
      setFormData({
        generator_key: '',
        variant_id: 'default',
        grade: '',
        difficulty: '',
        enonce_template_html: '<p><strong>{{consigne}}</strong></p>\n<p>{{enonce}}</p>',
        solution_template_html: '<p>{{solution}}</p>',
        allowed_html_vars: []
      });
    }
  }, [template]);

  // ============================================================================
  // VALIDATION & PREVIEW
  // ============================================================================

  const handleValidate = async () => {
    if (!formData.generator_key) {
      toast({
        title: "Générateur requis",
        description: "Veuillez sélectionner un générateur avant de prévisualiser",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsValidating(true);
      setValidationErrors([]);
      setValidationResult(null);

      const response = await axios.post(
        `${BACKEND_URL}/api/v1/admin/generator-templates/validate`,
        {
          generator_key: formData.generator_key,
          variant_id: formData.variant_id || 'default',
          grade: formData.grade === 'null' || !formData.grade ? null : formData.grade,
          difficulty: formData.difficulty === 'null' || !formData.difficulty ? null : formData.difficulty,
          seed: 42, // Seed fixe pour reproductibilité
          enonce_template_html: formData.enonce_template_html,
          solution_template_html: formData.solution_template_html,
          allowed_html_vars: formData.allowed_html_vars
        }
      );

      setValidationResult(response.data);
      setShowPreview(true);

      toast({
        title: "Validation réussie",
        description: "Le template est valide et prêt à être sauvegardé",
      });
    } catch (err) {
      console.error('Erreur validation:', err);

      if (err.response?.status === 422) {
        const detail = err.response.data.detail;
        
        // Erreurs de validation structurées
        const errors = [];
        
        if (detail.missing_placeholders && detail.missing_placeholders.length > 0) {
          errors.push({
            type: 'ADMIN_TEMPLATE_MISMATCH',
            message: `Placeholders manquants: ${detail.missing_placeholders.join(', ')}`,
            placeholders: detail.missing_placeholders
          });
        }

        if (detail.html_security_errors && detail.html_security_errors.length > 0) {
          detail.html_security_errors.forEach(error => {
            errors.push({
              type: 'HTML_VAR_NOT_ALLOWED',
              message: error.message,
              placeholder: error.placeholder
            });
          });
        }

        setValidationErrors(errors);
        setShowPreview(false);

        toast({
          title: "Erreurs de validation",
          description: `${errors.length} erreur(s) détectée(s)`,
          variant: "destructive"
        });
      } else {
        toast({
          title: "Erreur de validation",
          description: err.response?.data?.detail?.message || err.message,
          variant: "destructive"
        });
      }
    } finally {
      setIsValidating(false);
    }
  };

  // ============================================================================
  // SAUVEGARDE
  // ============================================================================

  const handleSave = async () => {
    if (!formData.generator_key) {
      toast({
        title: "Générateur requis",
        description: "Veuillez sélectionner un générateur",
        variant: "destructive"
      });
      return;
    }

    if (!formData.enonce_template_html || !formData.solution_template_html) {
      toast({
        title: "Templates requis",
        description: "Les templates d'énoncé et de solution sont obligatoires",
        variant: "destructive"
      });
      return;
    }

    try {
      setIsSaving(true);

      const payload = {
        generator_key: formData.generator_key,
        variant_id: formData.variant_id || 'default',
        grade: formData.grade === 'null' || !formData.grade ? null : formData.grade,
        difficulty: formData.difficulty === 'null' || !formData.difficulty ? null : formData.difficulty,
        enonce_template_html: formData.enonce_template_html,
        solution_template_html: formData.solution_template_html,
        allowed_html_vars: formData.allowed_html_vars
      };

      if (mode === 'edit' && template?.id) {
        // Mode édition
        await axios.put(
          `${BACKEND_URL}/api/v1/admin/generator-templates/${template.id}`,
          payload
        );

        toast({
          title: "Template mis à jour",
          description: `Le template ${formData.generator_key} a été mis à jour`,
        });
      } else {
        // Mode création ou duplication
        await axios.post(
          `${BACKEND_URL}/api/v1/admin/generator-templates`,
          payload
        );

        toast({
          title: "Template créé",
          description: `Le template ${formData.generator_key} a été créé`,
        });
      }

      onSave();
    } catch (err) {
      console.error('Erreur sauvegarde:', err);
      toast({
        title: "Erreur de sauvegarde",
        description: err.response?.data?.detail?.message || err.message,
        variant: "destructive"
      });
    } finally {
      setIsSaving(false);
    }
  };

  // ============================================================================
  // GESTION VARIABLES HTML
  // ============================================================================

  const handleAddHtmlVar = () => {
    if (newHtmlVar && !formData.allowed_html_vars.includes(newHtmlVar)) {
      setFormData({
        ...formData,
        allowed_html_vars: [...formData.allowed_html_vars, newHtmlVar]
      });
      setNewHtmlVar('');
    }
  };

  const handleRemoveHtmlVar = (varName) => {
    setFormData({
      ...formData,
      allowed_html_vars: formData.allowed_html_vars.filter(v => v !== varName)
    });
  };

  // ============================================================================
  // RENDU
  // ============================================================================

  const getModalTitle = () => {
    if (mode === 'create') return 'Nouveau Template';
    if (mode === 'edit') return 'Éditer Template';
    if (mode === 'duplicate') return 'Dupliquer Template';
    return 'Template';
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-6xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Code2 className="h-5 w-5" />
            {getModalTitle()}
          </DialogTitle>
          <DialogDescription>
            {mode === 'create' && "Créez un nouveau template de rédaction pour un générateur"}
            {mode === 'edit' && "Modifiez le template existant"}
            {mode === 'duplicate' && "Créez une copie du template avec de nouveaux paramètres"}
          </DialogDescription>
        </DialogHeader>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Colonne gauche : Formulaire */}
          <div className="space-y-4">
            <h3 className="font-semibold">Configuration</h3>

            {/* Générateur */}
            <div>
              <Label>Générateur *</Label>
              <Select
                value={formData.generator_key}
                onValueChange={(value) => setFormData({ ...formData, generator_key: value })}
                disabled={mode === 'edit'}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Sélectionner un générateur" />
                </SelectTrigger>
                <SelectContent>
                  {availableGenerators.map(gen => (
                    <SelectItem key={gen.key} value={gen.key}>
                      {gen.meta?.label || gen.key}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {mode === 'edit' && (
                <p className="text-xs text-muted-foreground mt-1">
                  Le générateur ne peut pas être modifié
                </p>
              )}
            </div>

            {/* Variant */}
            <div>
              <Label>Variant</Label>
              <Select
                value={formData.variant_id}
                onValueChange={(value) => setFormData({ ...formData, variant_id: value })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="default">default</SelectItem>
                  <SelectItem value="A">A (Standard)</SelectItem>
                  <SelectItem value="B">B (Guidé)</SelectItem>
                  <SelectItem value="C">C (Diagnostic)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Grade */}
            <div>
              <Label>Niveau (optionnel)</Label>
              <Select
                value={formData.grade}
                onValueChange={(value) => setFormData({ ...formData, grade: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Tous les niveaux" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="null">Tous les niveaux</SelectItem>
                  <SelectItem value="6e">6e</SelectItem>
                  <SelectItem value="5e">5e</SelectItem>
                  <SelectItem value="4e">4e</SelectItem>
                  <SelectItem value="3e">3e</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Difficulté */}
            <div>
              <Label>Difficulté (optionnelle)</Label>
              <Select
                value={formData.difficulty}
                onValueChange={(value) => setFormData({ ...formData, difficulty: value })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Toutes difficultés" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="null">Toutes difficultés</SelectItem>
                  <SelectItem value="facile">Facile</SelectItem>
                  <SelectItem value="moyen">Moyen</SelectItem>
                  <SelectItem value="standard">Standard</SelectItem>
                  <SelectItem value="difficile">Difficile</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Variables HTML autorisées */}
            <div>
              <Label>Variables HTML autorisées (triple moustaches)</Label>
              <div className="flex gap-2 mt-1">
                <Input
                  placeholder="Ex: tableau_html"
                  value={newHtmlVar}
                  onChange={(e) => setNewHtmlVar(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      handleAddHtmlVar();
                    }
                  }}
                />
                <Button
                  type="button"
                  onClick={handleAddHtmlVar}
                  variant="outline"
                  size="sm"
                >
                  Ajouter
                </Button>
              </div>
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.allowed_html_vars.map(varName => (
                  <Badge key={varName} variant="secondary" className="flex items-center gap-1">
                    {varName}
                    <X
                      className="h-3 w-3 cursor-pointer hover:text-destructive"
                      onClick={() => handleRemoveHtmlVar(varName)}
                    />
                  </Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Variables autorisées en HTML brut ({"{{{var}}}"}). Ex: tableau_html
              </p>
            </div>

            {/* Templates */}
            <div>
              <Label>Template Énoncé *</Label>
              <Textarea
                value={formData.enonce_template_html}
                onChange={(e) => setFormData({ ...formData, enonce_template_html: e.target.value })}
                rows={8}
                className="font-mono text-sm"
                placeholder="<p><strong>{{consigne}}</strong></p>&#10;<p>{{enonce}}</p>"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Utilisez {"{{var}}"} pour texte échappé, {"{{{var}}}"} pour HTML brut
              </p>
            </div>

            <div>
              <Label>Template Solution *</Label>
              <Textarea
                value={formData.solution_template_html}
                onChange={(e) => setFormData({ ...formData, solution_template_html: e.target.value })}
                rows={8}
                className="font-mono text-sm"
                placeholder="<p>{{solution}}</p>&#10;<p><strong>{{reponse_finale}}</strong></p>"
              />
            </div>
          </div>

          {/* Colonne droite : Preview & Validation */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Prévisualisation</h3>
              <Button
                onClick={handleValidate}
                disabled={isValidating || !formData.generator_key}
                variant="outline"
                size="sm"
                className="flex items-center gap-2"
              >
                {isValidating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
                Prévisualiser
              </Button>
            </div>

            {/* Erreurs de validation */}
            {validationErrors.length > 0 && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <strong>Erreurs de validation:</strong>
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    {validationErrors.map((error, index) => (
                      <li key={index} className="text-sm">
                        {error.message}
                      </li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            {/* Résultat validation */}
            {validationResult && showPreview && (
              <>
                <Alert>
                  <CheckCircle className="h-4 w-4" />
                  <AlertDescription>
                    <strong>Template valide</strong>
                    <div className="mt-2 space-y-1 text-sm">
                      <div>
                        Placeholders utilisés: {validationResult.used_placeholders.length}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {validationResult.used_placeholders.map(p => (
                          <Badge key={p} variant="outline" className="text-xs">
                            {p}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </AlertDescription>
                </Alert>

                {/* Preview Énoncé */}
                <div>
                  <Label>Preview Énoncé</Label>
                  <div
                    className="border rounded-md p-4 bg-muted/50 mt-2 text-sm"
                    dangerouslySetInnerHTML={{
                      __html: validationResult.preview?.enonce_html || ''
                    }}
                  />
                </div>

                {/* Preview Solution */}
                <div>
                  <Label>Preview Solution</Label>
                  <div
                    className="border rounded-md p-4 bg-muted/50 mt-2 text-sm"
                    dangerouslySetInnerHTML={{
                      __html: validationResult.preview?.solution_html || ''
                    }}
                  />
                </div>
              </>
            )}

            {!showPreview && !isValidating && (
              <div className="text-center py-12 text-muted-foreground">
                <Eye className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Cliquez sur "Prévisualiser" pour valider le template</p>
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isSaving}>
            Annuler
          </Button>
          <Button
            onClick={handleSave}
            disabled={isSaving}
            className="flex items-center gap-2"
          >
            {isSaving && <Loader2 className="h-4 w-4 animate-spin" />}
            <Save className="h-4 w-4" />
            {mode === 'edit' ? 'Mettre à jour' : 'Créer'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default TemplateEditorModal;

