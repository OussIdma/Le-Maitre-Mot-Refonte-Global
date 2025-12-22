/**
 * Panneau d'affichage des variables disponibles pour un générateur (P0.2)
 * 
 * Affiche:
 * - Liste des variables avec types et exemples
 * - Templates pré-remplis copiables
 * - Tips pédagogiques
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { Copy, Check, AlertCircle, Loader2, Info } from 'lucide-react';
import { fetchGeneratorSchema } from '../../lib/adminApi';

const GeneratorVariablesPanel = ({ generatorKey, onTemplatesLoaded }) => {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedVar, setCopiedVar] = useState(null);
  
  useEffect(() => {
    if (!generatorKey) return;
    
    const loadSchema = async () => {
      setLoading(true);
      setError(null);
      
      const result = await fetchGeneratorSchema(generatorKey);
      
      if (result.success) {
        setSchema(result.data);
        // Notifier le parent des templates exemples
        if (onTemplatesLoaded) {
          onTemplatesLoaded({
            enonce: result.data.template_example_enonce,
            solution: result.data.template_example_solution
          });
        }
      } else {
        setError(result.error);
      }
      
      setLoading(false);
    };
    
    loadSchema();
  }, [generatorKey, onTemplatesLoaded]);
  
  const copyToClipboard = (text, varName) => {
    navigator.clipboard.writeText(`{{${varName}}}`);
    setCopiedVar(varName);
    setTimeout(() => setCopiedVar(null), 2000);
  };
  
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-gray-500 py-4">
        <Loader2 className="h-4 w-4 animate-spin" />
        Chargement du schéma...
      </div>
    );
  }
  
  if (error) {
    return (
      <Alert variant="destructive" className="mt-2">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  
  if (!schema) return null;
  
  // Grouper les variables par catégorie
  const groupedVars = {
    'Base': schema.variables.filter(v => ['figure_type', 'figure_type_article', 'coefficient', 'coefficient_str', 'transformation', 'transformation_verbe', 'facteur'].includes(v.name)),
    'Dimensions': schema.variables.filter(v => v.name.includes('initial') || v.name.includes('final')),
    'Résultats': schema.variables.filter(v => v.name.includes('aire') || v.name.includes('perimetre') || v.name.includes('rapport'))
  };
  
  return (
    <div className="space-y-3 mt-3">
      {/* Info pédagogique */}
      {schema.pedagogical_tips && (
        <div className="flex items-start gap-2 text-sm bg-amber-50 border border-amber-200 p-3 rounded-lg">
          <Info className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <span className="text-amber-800">{schema.pedagogical_tips}</span>
        </div>
      )}
      
      {/* Variables disponibles */}
      <div className="bg-white border border-gray-200 rounded-lg p-3">
        <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
          📋 Variables disponibles
          <Badge variant="outline" className="text-xs">{schema.variables.length}</Badge>
        </h4>
        
        <div className="space-y-3">
          {Object.entries(groupedVars).map(([group, vars]) => (
            vars.length > 0 && (
              <div key={group}>
                <div className="text-xs font-medium text-gray-500 mb-1">{group}</div>
                <div className="flex flex-wrap gap-1">
                  {vars.map(v => (
                    <Button
                      key={v.name}
                      variant="outline"
                      size="sm"
                      className="h-7 text-xs font-mono hover:bg-purple-50 hover:border-purple-300"
                      onClick={() => copyToClipboard(v.name, v.name)}
                      title={`${v.description}\nType: ${v.type}\nEx: ${v.example}`}
                    >
                      {copiedVar === v.name ? (
                        <Check className="h-3 w-3 text-green-600 mr-1" />
                      ) : (
                        <Copy className="h-3 w-3 text-gray-400 mr-1" />
                      )}
                      {`{{${v.name}}}`}
                    </Button>
                  ))}
                </div>
              </div>
            )
          ))}
        </div>
        
        <div className="text-xs text-gray-500 mt-3 flex items-center gap-1">
          💡 Cliquez sur une variable pour la copier
        </div>
      </div>
      
      {/* SVG Mode info */}
      <div className="text-xs bg-blue-50 border border-blue-200 p-2 rounded flex items-center gap-2">
        <span>🖼️</span>
        <span className="text-blue-800">
          <strong>Mode SVG AUTO</strong> activé par défaut — les figures sont générées automatiquement depuis les variables.
        </span>
      </div>
    </div>
  );
};

export default GeneratorVariablesPanel;
