import React from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { FileText, Loader2, Shuffle, Zap } from "lucide-react";
import MathRenderer from "../MathRenderer";

const Step3GenerationApercu = ({
  // Sélections actuelles
  selectedMatiere,
  selectedNiveau,
  selectedChapitre,
  typeDoc,
  difficulte,
  nbExercices,
  // État de génération
  isGenerating,
  currentDocument,
  onGenerate,
  onVaryExercise,
  isLoading = false
}) => {
  const canGenerate = selectedMatiere && selectedNiveau && selectedChapitre && typeDoc && difficulte && nbExercices;

  // 🔍 Debug logging for geographic documents
  React.useEffect(() => {
    if (currentDocument && currentDocument.exercises) {
      const exercisesWithDocuments = currentDocument.exercises.filter(ex => ex.document);
      if (exercisesWithDocuments.length > 0) {
        console.log('🗺️ [Step3] Geographic documents detected:', {
          totalExercises: currentDocument.exercises.length,
          exercisesWithDocuments: exercisesWithDocuments.length,
          matiere: selectedMatiere,
          documents: exercisesWithDocuments.map(ex => ({
            title: ex.document?.titre,
            type: ex.document?.type,
            hasImage: !!ex.document?.url_fichier_direct
          }))
        });
      } else {
        console.log('🗺️ [Step3] No geographic documents in current document', {
          matiere: selectedMatiere,
          totalExercises: currentDocument.exercises.length
        });
      }
    }
  }, [currentDocument, selectedMatiere]);

  return (
    <div className="space-y-6">
      {/* Section Génération */}
      <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
        <CardHeader className="bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-t-lg">
          <CardTitle className="flex items-center">
            <Zap className="mr-2 h-5 w-5" />
            Génération du document
          </CardTitle>
          <CardDescription className="text-green-50">
            Créez votre document personnalisé avec l'intelligence artificielle
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          {canGenerate ? (
            <div className="space-y-4">
              {/* Résumé de la configuration */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-medium text-gray-900 mb-2">Configuration sélectionnée :</h4>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-600">Matière :</span>
                    <span className="ml-2 font-medium">{selectedMatiere}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Niveau :</span>
                    <span className="ml-2 font-medium">{selectedNiveau}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Type :</span>
                    <span className="ml-2 font-medium">{typeDoc}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Difficulté :</span>
                    <span className="ml-2 font-medium">{difficulte}</span>
                  </div>
                  <div className="col-span-2">
                    <span className="text-gray-600">Chapitre :</span>
                    <span className="ml-2 font-medium">{selectedChapitre}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Exercices :</span>
                    <span className="ml-2 font-medium">{nbExercices}</span>
                  </div>
                </div>
              </div>

              {/* Bouton de génération */}
              <Button
                onClick={onGenerate}
                disabled={isGenerating || isLoading}
                className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white py-3 rounded-lg font-semibold transition-all duration-200"
                size="lg"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Génération en cours...
                  </>
                ) : (
                  <>
                    <FileText className="mr-2 h-5 w-5" />
                    Générer le document
                  </>
                )}
              </Button>

              {isGenerating && (
                <div className="text-center text-sm text-gray-600">
                  <p>🤖 Le maître mot prépare vos exercices personnalisés...</p>
                  <p className="text-xs text-gray-500 mt-1">Cela peut prendre quelques secondes</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Configuration incomplète</h3>
              <p className="text-gray-500 mb-4">
                Veuillez compléter les étapes précédentes pour générer votre document
              </p>
              <div className="text-left max-w-md mx-auto">
                <h4 className="font-medium text-gray-700 mb-2">Éléments manquants :</h4>
                <ul className="text-sm text-gray-600 space-y-1">
                  {!selectedMatiere && <li>• Matière</li>}
                  {!selectedNiveau && <li>• Niveau</li>}
                  {!selectedChapitre && <li>• Chapitre</li>}
                  {!typeDoc && <li>• Type de document</li>}
                  {!difficulte && <li>• Difficulté</li>}
                  {!nbExercices && <li>• Nombre d'exercices</li>}
                </ul>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Aperçu du document généré */}
      {currentDocument && (
        <Card className="shadow-lg border-0 bg-white/80 backdrop-blur-sm">
          <CardHeader className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-t-lg">
            <CardTitle className="flex items-center">
              <FileText className="mr-2 h-5 w-5" />
              Aperçu du document
            </CardTitle>
            <CardDescription className="text-indigo-50">
              Prévisualisez le contenu généré
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            {/* Document Info */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="flex justify-between items-start mb-3">
                <div>
                  <h3 className="font-bold text-lg text-gray-900">
                    {currentDocument.type_doc.charAt(0).toUpperCase() + currentDocument.type_doc.slice(1)}
                  </h3>
                  <p className="text-gray-600">{currentDocument.matiere} - {currentDocument.niveau}</p>
                  <p className="text-sm text-gray-500">{currentDocument.chapitre}</p>
                </div>
                <div className="text-right">
                  <Badge variant="outline" className="mb-1">{currentDocument.difficulte}</Badge>
                  <p className="text-sm text-gray-500">{currentDocument.nb_exercices} exercices</p>
                </div>
              </div>
            </div>

            {/* Exercises Preview */}
            <Tabs defaultValue="sujet" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="sujet">Sujet</TabsTrigger>
                <TabsTrigger value="corrige">Corrigé</TabsTrigger>
              </TabsList>
              
              <TabsContent value="sujet" className="space-y-4 mt-4">
                {currentDocument.exercises.map((exercise, index) => (
                  <Card key={exercise.id} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center">
                          <span className="font-bold text-blue-600 mr-2">Exercice {index + 1}</span>
                          <Badge variant="secondary" className="text-xs">{exercise.type}</Badge>
                          <Badge variant="outline" className="text-xs ml-2">{exercise.difficulte}</Badge>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => onVaryExercise(index)}
                          className="text-gray-500 hover:text-gray-700"
                          title="Varier cet exercice"
                        >
                          <Shuffle className="h-4 w-4" />
                        </Button>
                      </div>
                      <div className="text-gray-900 whitespace-pre-wrap">
                        {/* Vérification critique avant rendu */}
                        {!exercise.enonce && console.error("❌ Exercice sans énoncé détecté:", exercise)}
                        <MathRenderer content={exercise.enonce} />
                      </div>
                      
                      {/* Display geometric schema if present */}
                      {exercise.schema_img && (
                        <div className="mt-4 text-center">
                          <h6 className="text-sm font-medium text-gray-700 mb-2">📐 Schéma géométrique</h6>
                          <img 
                            src={exercise.schema_img} 
                            alt="Schéma géométrique" 
                            className="max-w-full h-auto mx-auto border border-gray-300 rounded-lg shadow-sm"
                            style={{ maxHeight: '400px' }}
                          />
                        </div>
                      )}
                      
                      {/* Display SVG geometric figure for QUESTION (without answer) */}
                      {exercise.figure_svg_question && (
                        <div className="mt-4 flex justify-center">
                          <div 
                            className="border border-gray-300 rounded-lg shadow-sm bg-white p-4"
                            dangerouslySetInnerHTML={{ __html: exercise.figure_svg_question }}
                          />
                        </div>
                      )}
                      {/* Fallback to figure_svg if figure_svg_question not available (backward compatibility) */}
                      {!exercise.figure_svg_question && exercise.figure_svg && (
                        <div className="mt-4 flex justify-center">
                          <div 
                            className="border border-gray-300 rounded-lg shadow-sm bg-white p-4"
                            dangerouslySetInnerHTML={{ __html: exercise.figure_svg }}
                          />
                        </div>
                      )}
                      
                      {/* NOUVEAU: Display geographic document if present */}
                      {exercise.document && (
                        <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <div className="flex items-center mb-3">
                            <span className="text-xl mr-2">🗺️</span>
                            <h6 className="text-sm font-medium text-blue-800">Document pédagogique</h6>
                          </div>
                          
                          {/* Document title and description */}
                          <div className="mb-3">
                            <p className="text-sm font-medium text-blue-900">{exercise.document.titre}</p>
                            {exercise.document.description && (
                              <p className="text-xs text-blue-600 mt-1">{exercise.document.description}</p>
                            )}
                          </div>
                          
                          {/* Document image */}
                          {exercise.document.url_fichier_direct && (
                            <div className="text-center mb-3">
                              <img 
                                src={exercise.document.url_fichier_direct} 
                                alt={exercise.document.titre || "Document pédagogique"}
                                className="max-w-full h-auto mx-auto border border-gray-300 rounded-lg shadow-sm"
                                style={{ maxHeight: '350px' }}
                                onLoad={() => console.log('🗺️ Geographic document loaded:', exercise.document.titre)}
                                onError={(e) => {
                                  console.error('❌ Failed to load geographic document:', exercise.document.titre);
                                  e.target.style.display = 'none';
                                }}
                              />
                            </div>
                          )}
                          
                          {/* Document metadata */}
                          <div className="grid grid-cols-2 gap-2 text-xs text-blue-700">
                            {exercise.document.largeur_px && (
                              <div>
                                <span className="font-medium">Dimensions :</span> 
                                {exercise.document.largeur_px} × {exercise.document.hauteur_px} px
                              </div>
                            )}
                            {exercise.document.langue_labels && (
                              <div>
                                <span className="font-medium">Langue :</span> {exercise.document.langue_labels}
                              </div>
                            )}
                          </div>
                          
                          {/* License and attribution */}
                          {exercise.document.licence && (
                            <div className="mt-3 pt-3 border-t border-blue-200">
                              <div className="flex items-center justify-between text-xs">
                                <div>
                                  <span className="font-medium text-blue-800">Licence :</span>
                                  <span className="ml-1 px-2 py-1 bg-blue-100 rounded text-blue-800">
                                    {exercise.document.licence.type}
                                  </span>
                                </div>
                                {exercise.document.url_page_commons && (
                                  <a 
                                    href={exercise.document.url_page_commons}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-blue-600 hover:text-blue-800 underline"
                                    onClick={() => console.log('🔗 Opening document source:', exercise.document.url_page_commons)}
                                  >
                                    Source
                                  </a>
                                )}
                              </div>
                              {exercise.document.licence.notice_attribution && (
                                <p className="text-xs text-blue-600 mt-1">
                                  {exercise.document.licence.notice_attribution}
                                </p>
                              )}
                            </div>
                          )}
                          
                          {/* Debug info in development */}
                          {process.env.NODE_ENV === 'development' && exercise.document && (
                            <details className="mt-2">
                              <summary className="text-xs text-gray-500 cursor-pointer">Debug Document Data</summary>
                              <pre className="text-xs text-gray-600 mt-1 bg-gray-100 p-2 rounded overflow-auto">
                                {JSON.stringify(exercise.document, null, 2)}
                              </pre>
                            </details>
                          )}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>
              
              <TabsContent value="corrige" className="space-y-4 mt-4">
                {currentDocument.exercises.map((exercise, index) => (
                  <Card key={exercise.id} className="border-l-4 border-l-green-500">
                    <CardContent className="p-4">
                      <div className="flex items-center mb-3">
                        <span className="font-bold text-green-600 mr-2">Exercice {index + 1} - Solution</span>
                      </div>
                      <div className="space-y-2">
                        {exercise.solution.etapes.map((etape, etapeIndex) => (
                          <div key={etapeIndex} className="text-sm">
                            <span className="font-medium text-gray-700">Étape {etapeIndex + 1}:</span>
                            <span className="ml-2 text-gray-900">
                              <MathRenderer content={etape} />
                            </span>
                          </div>
                        ))}
                        <div className="mt-3 p-2 bg-green-50 rounded">
                          <strong className="text-green-800">Résultat :</strong> 
                          <span className="ml-2 text-green-900">
                            <MathRenderer content={exercise.solution.resultat} />
                          </span>
                        </div>
                        {exercise.bareme.length > 0 && (
                          <div className="mt-3 p-2 bg-blue-50 rounded">
                            <strong className="text-blue-800">Barème :</strong>
                            <ul className="list-disc list-inside mt-1 text-sm">
                              {exercise.bareme.map((item, i) => (
                                <li key={i} className="text-blue-900">
                                  {item.etape}: {item.points} pts
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                      
                      {/* Display SVG geometric figure for CORRECTION (with answer) */}
                      {exercise.figure_svg_correction && (
                        <div className="mt-4 flex justify-center">
                          <h6 className="text-sm font-medium text-gray-700 mb-2 text-center">📐 Figure corrigée</h6>
                          <div 
                            className="border border-green-300 rounded-lg shadow-sm bg-white p-4"
                            dangerouslySetInnerHTML={{ __html: exercise.figure_svg_correction }}
                          />
                        </div>
                      )}
                      {/* Fallback to figure_svg if figure_svg_correction not available (backward compatibility) */}
                      {!exercise.figure_svg_correction && exercise.figure_svg && (
                        <div className="mt-4 flex justify-center">
                          <h6 className="text-sm font-medium text-gray-700 mb-2 text-center">📐 Figure</h6>
                          <div 
                            className="border border-gray-300 rounded-lg shadow-sm bg-white p-4"
                            dangerouslySetInnerHTML={{ __html: exercise.figure_svg }}
                          />
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Step3GenerationApercu;