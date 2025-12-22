/**
 * Formulaire auto-généré pour les paramètres d'un générateur (P4)
 * 
 * Génère automatiquement les champs de formulaire depuis le schema.
 * Affiche les presets comme boutons de configuration rapide.
 */

import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';
import { Switch } from '../ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { Alert, AlertDescription } from '../ui/alert';
import { Loader2, Wand2, Settings2, Sparkles, AlertCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Composant de champ auto-généré selon le type du paramètre
 */
const ParamField = ({ param, value, onChange, error }) => {
  const { name, type, description, options, min, max } = param;
  
  switch (type) {
    case 'enum':
      return (
        <div className="space-y-1">
          <Label className="text-sm font-medium">{name}</Label>
          <Select value={value || ''} onValueChange={onChange}>
            <SelectTrigger className={error ? 'border-red-500' : ''}>
              <SelectValue placeholder={`Choisir ${name}...`} />
            </SelectTrigger>
            <SelectContent>
              {options?.map(opt => (
                <SelectItem key={opt} value={opt}>{opt}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-500">{description}</p>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
      );
    
    case 'bool':
      return (
        <div className="flex items-center justify-between py-2">
          <div>
            <Label className="text-sm font-medium">{name}</Label>
            <p className="text-xs text-gray-500">{description}</p>
          </div>
          <Switch checked={value || false} onCheckedChange={onChange} />
        </div>
      );
    
    case 'int':
    case 'float':
      return (
        <div className="space-y-1">
          <Label className="text-sm font-medium">{name}</Label>
          <Input
            type="number"
            value={value ?? ''}
            onChange={(e) => onChange(e.target.value === '' ? null : Number(e.target.value))}
            min={min}
            max={max}
            step={type === 'float' ? 0.1 : 1}
            className={error ? 'border-red-500' : ''}
            placeholder={`${min || ''} - ${max || ''}`}
          />
          <p className="text-xs text-gray-500">{description}</p>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
      );
    
    default: // string
      return (
        <div className="space-y-1">
          <Label className="text-sm font-medium">{name}</Label>
          <Input
            type="text"
            value={value || ''}
            onChange={(e) => onChange(e.target.value)}
            className={error ? 'border-red-500' : ''}
          />
          <p className="text-xs text-gray-500">{description}</p>
          {error && <p className="text-xs text-red-500">{error}</p>}
        </div>
      );
  }
};

/**
 * Composant principal: formulaire de paramètres avec presets
 */
const GeneratorParamsForm = ({ 
  generatorKey, 
  initialParams = {}, 
  onChange,
  showPresets = true,
  compact = false 
}) => {
  const [schema, setSchema] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [params, setParams] = useState(initialParams);
  const [validationErrors, setValidationErrors] = useState({});
  
  // Charger le schéma Factory
  useEffect(() => {
    if (!generatorKey) return;
    
    const loadSchema = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`${BACKEND_URL}/api/v1/exercises/generators/${generatorKey}/full-schema`);
        
        if (!response.ok) {
          throw new Error(`Générateur non trouvé: ${generatorKey}`);
        }
        
        const data = await response.json();
        setSchema(data);
        
        // Initialiser avec les defaults si params vides
        if (Object.keys(params).length === 0) {
          setParams(data.defaults || {});
          if (onChange) onChange(data.defaults || {});
        }
        
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    loadSchema();
  }, [generatorKey]);
  
  // Callback stable pour changement de paramètre
  const handleParamChange = useCallback((paramName, value) => {
    setParams(prev => {
      const newParams = { ...prev, [paramName]: value };
      if (onChange) onChange(newParams);
      return newParams;
    });
    // Clear validation error for this field
    setValidationErrors(prev => {
      const { [paramName]: _, ...rest } = prev;
      return rest;
    });
  }, [onChange]);
  
  // Appliquer un preset
  const applyPreset = useCallback((preset) => {
    const newParams = { ...params, ...preset.params };
    setParams(newParams);
    if (onChange) onChange(newParams);
    setValidationErrors({});
  }, [params, onChange]);
  
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
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  
  if (!schema) return null;
  
  return (
    <div className={`space-y-4 ${compact ? 'text-sm' : ''}`}>
      {/* Presets */}
      {showPresets && schema.presets?.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
            <Sparkles className="h-4 w-4 text-purple-500" />
            Presets pédagogiques
          </div>
          <div className="flex flex-wrap gap-2">
            {schema.presets.map(preset => (
              <Button
                key={preset.key}
                type="button"
                variant="outline"
                size="sm"
                className="h-8 text-xs hover:bg-purple-50 hover:border-purple-300"
                onClick={() => applyPreset(preset)}
                title={preset.description}
              >
                <Wand2 className="h-3 w-3 mr-1" />
                {preset.label}
              </Button>
            ))}
          </div>
        </div>
      )}
      
      {/* Paramètres */}
      <div className="space-y-3">
        <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
          <Settings2 className="h-4 w-4" />
          Paramètres
          <Badge variant="outline" className="text-xs">{schema.schema?.length || 0}</Badge>
        </div>
        
        <div className={`grid gap-4 ${compact ? 'grid-cols-2' : 'grid-cols-1'}`}>
          {schema.schema?.map(param => (
            <ParamField
              key={param.name}
              param={param}
              value={params[param.name]}
              onChange={(v) => handleParamChange(param.name, v)}
              error={validationErrors[param.name]}
            />
          ))}
        </div>
      </div>
      
      {/* Tips pédagogiques */}
      {schema.meta?.pedagogical_tips && (
        <div className="flex items-start gap-2 text-xs bg-amber-50 border border-amber-200 p-2 rounded">
          <span className="text-amber-600">💡</span>
          <span className="text-amber-800">{schema.meta.pedagogical_tips}</span>
        </div>
      )}
    </div>
  );
};

export default GeneratorParamsForm;
