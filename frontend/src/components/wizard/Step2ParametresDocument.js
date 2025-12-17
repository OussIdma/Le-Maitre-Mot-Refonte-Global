import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Label } from "../ui/label";
import { Badge } from "../ui/badge";
import { Settings } from "lucide-react";

const Step2ParametresDocument = ({
  typeDoc,
  difficulte,
  nbExercices,
  onTypeDocChange,
  onDifficulteChange,
  onNbExercicesChange,
  isLoading = false
}) => {
  const typesDoc = [
    { value: "exercices", label: "Exercices", description: "Série d'exercices thématiques" },
    { value: "controle", label: "Contrôle", description: "Évaluation avec barème" },
    { value: "evaluation", label: "Évaluation", description: "Test de compétences" }
  ];

  const difficultes = [
    { value: "facile", label: "Facile", description: "Niveau débutant" },
    { value: "moyen", label: "Moyen", description: "Niveau intermédiaire" },
    { value: "difficile", label: "Difficile", description: "Niveau avancé" }
  ];

  const nombreExercices = [
    { value: 2, label: "2 exercices", description: "Document court" },
    { value: 4, label: "4 exercices", description: "Document standard" },
    { value: 6, label: "6 exercices", description: "Document complet" },
    { value: 8, label: "8 exercices", description: "Document approfondi" }
  ];

  return (
    <div className="space-y-6">
      <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-t-lg">
          <CardTitle className="flex items-center">
            <Settings className="mr-2 h-5 w-5" />
            Paramètres du document
          </CardTitle>
          <CardDescription className="text-purple-50">
            Configurez le type, la difficulté et le nombre d'exercices
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-6">
          {/* Type de Document */}
          <div className="space-y-2">
            <Label htmlFor="type-doc-select" className="text-sm font-medium text-gray-700">
              📋 Type de document
            </Label>
            <Select 
              value={typeDoc} 
              onValueChange={onTypeDocChange}
              disabled={isLoading}
            >
              <SelectTrigger id="type-doc-select" className="w-full">
                <SelectValue placeholder="Choisir un type" />
              </SelectTrigger>
              <SelectContent>
                {typesDoc.map((type) => (
                  <SelectItem key={type.value} value={type.value}>
                    <div className="flex flex-col">
                      <span className="font-medium">{type.label}</span>
                      <span className="text-xs text-gray-500">{type.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Difficulté */}
          <div className="space-y-2">
            <Label htmlFor="difficulte-select" className="text-sm font-medium text-gray-700">
              ⚡ Difficulté
            </Label>
            <Select 
              value={difficulte} 
              onValueChange={onDifficulteChange}
              disabled={isLoading}
            >
              <SelectTrigger id="difficulte-select" className="w-full">
                <SelectValue placeholder="Choisir une difficulté" />
              </SelectTrigger>
              <SelectContent>
                {difficultes.map((diff) => (
                  <SelectItem key={diff.value} value={diff.value}>
                    <div className="flex items-center justify-between w-full">
                      <div className="flex flex-col">
                        <span className="font-medium">{diff.label}</span>
                        <span className="text-xs text-gray-500">{diff.description}</span>
                      </div>
                      <Badge 
                        variant={diff.value === "facile" ? "default" : diff.value === "moyen" ? "secondary" : "destructive"}
                        className="ml-2"
                      >
                        {diff.value}
                      </Badge>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Nombre d'exercices */}
          <div className="space-y-2">
            <Label htmlFor="nb-exercices-select" className="text-sm font-medium text-gray-700">
              📊 Nombre d'exercices
            </Label>
            <Select 
              value={nbExercices.toString()} 
              onValueChange={(value) => onNbExercicesChange(parseInt(value))}
              disabled={isLoading}
            >
              <SelectTrigger id="nb-exercices-select" className="w-full">
                <SelectValue placeholder="Choisir le nombre" />
              </SelectTrigger>
              <SelectContent>
                {nombreExercices.map((nb) => (
                  <SelectItem key={nb.value} value={nb.value.toString()}>
                    <div className="flex flex-col">
                      <span className="font-medium">{nb.label}</span>
                      <span className="text-xs text-gray-500">{nb.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Progress Indicator */}
          {typeDoc && difficulte && nbExercices && (
            <div className="mt-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
              <div className="flex items-center text-purple-800">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-2">
                  <p className="text-sm font-medium">
                    Configuration : {typeDoc} • {difficulte} • {nbExercices} exercices
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Step2ParametresDocument;