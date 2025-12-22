import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../ui/select";
import { Label } from "../ui/label";
import { BookOpen } from "lucide-react";

const Step1ProgrammeScolaire = ({
  matieres,
  niveaux,
  chapitres,
  selectedMatiere,
  selectedNiveau,
  selectedChapitre,
  onMatiereChange,
  onNiveauChange,
  onChapitreChange,
  isLoading = false,
  catalogStats = null  // Add catalog stats prop
}) => {

  // Helper function to get status emoji and styling
  const getStatusDisplay = (matiere) => {
    if (!matiere.status_info) return { emoji: "", className: "", tooltip: "" };
    
    const statusConfig = {
      active: { className: "text-green-600", tooltip: "Disponible maintenant" },
      coming_soon: { className: "text-orange-500", tooltip: `Disponible ${matiere.expected || 'bientôt'}` },
      planned: { className: "text-blue-500", tooltip: `En développement - ${matiere.expected || 'TBD'}` },
      beta: { className: "text-purple-500", tooltip: `Version test - ${matiere.expected || 'TBD'}` },
      future: { className: "text-gray-400", tooltip: `Prochainement - ${matiere.expected || 'TBD'}` }
    };
    
    const config = statusConfig[matiere.status] || statusConfig.future;
    
    return {
      emoji: matiere.status_info.emoji,
      className: config.className,
      tooltip: `${config.tooltip} - ${matiere.description}${matiere.note ? ' (' + matiere.note + ')' : ''}`
    };
  };
  return (
    <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
      <CardHeader className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-t-lg">
        <CardTitle className="flex items-center">
          <BookOpen className="mr-2 h-5 w-5" />
          Programme scolaire
        </CardTitle>
        <CardDescription className="text-blue-50">
          Sélectionnez la matière, le niveau et le chapitre souhaités
        </CardDescription>
      </CardHeader>
      <CardContent className="p-6 space-y-6">
        {/* Matière Selection */}
        <div className="space-y-2">
          <Label htmlFor="matiere-select" className="text-sm font-medium text-gray-700 flex items-center justify-between">
            📚 Matière
            {catalogStats && (
              <span className="text-xs text-gray-500">
                {catalogStats.total_subjects} matières • {catalogStats.total_chapters} chapitres
              </span>
            )}
          </Label>
          <Select 
            value={selectedMatiere} 
            onValueChange={onMatiereChange}
            disabled={isLoading}
          >
            <SelectTrigger id="matiere-select" className="w-full">
              <SelectValue placeholder="Choisir une matière" />
            </SelectTrigger>
            <SelectContent>
              {matieres.map((matiere) => {
                const statusDisplay = getStatusDisplay(matiere);
                const isActive = matiere.status === 'active';
                
                return (
                  <SelectItem 
                    key={matiere.name} 
                    value={matiere.name}
                    disabled={!isActive}
                    title={statusDisplay.tooltip}
                    className={`${isActive ? '' : 'opacity-60'}`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span>
                        {statusDisplay.emoji} {matiere.name}
                      </span>
                      {!isActive && (
                        <span className={`text-xs ${statusDisplay.className} ml-2`}>
                          {matiere.expected || 'Bientôt'}
                        </span>
                      )}
                      {isActive && matiere.chapter_count > 0 && (
                        <span className="text-xs text-gray-400 ml-2">
                          {matiere.chapter_count} ch.
                        </span>
                      )}
                    </div>
                  </SelectItem>
                );
              })}
            </SelectContent>
          </Select>
          
          {/* Status legend */}
          <div className="text-xs text-gray-500 mt-2 flex flex-wrap gap-3">
            <span>✅ Disponible</span>
            <span>🔄 Bientôt</span>
            <span>📋 En cours</span>
            <span>🧪 Test</span>
          </div>
        </div>

        {/* Niveau Selection */}
        <div className="space-y-2">
          <Label htmlFor="niveau-select" className="text-sm font-medium text-gray-700">
            🎓 Niveau
          </Label>
          <Select 
            value={selectedNiveau} 
            onValueChange={onNiveauChange}
            disabled={!selectedMatiere || isLoading}
          >
            <SelectTrigger id="niveau-select" className="w-full">
              <SelectValue placeholder="Choisir un niveau" />
            </SelectTrigger>
            <SelectContent>
              {niveaux.map((niveau) => (
                <SelectItem key={niveau} value={niveau}>
                  {niveau}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!selectedMatiere && (
            <p className="text-xs text-gray-500">
              Sélectionnez d'abord une matière
            </p>
          )}
        </div>

        {/* Chapitre Selection */}
        <div className="space-y-2">
          <Label htmlFor="chapitre-select" className="text-sm font-medium text-gray-700">
            📖 Chapitre/Compétence
          </Label>
          <Select 
            value={selectedChapitre} 
            onValueChange={onChapitreChange}
            disabled={!selectedNiveau || isLoading}
          >
            <SelectTrigger id="chapitre-select" className="w-full">
              <SelectValue placeholder="Choisir un chapitre" />
            </SelectTrigger>
            <SelectContent>
              {chapitres.map((chapitre) => (
                <SelectItem key={chapitre} value={chapitre}>
                  {chapitre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {!selectedNiveau && (
            <p className="text-xs text-gray-500">
              Sélectionnez d'abord un niveau
            </p>
          )}
        </div>

        {/* Progress Indicator */}
        {selectedMatiere && selectedNiveau && selectedChapitre && (
          <div className="mt-4 p-3 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center text-green-800">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-2">
                <p className="text-sm font-medium">
                  Programme sélectionné : {selectedMatiere} - {selectedNiveau}
                </p>
                <p className="text-xs text-green-600">
                  Chapitre : {selectedChapitre}
                </p>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default Step1ProgrammeScolaire;