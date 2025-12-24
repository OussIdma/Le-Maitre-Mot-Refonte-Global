/**
 * MySheetsPageP31 - Page "Mes fiches" (P3.1)
 * 
 * Liste simple et claire des fiches d'exercices créées par l'utilisateur.
 * Permet de créer, ouvrir, exporter et supprimer des fiches.
 */
import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Textarea } from "./ui/textarea.jsx";
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
  Download, 
  Trash2, 
  Eye, 
  Loader2,
  FolderOpen,
  Plus,
  AlertCircle
} from "lucide-react";
import { useToast } from "../hooks/use-toast";
import { useLogin } from "../contexts/LoginContext";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function MySheetsPageP31() {
  const navigate = useNavigate();
  const { toast } = useToast();
  const { openLogin } = useLogin();
  const { t } = useTranslation();
  
  const [sheets, setSheets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState("");
  const [isPro, setIsPro] = useState(false);
  const [sessionToken, setSessionToken] = useState("");
  const [creating, setCreating] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newSheetTitle, setNewSheetTitle] = useState("");
  const [newSheetDescription, setNewSheetDescription] = useState("");

  useEffect(() => {
    const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    if (storedSessionToken && storedEmail && loginMethod === 'session') {
      setSessionToken(storedSessionToken);
      setUserEmail(storedEmail);
      setIsPro(true);
      loadSheets();
    } else {
      // P0 UX: Stocker returnTo si non connecté
      sessionStorage.setItem('postLoginRedirect', '/mes-fiches');
      setLoading(false);
    }
  }, []);

  // Recharger quand sessionToken devient disponible après login
  useEffect(() => {
    if (sessionToken && isPro) {
      loadSheets();
    }
  }, [sessionToken, isPro]);

  const loadSheets = async () => {
    try {
      setLoading(true);
      
      const sessionToken = localStorage.getItem('lemaitremot_session_token');
      if (!sessionToken) {
        setLoading(false);
        return;
      }
      
      // P3.1 HOTFIX: URL corrigée - /api/user/sheets (router a prefix /api/user/sheets)
      const response = await axios.get(`${API}/user/sheets`, {
        headers: {
          'X-Session-Token': sessionToken
        },
        withCredentials: true  // P0/P1/P2: Cookies httpOnly
      });
      
      setSheets(response.data || []);
      console.log('📚 Fiches chargées:', response.data?.length || 0);
    } catch (error) {
      console.error('Erreur chargement fiches:', error);
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

  const handleOpenCreateModal = () => {
    if (!sessionToken) {
      openLogin('/mes-fiches');
      return;
    }
    setNewSheetTitle("");
    setNewSheetDescription("");
    setShowCreateModal(true);
  };

  const handleCreateSheet = async () => {
    // Validation UX minimale
    if (!newSheetTitle || !newSheetTitle.trim()) {
      toast({
        title: "Titre requis",
        description: "Veuillez saisir un titre pour la fiche",
        variant: "destructive"
      });
      return;
    }

    try {
      setCreating(true);
      
      // P3.1 HOTFIX: URL corrigée - /api/user/sheets (router a prefix /api/user/sheets)
      const response = await axios.post(
        `${API}/user/sheets`,
        {
          title: newSheetTitle.trim(),
          description: newSheetDescription.trim() || ""
        },
        {
          headers: {
            'X-Session-Token': sessionToken
          },
          withCredentials: true  // P0/P1/P2: Cookies httpOnly
        }
      );
      
      setShowCreateModal(false);
      setNewSheetTitle("");
      setNewSheetDescription("");
      
      // Rediriger vers la page d'édition
      navigate(`/mes-fiches/${response.data.sheet_uid}`);
      
      toast({
        title: t('sheets.created'),
        description: t('sheets.createdDescription'),
        variant: "default"
      });
    } catch (error) {
      console.error('Erreur création fiche:', error);
      const errorMessage = error.response?.data?.detail || error.message || "Erreur inconnue";
      const statusCode = error.response?.status;
      
      toast({
        title: t('sheets.createError'),
        description: `${t('sheets.createErrorDescription')} (${statusCode || 'N/A'})`,
        variant: "destructive"
      });
      
      // Debug console avec status/response
      console.error('Détails erreur:', {
        status: statusCode,
        response: error.response?.data,
        url: `${API}/user/sheets`
      });
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteSheet = async (sheetUid) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette fiche ?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/user/sheets/${sheetUid}`, {
        headers: {
          'X-Session-Token': sessionToken
        }
      });
      
      setSheets(sheets.filter(s => s.sheet_uid !== sheetUid));
      
      toast({
        title: "✅ Fiche supprimée",
        description: "La fiche a été supprimée",
        variant: "default"
      });
      
      console.log('🗑️ Fiche supprimée:', sheetUid);
    } catch (error) {
      console.error('Erreur suppression fiche:', error);
      toast({
        title: "Erreur",
        description: "Impossible de supprimer la fiche",
        variant: "destructive"
      });
    }
  };

  const handleLogin = () => {
    openLogin('/mes-fiches');
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
      
      setSessionToken("");
      setUserEmail("");
      setIsPro(false);
      
      console.log('✅ Déconnexion réussie');
      navigate('/');
    } catch (error) {
      console.error('Erreur déconnexion:', error);
    }
  };

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

  const getExerciseCount = (sheet) => {
    return sheet.exercises?.length || 0;
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
            <FolderOpen className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">Mes fiches</h1>
          </div>
          <p className="text-lg text-gray-600">
            Créez et organisez vos devoirs et contrôles
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
                Connectez-vous pour créer et gérer vos fiches d'exercices
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
        ) : (
          <>
            {/* Bouton créer */}
            <div className="mb-6 flex justify-end">
              <Button 
                onClick={handleOpenCreateModal}
                disabled={creating}
                className="bg-blue-600 hover:bg-blue-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                {t('sheets.newSheet')}
              </Button>
            </div>

            {sheets.length === 0 ? (
              <Card className="max-w-2xl mx-auto">
                <CardContent className="text-center py-12">
                  <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    Aucune fiche créée
                  </h3>
                  <p className="text-gray-600 mb-4">
                    Commencez par créer votre première fiche d'exercices
                  </p>
                  <Button onClick={handleOpenCreateModal} disabled={creating}>
                    <Plus className="h-4 w-4 mr-2" />
                    {t('sheets.createFirstSheet')}
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {sheets.map((sheet) => (
                  <Card key={sheet.sheet_uid} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-lg mb-2">
                            {sheet.title}
                          </CardTitle>
                          <CardDescription className="flex items-center gap-2 flex-wrap">
                            <Badge variant="secondary" className="text-xs">
                              {getExerciseCount(sheet)} exercice{getExerciseCount(sheet) > 1 ? 's' : ''}
                            </Badge>
                            <span className="text-xs text-gray-500">
                              Modifié {formatDate(sheet.updated_at)}
                            </span>
                          </CardDescription>
                        </div>
                        <FileText className="h-5 w-5 text-blue-600" />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {sheet.description && (
                          <p className="text-sm text-gray-600">{sheet.description}</p>
                        )}

                        <div className="flex gap-2 pt-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/mes-fiches/${sheet.sheet_uid}`)}
                            className="flex-1"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Ouvrir
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => navigate(`/mes-fiches/${sheet.sheet_uid}?export=pdf`)}
                            className="flex-1"
                          >
                            <Download className="h-4 w-4 mr-1" />
                            PDF
                          </Button>
                          
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => handleDeleteSheet(sheet.sheet_uid)}
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
            )}
          </>
        )}
      </div>

      {/* Modal création fiche - P3.1 HOTFIX: Remplace window.prompt par modal shadcn */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>{t('sheets.createTitle')}</DialogTitle>
            <DialogDescription>
              {t('sheets.createDescription')}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label htmlFor="sheet-title">{t('sheets.createTitle')} *</Label>
              <Input
                id="sheet-title"
                value={newSheetTitle}
                onChange={(e) => setNewSheetTitle(e.target.value)}
                placeholder={t('sheets.createTitle')}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && newSheetTitle.trim() && !creating) {
                    handleCreateSheet();
                  }
                }}
                autoFocus
              />
              {!newSheetTitle.trim() && (
                <p className="text-xs text-red-600">{t('sheets.titleRequired')}</p>
              )}
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="sheet-description">{t('sheets.createDescription')}</Label>
              <Textarea
                id="sheet-description"
                value={newSheetDescription}
                onChange={(e) => setNewSheetDescription(e.target.value)}
                placeholder={t('sheets.createDescription')}
                rows={3}
              />
            </div>
            
            <div className="flex justify-end gap-2 pt-4">
              <Button
                variant="outline"
                onClick={() => {
                  setShowCreateModal(false);
                  setNewSheetTitle("");
                  setNewSheetDescription("");
                }}
                disabled={creating}
              >
                {t('actions.cancel')}
              </Button>
              <Button
                onClick={handleCreateSheet}
                disabled={!newSheetTitle.trim() || creating}
                className="bg-blue-600 hover:bg-blue-700"
              >
                {creating ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    {t('actions.loading')}
                  </>
                ) : (
                  <>
                    <Plus className="h-4 w-4 mr-2" />
                    {t('sheets.create')}
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default MySheetsPageP31;

