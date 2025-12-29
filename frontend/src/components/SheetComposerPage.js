/**
 * SheetComposerPage - Composer une fiche d'exercices
 *
 * Workflow:
 * 1. Affiche les exercices sélectionnés depuis SelectionContext
 * 2. Permet de réordonner (up/down) et supprimer des exercices
 * 3. Paramètres: titre, layout, inclure correction
 * 4. Export PDF: nécessite une session (Free ou Pro)
 */

import React, { useState, useEffect, useCallback } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Switch } from "./ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { useToast } from "../hooks/use-toast";
import { useAuth } from "../hooks/useAuth";
import { useLogin } from "../contexts/LoginContext";
import { useSelection } from "../contexts/SelectionContext";
import {
  FileText,
  Download,
  Loader2,
  ChevronUp,
  ChevronDown,
  Trash2,
  AlertCircle,
  ShoppingCart,
  FileDown,
  ArrowLeft,
  LayoutGrid,
  CheckCircle
} from "lucide-react";
import MathRenderer from "./MathRenderer";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * MathHtmlRenderer - Composant pour rendre du HTML contenant du LaTeX
 */
const MathHtmlRenderer = ({ html, className = "" }) => {
  if (!html) return null;

  const renderMixedContent = (htmlContent) => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(htmlContent, 'text/html');

    const processNode = (node, index = 0) => {
      if (node.nodeType === Node.TEXT_NODE) {
        const text = node.textContent;
        if (text && text.trim()) {
          const hasLatex = /\\(?:frac|sqrt|times|div|pm|cdot|leq|geq|neq|approx|[a-zA-Z]+)\{/.test(text) ||
                          /\^{[^}]+}/.test(text) ||
                          /_\{[^}]+\}/.test(text);

          if (hasLatex) {
            return <MathRenderer key={`math-${index}`} content={text} className="inline" />;
          }
          return <span key={`text-${index}`}>{text}</span>;
        }
        return null;
      }

      if (node.nodeType === Node.ELEMENT_NODE) {
        const tagName = node.tagName.toLowerCase();

        const rawHtmlElements = ['svg', 'table', 'img', 'br', 'hr'];
        if (rawHtmlElements.includes(tagName)) {
          return (
            <span
              key={`html-${index}`}
              dangerouslySetInnerHTML={{ __html: node.outerHTML }}
            />
          );
        }

        const children = Array.from(node.childNodes).map((child, i) =>
          processNode(child, index * 100 + i)
        ).filter(Boolean);

        const props = { key: `elem-${index}` };
        if (node.className) props.className = node.className;
        if (node.id) props.id = node.id;

        const reactTagMap = {
          'div': 'div', 'p': 'p', 'span': 'span', 'strong': 'strong', 'b': 'b',
          'em': 'em', 'i': 'i', 'ol': 'ol', 'ul': 'ul', 'li': 'li',
          'h1': 'h1', 'h2': 'h2', 'h3': 'h3', 'h4': 'h4', 'h5': 'h5', 'h6': 'h6',
          'a': 'a', 'sup': 'sup', 'sub': 'sub'
        };

        const ReactTag = reactTagMap[tagName] || 'span';
        return React.createElement(ReactTag, props, children.length > 0 ? children : null);
      }

      return null;
    };

    const bodyChildren = Array.from(doc.body.childNodes).map((node, i) =>
      processNode(node, i)
    ).filter(Boolean);

    return bodyChildren;
  };

  return (
    <div className={`math-html-renderer ${className}`}>
      {renderMixedContent(html)}
    </div>
  );
};

const SheetComposerPage = () => {
  const { toast } = useToast();
  const navigate = useNavigate();
  const { sessionToken, isPro } = useAuth();
  const { openLogin } = useLogin();
  const { selectedExercises, removeExercise, clearSelection, reorderExercises, selectionCount } = useSelection();

  // Paramètres de la fiche
  const [sheetTitle, setSheetTitle] = useState("");
  const [layout, setLayout] = useState("standard");
  const [includeCorrection, setIncludeCorrection] = useState(true);

  // État de l'export
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState(null);

  // Déplacer un exercice vers le haut
  const moveUp = (index) => {
    if (index > 0) {
      reorderExercises(index, index - 1);
    }
  };

  // Déplacer un exercice vers le bas
  const moveDown = (index) => {
    if (index < selectedExercises.length - 1) {
      reorderExercises(index, index + 1);
    }
  };

  // Fonction d'export (peut être appelée directement ou après login)
  const doExport = useCallback(async (token) => {
    if (selectedExercises.length === 0) {
      toast({
        title: "Aucun exercice",
        description: "Ajoutez des exercices depuis le générateur",
        variant: "destructive"
      });
      return;
    }

    setIsExporting(true);
    setError(null);

    try {
      const exportData = {
        title: sheetTitle || "Fiche d'exercices",
        layout: layout,
        include_correction: includeCorrection,
        exercises: selectedExercises.map((ex, index) => ({
          order: index + 1,
          enonce_html: ex.enonce_html,
          solution_html: ex.solution_html,
          figure_svg_enonce: ex.figure_svg_enonce || ex.figure_svg,
          figure_svg_solution: ex.figure_svg_solution,
          metadata: ex.metadata
        }))
      };

      const response = await axios.post(
        `${BACKEND_URL}/api/v1/sheets/export-selection`,
        exportData,
        {
          headers: {
            'X-Session-Token': token,
            'Content-Type': 'application/json'
          },
          responseType: 'blob'
        }
      );

      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${sheetTitle || 'fiche'}_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      toast({
        title: "PDF exporté",
        description: "Votre fiche a été téléchargée",
        variant: "default"
      });

    } catch (err) {
      console.error("Erreur export PDF:", err);

      if (err.response?.status === 401) {
        toast({
          title: "Session expirée",
          description: "Veuillez vous reconnecter",
          variant: "destructive"
        });
        openLogin({
          returnTo: '/fiches/nouvelle',
          pendingAction: { type: 'export_pdf' },
          mode: 'login'
        });
      } else if (err.response?.status === 429) {
        toast({
          title: "Quota dépassé",
          description: "Vous avez atteint votre limite d'exports du jour. Passez en Pro pour des exports illimités.",
          variant: "destructive"
        });
      } else {
        setError("Erreur lors de l'export. Veuillez réessayer.");
        toast({
          title: "Erreur",
          description: "Impossible d'exporter la fiche",
          variant: "destructive"
        });
      }
    } finally {
      setIsExporting(false);
    }
  }, [selectedExercises, sheetTitle, layout, includeCorrection, toast, openLogin]);

  // Écouter l'événement de pending action après login
  useEffect(() => {
    const handlePendingAction = (event) => {
      const action = event.detail;
      if (action?.type === 'export_pdf') {
        // Récupérer le nouveau token depuis localStorage
        const newToken = localStorage.getItem('lemaitremot_session_token');
        if (newToken) {
          console.log('🔄 Relancement de l\'export PDF après login');
          setTimeout(() => doExport(newToken), 500); // Petit délai pour laisser l'état se stabiliser
        }
      }
    };

    window.addEventListener('lmm:execute-pending-action', handlePendingAction);
    return () => {
      window.removeEventListener('lmm:execute-pending-action', handlePendingAction);
    };
  }, [doExport]);

  // Export PDF - point d'entrée principal
  const handleExportPDF = async () => {
    // Vérifier qu'il y a des exercices
    if (selectedExercises.length === 0) {
      toast({
        title: "Aucun exercice",
        description: "Ajoutez des exercices depuis le générateur",
        variant: "destructive"
      });
      return;
    }

    // Vérifier la session
    if (!sessionToken) {
      toast({
        title: "Connexion requise",
        description: "Créez un compte gratuit pour exporter votre fiche en PDF",
        variant: "default"
      });
      // Ouvrir en mode register avec pendingAction
      openLogin({
        returnTo: '/fiches/nouvelle',
        pendingAction: { type: 'export_pdf' },
        mode: 'register'
      });
      return;
    }

    // Session présente, lancer l'export
    await doExport(sessionToken);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => navigate('/generer')}
            className="mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Retour au générateur
          </Button>

          <div className="flex items-center gap-3 mb-2">
            <ShoppingCart className="h-8 w-8 text-blue-600" />
            <h1 className="text-3xl font-bold text-gray-900">Composer ma fiche</h1>
          </div>
          <p className="text-gray-600">
            {selectionCount > 0
              ? `${selectionCount} exercice(s) dans votre sélection`
              : "Aucun exercice sélectionné"
            }
          </p>
        </div>

        {/* Message si sélection vide */}
        {selectedExercises.length === 0 ? (
          <Card>
            <CardContent className="py-12 text-center">
              <ShoppingCart className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h2 className="text-xl font-semibold text-gray-700 mb-2">
                Votre sélection est vide
              </h2>
              <p className="text-gray-500 mb-6">
                Ajoutez des exercices depuis le générateur pour créer votre fiche
              </p>
              <Button onClick={() => navigate('/generer')}>
                <FileText className="h-4 w-4 mr-2" />
                Aller au générateur
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Paramètres de la fiche */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LayoutGrid className="h-5 w-5" />
                  Paramètres de la fiche
                </CardTitle>
                <CardDescription>
                  Personnalisez votre fiche avant l'export
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Titre */}
                  <div className="md:col-span-2">
                    <Label htmlFor="sheet-title">Titre de la fiche</Label>
                    <Input
                      id="sheet-title"
                      value={sheetTitle}
                      onChange={(e) => setSheetTitle(e.target.value)}
                      placeholder="Ex: Exercices de géométrie - Chapitre 3"
                      className="mt-1"
                    />
                  </div>

                  {/* Layout */}
                  <div>
                    <Label htmlFor="layout">Mise en page</Label>
                    <Select value={layout} onValueChange={setLayout}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard</SelectItem>
                        <SelectItem value="eco">Économique</SelectItem>
                        <SelectItem value="large">Grand format</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* Options */}
                <div className="mt-4 flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Switch
                      id="include-correction"
                      checked={includeCorrection}
                      onCheckedChange={setIncludeCorrection}
                    />
                    <Label htmlFor="include-correction" className="cursor-pointer">
                      Inclure la correction
                    </Label>
                  </div>
                </div>

                {/* Boutons d'action */}
                <div className="mt-6 flex gap-3">
                  <Button
                    onClick={handleExportPDF}
                    disabled={isExporting || selectedExercises.length === 0}
                    className="flex-1"
                    size="lg"
                  >
                    {isExporting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Export en cours...
                      </>
                    ) : (
                      <>
                        <Download className="mr-2 h-4 w-4" />
                        Exporter en PDF
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    onClick={() => {
                      clearSelection();
                      toast({
                        title: "Sélection vidée",
                        description: "Tous les exercices ont été retirés",
                      });
                    }}
                  >
                    <Trash2 className="mr-2 h-4 w-4" />
                    Vider
                  </Button>
                </div>

                {/* Info authentification */}
                {!sessionToken && (
                  <Alert className="mt-4 border-blue-200 bg-blue-50">
                    <AlertCircle className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-800">
                      Connectez-vous pour exporter votre fiche en PDF.
                      <Button
                        variant="link"
                        className="text-blue-700 underline p-0 ml-1 h-auto"
                        onClick={() => openLogin('/fiches/nouvelle')}
                      >
                        Se connecter
                      </Button>
                    </AlertDescription>
                  </Alert>
                )}

                {/* Info quotas Free */}
                {sessionToken && !isPro && (
                  <Alert className="mt-4 border-amber-200 bg-amber-50">
                    <AlertCircle className="h-4 w-4 text-amber-600" />
                    <AlertDescription className="text-amber-800">
                      Compte gratuit : 10 exports PDF par jour.
                      <Button
                        variant="link"
                        className="text-amber-700 underline p-0 ml-1 h-auto"
                        onClick={() => navigate('/upgrade')}
                      >
                        Passer en Pro
                      </Button>
                    </AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>

            {/* Erreur */}
            {error && (
              <Alert variant="destructive" className="mb-6">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {/* Liste des exercices */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Exercices ({selectedExercises.length})
                </CardTitle>
                <CardDescription>
                  Réorganisez vos exercices par glisser-déposer ou avec les flèches
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {selectedExercises.map((exercise, index) => (
                    <div
                      key={exercise.uniqueId}
                      className="border rounded-lg p-4 bg-white hover:shadow-md transition-shadow"
                    >
                      {/* Header de l'exercice */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="px-3 py-1">
                            {index + 1}
                          </Badge>
                          {exercise.niveau && (
                            <Badge variant="outline">{exercise.niveau}</Badge>
                          )}
                          {exercise.chapitre && (
                            <Badge variant="outline">{exercise.chapitre}</Badge>
                          )}
                          {exercise.metadata?.is_premium && (
                            <Badge className="bg-purple-100 text-purple-800 border-purple-300">
                              PREMIUM
                            </Badge>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => moveUp(index)}
                            disabled={index === 0}
                          >
                            <ChevronUp className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => moveDown(index)}
                            disabled={index === selectedExercises.length - 1}
                          >
                            <ChevronDown className="h-4 w-4" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              removeExercise(exercise.uniqueId);
                              toast({
                                title: "Exercice retiré",
                                description: "L'exercice a été retiré de la sélection",
                              });
                            }}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>

                      {/* Apercu de l'énoncé */}
                      <div className="text-sm text-gray-700 line-clamp-3">
                        <MathHtmlRenderer html={exercise.enonce_html} />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
};

export default SheetComposerPage;
