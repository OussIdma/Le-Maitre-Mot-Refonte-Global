/**
 * AddGeneratorModal - Modal pour ajouter un générateur à un chapitre (P1.2)
 * 
 * Fonctionnalités:
 * - Liste les générateurs dynamiques compatibles avec le grade du chapitre
 * - Filtre automatiquement selon is_dynamic et supported_grades
 * - Section "Plus de choix" pour les incompatibles (grisés + tooltip)
 * - Appel API POST /api/v1/admin/curriculum/chapters/{code}/exercise-types
 */

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
import { Badge } from '../ui/badge';
import {  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '../ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Loader2, 
  Check, 
  AlertCircle, 
  ChevronDown,
  ChevronRight,
  Info,
  Sparkles
} from 'lucide-react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

const AddGeneratorModal = ({ open, onClose, chapterCode, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [allGenerators, setAllGenerators] = useState([]);
  const [currentGenerators, setCurrentGenerators] = useState([]);
  const [compatibleGenerators, setCompatibleGenerators] = useState([]);
  const [incompatibleGenerators, setIncompatibleGenerators] = useState([]);
  const [error, setError] = useState(null);
  const [adding, setAdding] = useState(false);
  const [showIncompatible, setShowIncompatible] = useState(false);
  
  // Extraire le grade depuis le code_officiel
  const chapterGrade = chapterCode ? chapterCode.split('_')[0] : '';
  
  useEffect(() => {
    if (open && chapterCode) {
      fetchGenerators();
    }
  }, [open, chapterCode]);
  
  const fetchGenerators = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 1. Récupérer tous les générateurs avec métadonnées
      const allResponse = await axios.get(`${BACKEND_URL}/api/v1/exercises/generators`);
      const allGens = allResponse.data.generators || [];
      setAllGenerators(allGens);
      
      // 2. Récupérer les générateurs actuels du chapitre
      const currentResponse = await axios.get(
        `${BACKEND_URL}/api/v1/admin/curriculum/chapters/${chapterCode}/exercise-types`
      );
      const currentKeys = currentResponse.data.exercise_types.map(g => g.key);
      setCurrentGenerators(currentKeys);
      
      // 3. Filtrer par compatibilité
      const compatible = allGens.filter(gen =>
        gen.is_dynamic && 
        gen.supported_grades.includes(chapterGrade) &&
        !currentKeys.includes(gen.key)
      );
      
      const incompatible = allGens.filter(gen =>
        gen.is_dynamic &&
        !gen.supported_grades.includes(chapterGrade) &&
        !currentKeys.includes(gen.key)
      );
      
      setCompatibleGenerators(compatible);
      setIncompatibleGenerators(incompatible);
      
    } catch (err) {
      console.error('Erreur chargement générateurs:', err);
      setError(err.response?.data?.detail?.message || "Erreur lors du chargement des générateurs");
    } finally {
      setLoading(false);
    }
  };
  
  const handleAddGenerator = async (generatorKey) => {
    setAdding(true);
    setError(null);
    
    try {
      await axios.post(
        `${BACKEND_URL}/api/v1/admin/curriculum/chapters/${chapterCode}/exercise-types`,
        { add: [generatorKey] }
      );
      
      // Succès - rafraîchir et fermer
      onSuccess && onSuccess(generatorKey);
      onClose();
      
    } catch (err) {
      console.error('Erreur ajout générateur:', err);
      setError(
        err.response?.data?.detail?.message || 
        `Impossible d'ajouter ${generatorKey}`
      );
    } finally {
      setAdding(false);
    }
  };
  
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-600" />
            Ajouter un générateur à {chapterCode}
          </DialogTitle>
          <DialogDescription>
            Sélectionnez un générateur dynamique compatible avec {chapterGrade}
          </DialogDescription>
        </DialogHeader>
        
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">Chargement des générateurs...</span>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : (
          <div className="space-y-6">
            {/* Générateurs compatibles */}
            {compatibleGenerators.length === 0 ? (
              <div className="text-center py-8 bg-gray-50 rounded-lg border-2 border-dashed">
                <Info className="h-12 w-12 mx-auto mb-3 text-gray-400" />
                <p className="text-gray-600 font-medium">Aucun générateur compatible disponible</p>
                <p className="text-sm text-gray-500 mt-1">
                  Tous les générateurs compatibles avec {chapterGrade} sont déjà associés
                </p>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-gray-900">
                    Générateurs compatibles ({compatibleGenerators.length})
                  </h3>
                  <Badge variant="outline" className="bg-green-50 text-green-700 border-green-300">
                    Compatible {chapterGrade}
                  </Badge>
                </div>
                
                <div className="space-y-3">
                  {compatibleGenerators.map((gen) => (
                    <div
                      key={gen.key}
                      className="flex items-start gap-4 p-4 border rounded-lg hover:bg-gray-50 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-gray-900">{gen.label}</span>
                          <Badge variant="outline" className="text-xs">{gen.version}</Badge>
                          {gen.label.toLowerCase().includes('premium') && (
                            <Badge className="bg-purple-100 text-purple-800 text-xs">PREMIUM</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600 mb-2">{gen.description}</p>
                        <div className="flex gap-3 text-xs text-gray-500">
                          <span>🎯 Niveaux: {gen.supported_grades.join(', ')}</span>
                          {gen.supported_chapters && gen.supported_chapters.length > 0 && (
                            <span>📚 {gen.supported_chapters.length} chapitres</span>
                          )}
                        </div>
                      </div>
                      
                      <Button
                        onClick={() => handleAddGenerator(gen.key)}
                        disabled={adding}
                        size="sm"
                        className="shrink-0"
                      >
                        {adding ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <>
                            <Check className="h-4 w-4 mr-1" />
                            Ajouter
                          </>
                        )}
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Section "Plus de choix" (incompatibles) */}
            {incompatibleGenerators.length > 0 && (
              <Collapsible open={showIncompatible} onOpenChange={setShowIncompatible}>
                <CollapsibleTrigger className="w-full">
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border hover:bg-gray-100 transition-colors">
                    <div className="flex items-center gap-2">
                      {showIncompatible ? (
                        <ChevronDown className="h-4 w-4 text-gray-500" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-gray-500" />
                      )}
                      <span className="text-sm font-medium text-gray-700">
                        Plus de choix ({incompatibleGenerators.length})
                      </span>
                    </div>
                    <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-300 text-xs">
                      Incompatibles avec {chapterGrade}
                    </Badge>
                  </div>
                </CollapsibleTrigger>
                
                <CollapsibleContent>
                  <div className="mt-3 space-y-3">
                    {incompatibleGenerators.map((gen) => (
                      <TooltipProvider key={gen.key}>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <div className="flex items-start gap-4 p-4 border rounded-lg bg-gray-50 opacity-60 cursor-not-allowed">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-gray-600">{gen.label}</span>
                                  <Badge variant="outline" className="text-xs">{gen.version}</Badge>
                                </div>
                                <p className="text-sm text-gray-500 mb-2">{gen.description}</p>
                                <div className="flex gap-3 text-xs text-gray-400">
                                  <span>🎯 Niveaux: {gen.supported_grades.join(', ')}</span>
                                </div>
                              </div>
                              
                              <Button
                                disabled
                                size="sm"
                                variant="outline"
                                className="shrink-0"
                              >
                                Incompatible
                              </Button>
                            </div>
                          </TooltipTrigger>
                          <TooltipContent>
                            <p className="font-medium mb-1">Incompatible avec {chapterGrade}</p>
                            <p className="text-xs">Compatible avec : {gen.supported_grades.join(', ')}</p>
                          </TooltipContent>
                        </Tooltip>
                      </TooltipProvider>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            )}
            
            {/* Message info */}
            <Alert className="bg-blue-50 border-blue-200">
              <Info className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-900 text-sm">
                <strong>Filtrage automatique :</strong> Seuls les générateurs dynamiques compatibles avec {chapterGrade} sont proposés.
                Les générateurs déjà associés au chapitre ne sont pas affichés.
              </AlertDescription>
            </Alert>
          </div>
        )}
        
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Fermer
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default AddGeneratorModal;




