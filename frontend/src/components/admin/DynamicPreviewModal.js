/**
 * Modal de prévisualisation d'un exercice dynamique (P2)
 * 
 * Permet de:
 * - Générer un exemple avec seed aléatoire ou fixe
 * - Voir le rendu HTML final avec variables injectées
 * - Voir les SVG générés automatiquement
 * - Identifier les erreurs de variables
 */

import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Eye, 
  RefreshCw, 
  Loader2, 
  AlertCircle, 
  CheckCircle,
  Dice5,
  Code
} from 'lucide-react';
import { previewDynamicExercise } from '../../lib/adminApi';

const DynamicPreviewModal = ({ 
  open, 
  onOpenChange, 
  generatorKey,
  enonceTemplate,
  solutionTemplate,
  difficulty = 'moyen'
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [preview, setPreview] = useState(null);
  const [seed, setSeed] = useState('');
  const [showVariables, setShowVariables] = useState(false);
  
  const generatePreview = async (customSeed = null) => {
    setLoading(true);
    setError(null);
    
    const seedValue = customSeed !== null 
      ? customSeed 
      : (seed ? parseInt(seed) : Math.floor(Math.random() * 100000));
    
    const result = await previewDynamicExercise({
      generator_key: generatorKey,
      enonce_template_html: enonceTemplate,
      solution_template_html: solutionTemplate,
      difficulty: difficulty,
      seed: seedValue,
      svg_mode: 'AUTO'
    });
    
    if (result.success) {
      setPreview({ ...result.data, seed_used: seedValue });
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };
  
  const handleOpen = (isOpen) => {
    onOpenChange(isOpen);
    if (isOpen && !preview) {
      generatePreview();
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-[800px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-purple-600" />
            Prévisualisation dynamique
          </DialogTitle>
          <DialogDescription>
            Aperçu de l'exercice généré avec des valeurs aléatoires
          </DialogDescription>
        </DialogHeader>
        
        {/* Contrôles de génération */}
        <div className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2 flex-1">
            <Label className="text-sm whitespace-nowrap">Seed :</Label>
            <Input
              type="number"
              value={seed}
              onChange={(e) => setSeed(e.target.value)}
              placeholder="Aléatoire"
              className="w-28 h-8"
            />
          </div>
          
          <Button 
            onClick={() => generatePreview()} 
            disabled={loading}
            size="sm"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin mr-1" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-1" />
            )}
            Régénérer
          </Button>
          
          <Button 
            variant="outline"
            onClick={() => generatePreview(Math.floor(Math.random() * 100000))} 
            disabled={loading}
            size="sm"
          >
            <Dice5 className="h-4 w-4 mr-1" />
            Aléatoire
          </Button>
        </div>
        
        {/* Erreur */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {/* Preview */}
        {preview && (
          <div className="space-y-4">
            {/* Status et seed */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {preview.success ? (
                  <Badge className="bg-green-100 text-green-800">
                    <CheckCircle className="h-3 w-3 mr-1" />
                    Valide
                  </Badge>
                ) : (
                  <Badge className="bg-red-100 text-red-800">
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Erreurs détectées
                  </Badge>
                )}
                <span className="text-xs text-gray-500">
                  Seed: {preview.seed_used}
                </span>
              </div>
              
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowVariables(!showVariables)}
              >
                <Code className="h-4 w-4 mr-1" />
                {showVariables ? 'Masquer' : 'Voir'} variables
              </Button>
            </div>
            
            {/* Erreurs de variables */}
            {preview.errors?.length > 0 && (
              <Alert className="border-amber-300 bg-amber-50">
                <AlertCircle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-800">
                  <strong>Variables non reconnues :</strong>
                  <ul className="list-disc list-inside mt-1">
                    {preview.errors.map((err, i) => (
                      <li key={i} className="text-sm">{err}</li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}
            
            {/* Variables utilisées */}
            {showVariables && (
              <div className="bg-gray-100 p-3 rounded-lg text-xs font-mono overflow-x-auto">
                <div className="text-gray-500 mb-2">Variables générées :</div>
                <pre>{JSON.stringify(preview.variables_used, null, 2)}</pre>
              </div>
            )}
            
            {/* Énoncé */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                📝 Énoncé
              </h4>
              <div 
                className="bg-white border border-gray-200 p-4 rounded-md prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: preview.enonce_html }}
              />
              {preview.svg_enonce && (
                <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-200">
                  <div className="text-xs text-gray-500 mb-1">Figure énoncé :</div>
                  <div dangerouslySetInnerHTML={{ __html: preview.svg_enonce }} />
                </div>
              )}
            </div>
            
            {/* Solution */}
            <div>
              <h4 className="font-medium text-gray-900 mb-2 flex items-center gap-2">
                ✅ Solution
              </h4>
              <div 
                className="bg-green-50 border border-green-200 p-4 rounded-md prose prose-sm max-w-none"
                dangerouslySetInnerHTML={{ __html: preview.solution_html }}
              />
              {preview.svg_solution && (
                <div className="mt-2 p-2 bg-gray-50 rounded border border-gray-200">
                  <div className="text-xs text-gray-500 mb-1">Figure solution :</div>
                  <div dangerouslySetInnerHTML={{ __html: preview.svg_solution }} />
                </div>
              )}
            </div>
          </div>
        )}
        
        {/* Loading initial */}
        {loading && !preview && (
          <div className="py-12 flex flex-col items-center justify-center text-gray-500">
            <Loader2 className="h-8 w-8 animate-spin mb-3" />
            Génération de l'aperçu...
          </div>
        )}
        
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Fermer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default DynamicPreviewModal;
