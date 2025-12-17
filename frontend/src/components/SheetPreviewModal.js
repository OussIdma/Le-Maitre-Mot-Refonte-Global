import React, { useState } from "react";
import { X } from "lucide-react";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { Separator } from "./ui/separator";

function SheetPreviewModal({ isOpen, onClose, previewData }) {
  const [activeTab, setActiveTab] = useState("sujet");

  if (!isOpen || !previewData) return null;

  const { titre, niveau, items } = previewData;
  
  // Calculate total questions
  const totalQuestions = items.reduce((sum, item) => {
    return sum + (item.generated?.questions?.length || 0);
  }, 0);

  const renderQuestionEnonce = (question, questionNumber, exerciseType) => {
    // Logging: Vérifier si un exercice de géométrie n'a pas de figure
    if (!question.figure_html && exerciseType?.domaine?.toLowerCase().includes('géométrie')) {
      console.warn(`⚠️ Question ${questionNumber} (${exerciseType.titre}) : figure_html manquante pour un exercice de géométrie`);
    }
    
    return (
      <div key={question.id} className="mb-4">
        <p className="font-medium text-gray-900 mb-2">
          <span className="font-bold">{questionNumber}.</span>{' '}
          <span dangerouslySetInnerHTML={{ __html: question.enonce_brut }} />
        </p>
        
        {/* Figure géométrique si présente */}
        {question.figure_html && (
          <div 
            className="exercise-figure" 
            dangerouslySetInnerHTML={{ __html: question.figure_html }}
          />
        )}
      </div>
    );
  };

  const renderQuestionWithAnswer = (question, questionNumber, exerciseType) => {
    // Logging: Vérifier si un exercice de géométrie n'a pas de figure
    if (!question.figure_html && exerciseType?.domaine?.toLowerCase().includes('géométrie')) {
      console.warn(`⚠️ Question ${questionNumber} (${exerciseType.titre}) : figure_html manquante pour un exercice de géométrie`);
    }
    
    return (
      <div key={question.id} className="mb-6">
        <p className="font-medium text-gray-900 mb-2">
          <span className="font-bold">{questionNumber}.</span>{' '}
          <span dangerouslySetInnerHTML={{ __html: question.enonce_brut }} />
        </p>
        
        {/* Figure géométrique si présente */}
        {question.figure_html && (
          <div 
            className="exercise-figure" 
            dangerouslySetInnerHTML={{ __html: question.figure_html }}
          />
        )}
        
        {/* Zone de réponse élève */}
        <div className="ml-6 mt-2 p-4 border-2 border-dashed border-gray-300 rounded bg-gray-50 min-h-[80px]">
          <p className="text-xs text-gray-400 italic">Zone de réponse</p>
        </div>
      </div>
    );
  };

  const renderQuestionWithSolution = (question, questionNumber, exerciseType) => {
    // Logging: Vérifier si un exercice de géométrie n'a pas de figure
    if (!question.figure_html && exerciseType?.domaine?.toLowerCase().includes('géométrie')) {
      console.warn(`⚠️ Question ${questionNumber} (${exerciseType.titre}) : figure_html manquante pour un exercice de géométrie`);
    }
    
    return (
      <div key={question.id} className="mb-6">
        <p className="font-medium text-gray-900 mb-2">
          <span className="font-bold">{questionNumber}.</span>{' '}
          <span dangerouslySetInnerHTML={{ __html: question.enonce_brut }} />
        </p>
        
        {/* Figure géométrique si présente */}
        {question.figure_html && (
          <div 
            className="exercise-figure" 
            dangerouslySetInnerHTML={{ __html: question.figure_html }}
          />
        )}
        
        {/* Solution */}
        <div className="ml-6 mt-3 p-4 bg-blue-50 border-l-4 border-blue-500 rounded">
          <p className="text-sm font-semibold text-blue-900 mb-1">📝 Correction :</p>
          {question.solution_brut ? (
            <p className="text-sm text-gray-800 whitespace-pre-wrap">{question.solution_brut}</p>
          ) : (
            <p className="text-sm text-gray-500 italic">(Correction non disponible)</p>
          )}
        </div>
      </div>
    );
  };

  const renderExerciseContent = (item, exerciseNumber, renderMode) => {
    const exerciseType = item.exercise_type_summary || {};
    const questions = item.generated?.questions || [];
    
    let questionCounter = 1;

    return (
      <Card key={item.item_id} className="mb-6">
        <CardHeader className="bg-gradient-to-r from-gray-50 to-gray-100">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg">
                Exercice {exerciseNumber} — {exerciseType.titre || "Sans titre"}
              </CardTitle>
              <div className="flex gap-2 mt-2">
                <Badge variant="outline" className="text-xs">
                  {exerciseType.niveau || "N/A"}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {exerciseType.domaine || "N/A"}
                </Badge>
                <Badge variant="secondary" className="text-xs">
                  {questions.length} question{questions.length > 1 ? "s" : ""}
                </Badge>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="pt-6">
          {questions.length === 0 ? (
            <p className="text-gray-500 italic">Aucune question disponible</p>
          ) : (
            <div className="space-y-2">
              {questions.map((question) => {
                const qNum = questionCounter++;
                
                if (renderMode === "sujet") {
                  return renderQuestionEnonce(question, qNum, exerciseType);
                } else if (renderMode === "eleve") {
                  return renderQuestionWithAnswer(question, qNum, exerciseType);
                } else if (renderMode === "corrige") {
                  return renderQuestionWithSolution(question, qNum, exerciseType);
                }
                
                return null;
              })}
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <>
      <style>{`
        .exercise-figure {
          margin: 12px 0;
          text-align: center;
          width: 100%;
        }
        .exercise-figure svg {
          max-width: 100%;
          height: auto;
        }
      `}</style>
      
      <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">
              Aperçu de la fiche
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {titre} • {niveau} • {items.length} exercice{items.length > 1 ? "s" : ""} • {totalQuestions} question{totalQuestions > 1 ? "s" : ""}
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Content with Tabs */}
        <div className="flex-1 overflow-y-auto p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-3 mb-6">
              <TabsTrigger value="sujet">📄 Sujet</TabsTrigger>
              <TabsTrigger value="eleve">✏️ Version élève</TabsTrigger>
              <TabsTrigger value="corrige">✅ Corrigé</TabsTrigger>
            </TabsList>

            <TabsContent value="sujet">
              <div className="space-y-4">
                <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded">
                  <p className="text-sm text-blue-900">
                    <strong>Mode Sujet :</strong> Les énoncés des exercices sont affichés, sans espaces de réponse ni corrections.
                  </p>
                </div>
                
                {items.map((item, index) => renderExerciseContent(item, index + 1, "sujet"))}
              </div>
            </TabsContent>

            <TabsContent value="eleve">
              <div className="space-y-4">
                <div className="bg-green-50 border-l-4 border-green-500 p-4 rounded">
                  <p className="text-sm text-green-900">
                    <strong>Version élève :</strong> Les énoncés sont affichés avec des espaces pour que l&apos;élève puisse répondre.
                  </p>
                </div>
                
                {items.map((item, index) => renderExerciseContent(item, index + 1, "eleve"))}
              </div>
            </TabsContent>

            <TabsContent value="corrige">
              <div className="space-y-4">
                <div className="bg-purple-50 border-l-4 border-purple-500 p-4 rounded">
                  <p className="text-sm text-purple-900">
                    <strong>Corrigé :</strong> Les énoncés sont affichés avec leurs corrections détaillées.
                  </p>
                </div>
                
                {items.map((item, index) => renderExerciseContent(item, index + 1, "corrige"))}
              </div>
            </TabsContent>
          </Tabs>
        </div>

        {/* Footer */}
        <div className="border-t p-4 flex justify-between items-center">
          <p className="text-xs text-gray-500">
            Le Maître Mot — Aperçu généré automatiquement
          </p>
          <Button onClick={onClose}>Fermer</Button>
        </div>
      </div>
    </div>
    </>
  );
}

export default SheetPreviewModal;
