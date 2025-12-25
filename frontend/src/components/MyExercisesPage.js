/**
 * MyExercisesPage - Bibliothèque d'exercices sauvegardés (P3.0)
 * 
 * Affiche la liste des exercices sauvegardés par l'utilisateur.
 * Permet de voir, dupliquer et supprimer des exercices.
 */

import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { useAuth } from "../hooks/useAuth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "./ui/dialog";
import Header from "./Header";
import { 
  FileText, 
  Trash2, 
  Eye, 
  Loader2,
  FolderOpen,
  AlertCircle,
  Copy,
  BookOpen,
  CheckCircle
} from "lucide-react";
import { useToast } from "../hooks/use-toast";
import MathRenderer from "./MathRenderer";
import { useLogin } from "../contexts/LoginContext";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * MathHtmlRenderer - Composant pour rendre du HTML contenant du LaTeX
 */
const MathHtmlRenderer = ({ html, className = "" }) => {
  if (!html) {
    return null;
  }

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
          'em': 'em', 'i': 'i', 'u': 'u', 'h1': 'h1', 'h2': 'h2', 'h3': 'h3',
          'h4': 'h4', 'h5': 'h5', 'h6': 'h6', 'ul': 'ul', 'ol': 'ol', 'li': 'li',
          'blockquote': 'blockquote', 'code': 'code', 'pre': 'pre'
        };
        
        const ReactTag = reactTagMap[tagName] || 'div';
        return React.createElement(ReactTag, props, children.length > 0 ? children : null);
      }
      
      return null;
    };
    
    return processNode(doc.body);
  };

  return (
    <div className={className}>
      {renderMixedContent(html)}
    </div>
  );
};

function MyExercisesPage() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { openLogin } = useLogin();
  
  // P0: Utiliser useAuth() pour cohérence avec ExerciseGeneratorPage
  const { sessionToken, userEmail, isPro } = useAuth();
  
  const [exercises, setExercises] = useState([]);
  const [loading, setLoading] = useState(true);
  
  // États pour la modal de visualisation
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [selectedExercise, setSelectedExercise] = useState(null);
  const [showSolution, setShowSolution] = useState(false); // BUG-010: Masquer solution par défaut
  
  // États pour les filtres
  const [filterCodeOfficiel, setFilterCodeOfficiel] = useState("");
  const [filterDifficulty, setFilterDifficulty] = useState("");

  // P0: Plus besoin d'initialiser auth manuellement - useAuth() le fait
  // Charger les exercices quand sessionToken devient disponible
  useEffect(() => {
    if (sessionToken && isPro) {
      loadExercises();
    } else if (!sessionToken) {
      // P0 UX: Stocker returnTo si non connecté
      sessionStorage.setItem('postLoginRedirect', '/mes-exercices');
      setLoading(false);
    }
  }, [sessionToken, isPro]); // Se déclenche quand sessionToken change

  const loadExercises = async () => {
    try {
      setLoading(true);
      
      // P0: Utiliser sessionToken de useAuth() au lieu de localStorage
      if (!sessionToken) {
        setLoading(false);
        return;
      }
      
      // Construire les query params
      const params = new URLSearchParams();
      if (filterCodeOfficiel) {
        params.append('code_officiel', filterCodeOfficiel);
      }
      if (filterDifficulty) {
        params.append('difficulty', filterDifficulty);
      }
      
      const url = `${API}/user/exercises${params.toString() ? '?' + params.toString() : ''}`;
      
      const response = await axios.get(url, {
        headers: {
          'X-Session-Token': sessionToken
        },
        withCredentials: true  // P0: Stabiliser l'auth côté front
      });
      
      setExercises(response.data.exercises || []);
      console.log('📚 Exercices chargés:', response.data.exercises?.length || 0);
    } catch (error) {
      console.error('Erreur chargement exercices:', error);
      if (error.response?.status === 401) {
        toast({
          title: "Session expirée",
          description: "Veuillez vous reconnecter",
          variant: "destructive"
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // Recharger quand les filtres changent
  useEffect(() => {
    if (sessionToken && isPro) {
      loadExercises();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filterCodeOfficiel, filterDifficulty, sessionToken, isPro]);

  const handleDeleteExercise = async (exerciseUid) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cet exercice ?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/user/exercises/${exerciseUid}`, {
        headers: {
          'X-Session-Token': sessionToken
        },
        withCredentials: true  // P0: Stabiliser l'auth côté front
      });
      
      setExercises(exercises.filter(ex => ex.exercise_uid !== exerciseUid));
      
      toast({
        title: "✅ Exercice supprimé",
        description: "L'exercice a été supprimé de votre bibliothèque",
        variant: "default"
      });
      
      console.log('🗑️ Exercice supprimé:', exerciseUid);
    } catch (error) {
      console.error('Erreur suppression exercice:', error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer l'exercice",
        variant: "destructive"
      });
    }
  };

  const handleDuplicateExercise = async (exercise) => {
    // P3.0: Dupliquer = créer un nouvel exercice avec un nouveau seed
    // Pour l'instant, on génère un nouvel exercise_uid et on sauvegarde
    const newExerciseUid = `ex_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    try {
      const saveData = {
        exercise_uid: newExerciseUid,
        generator_key: exercise.generator_key,
        code_officiel: exercise.code_officiel,
        difficulty: exercise.difficulty,
        seed: exercise.seed ? exercise.seed + 1 : Date.now(), // Nouveau seed
        variables: exercise.variables || {},
        enonce_html: exercise.enonce_html,
        solution_html: exercise.solution_html,
        metadata: exercise.metadata || {}
      };
      
      await axios.post(`${API}/user/exercises`, saveData, {
        headers: {
          'X-Session-Token': sessionToken
        },
        withCredentials: true  // P0: Stabiliser l'auth côté front
      });
      
      // Recharger la liste
      await loadExercises();
      
      toast({
        title: "✅ Exercice dupliqué",
        description: "Une copie de l'exercice a été créée",
        variant: "default"
      });
      
    } catch (error) {
      console.error('Erreur duplication exercice:', error);
      toast({
        title: "Erreur",
        description: "Impossible de dupliquer l'exercice",
        variant: "destructive"
      });
    }
  };

  const handleViewExercise = (exercise) => {
    setSelectedExercise(exercise);
    setShowSolution(false); // BUG-010: Réinitialiser à "énoncé" par défaut
    setViewModalOpen(true);
  };

  const handleLogin = () => {
    // P0 UX: Ouvrir le modal de login avec returnTo
    openLogin('/mes-exercices');
  };

  const handleLogout = async () => {
    try {
      if (sessionToken) {
        await axios.post(`${API}/auth/logout`, {}, {
          headers: {
            'X-Session-Token': sessionToken
          }
        });
      }
      
      localStorage.removeItem('lemaitremot_session_token');
      localStorage.removeItem('lemaitremot_user_email');
      localStorage.removeItem('lemaitremot_login_method');
      
      // P0: useAuth() se mettra à jour automatiquement via l'événement storage
      // Plus besoin de setSessionToken/setUserEmail/setIsPro
      
      console.log('✅ Déconnexion réussie');
      navigate('/');
      
    } catch (error) {
      console.error('Erreur déconnexion:', error);
    }
  };

  // Format date
  const formatDate = (dateString) => {
    if (!dateString) return "Date inconnue";
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return "Date inconnue";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <Header 
        isPro={isPro}
        userEmail={userEmail}
        onLogin={handleLogin}
        onLogout={handleLogout}
      />
      
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <BookOpen className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">Mes exercices</h1>
          </div>
          <p className="text-lg text-gray-600">
            Retrouvez tous vos exercices sauvegardés
          </p>
        </div>

        {!sessionToken ? (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="text-center py-12">
              <AlertCircle className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Connexion requise
              </h3>
              <p className="text-gray-600 mb-4">
                Connectez-vous pour accéder à votre bibliothèque d'exercices
              </p>
              <Button onClick={handleLogin}>
                Se connecter
              </Button>
            </CardContent>
          </Card>
        ) : loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">Chargement...</span>
          </div>
        ) : exercises.length === 0 ? (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="text-center py-12">
              <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Aucun exercice sauvegardé
              </h3>
              <p className="text-gray-600 mb-4">
                Commencez par générer et sauvegarder vos premiers exercices
              </p>
              <Button onClick={() => navigate('/generer')}>
                Générer des exercices
              </Button>
            </CardContent>
          </Card>
        ) : (
          <>
            {/* Filtres */}
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Filtres</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Code officiel
                    </label>
                    <input
                      type="text"
                      value={filterCodeOfficiel}
                      onChange={(e) => setFilterCodeOfficiel(e.target.value)}
                      placeholder="Ex: 6e_N08"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">
                      Difficulté
                    </label>
                    <select
                      value={filterDifficulty}
                      onChange={(e) => setFilterDifficulty(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    >
                      <option value="">Toutes</option>
                      <option value="facile">Facile</option>
                      <option value="moyen">Moyen</option>
                      <option value="difficile">Difficile</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Liste des exercices */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {exercises.map((exercise) => (
                <Card key={exercise.exercise_uid} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2">
                          {exercise.code_officiel || "Exercice"}
                        </CardTitle>
                        <CardDescription className="flex items-center gap-2 flex-wrap">
                          {exercise.generator_key && (
                            <Badge variant="outline" className="text-xs">
                              {exercise.generator_key}
                            </Badge>
                          )}
                          {exercise.difficulty && (
                            <Badge variant="secondary" className="text-xs">
                              {exercise.difficulty}
                            </Badge>
                          )}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="text-xs text-gray-500">
                        Sauvegardé le {formatDate(exercise.created_at)}
                      </div>

                      <div className="flex gap-2 pt-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleViewExercise(exercise)}
                          className="flex-1"
                        >
                          <Eye className="h-4 w-4 mr-1" />
                          Voir
                        </Button>
                        
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDuplicateExercise(exercise)}
                          className="flex-1"
                        >
                          <Copy className="h-4 w-4 mr-1" />
                          Dupliquer
                        </Button>
                        
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDeleteExercise(exercise.exercise_uid)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}

        {/* Modal de visualisation */}
        <Dialog open={viewModalOpen} onOpenChange={setViewModalOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Exercice sauvegardé</DialogTitle>
              <DialogDescription>
                {selectedExercise?.code_officiel} • {selectedExercise?.difficulty}
              </DialogDescription>
            </DialogHeader>
            
            {selectedExercise && (
              <div className="space-y-6 mt-4">
                {/* BUG-010: Onglets pour séparer énoncé et solution */}
                <Tabs value={showSolution ? "solution" : "enonce"} onValueChange={(value) => setShowSolution(value === "solution")} className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="enonce" className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Énoncé
                    </TabsTrigger>
                    <TabsTrigger value="solution" className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4" />
                      Solution
                    </TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="enonce" className="mt-4">
                    <div className="prose prose-lg max-w-none bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                      <div 
                        className="text-base leading-relaxed text-gray-800 space-y-3"
                        // P3.0.1: HTML trusted from backend templates; do not render user-provided raw HTML
                        // Le HTML provient de nos templates backend (P0.4), donc safe
                        dangerouslySetInnerHTML={{ __html: selectedExercise.enonce_html || '' }}
                      />
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="solution" className="mt-4">
                    <div className="prose prose-lg max-w-none bg-green-50 p-4 rounded-lg border border-green-200 shadow-sm">
                      <div 
                        className="text-base leading-relaxed text-gray-800 space-y-3"
                        // P3.0.1: HTML trusted from backend templates; do not render user-provided raw HTML
                        // Le HTML provient de nos templates backend (P0.4), donc safe
                        dangerouslySetInnerHTML={{ __html: selectedExercise.solution_html || '' }}
                      />
                    </div>
                  </TabsContent>
                </Tabs>

                {/* Métadonnées */}
                <div className="pt-4 border-t">
                  <h4 className="text-sm font-semibold text-gray-700 mb-2">Informations</h4>
                  <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                    <div><strong>Code officiel:</strong> {selectedExercise.code_officiel}</div>
                    <div><strong>Difficulté:</strong> {selectedExercise.difficulty}</div>
                    {selectedExercise.generator_key && (
                      <div><strong>Générateur:</strong> {selectedExercise.generator_key}</div>
                    )}
                    {selectedExercise.seed && (
                      <div><strong>Seed:</strong> {selectedExercise.seed}</div>
                    )}
                    <div><strong>Sauvegardé le:</strong> {formatDate(selectedExercise.created_at)}</div>
                  </div>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}

export default MyExercisesPage;

