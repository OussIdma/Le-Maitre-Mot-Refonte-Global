import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import { Button } from "./ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";
import { Alert, AlertDescription } from "./ui/alert";
import Header from "./Header";
import { 
  FileText, 
  Download, 
  Trash2, 
  Eye, 
  Loader2,
  FolderOpen,
  AlertCircle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function MySheetsPage() {
  const navigate = useNavigate();
  
  const [sheets, setSheets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [userEmail, setUserEmail] = useState("");
  const [isPro, setIsPro] = useState(false);
  const [sessionToken, setSessionToken] = useState("");

  useEffect(() => {
    const storedSessionToken = localStorage.getItem('lemaitremot_session_token');
    const storedEmail = localStorage.getItem('lemaitremot_user_email');
    const loginMethod = localStorage.getItem('lemaitremot_login_method');
    
    if (storedSessionToken && storedEmail && loginMethod === 'session') {
      setSessionToken(storedSessionToken);
      setUserEmail(storedEmail);
      setIsPro(true);
    }
    
    loadSheets();
  }, []);

  const loadSheets = async () => {
    try {
      setLoading(true);
      
      const ownerId = localStorage.getItem('lemaitremot_user_email') || 
                      localStorage.getItem('lemaitremot_guest_id') || 
                      'anonymous';
      
      const response = await axios.get(`${API}/mathalea/sheets?owner_id=${ownerId}`);
      setSheets(response.data.items || []);
      
      console.log('📚 Fiches chargées:', response.data.items?.length || 0);
    } catch (error) {
      console.error('Erreur chargement fiches:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSheet = async (sheetId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette fiche ?')) {
      return;
    }
    
    try {
      await axios.delete(`${API}/mathalea/sheets/${sheetId}`);
      setSheets(sheets.filter(s => s.id !== sheetId));
      console.log('🗑️ Fiche supprimée:', sheetId);
    } catch (error) {
      console.error('Erreur suppression fiche:', error);
      alert('Erreur lors de la suppression de la fiche');
    }
  };

  const handleDownloadPDF = async (sheetId, titre) => {
    try {
      const config = {};
      if (sessionToken) {
        config.headers = {
          'X-Session-Token': sessionToken
        };
      }
      
      const response = await axios.post(
        `${API}/mathalea/sheets/${sheetId}/generate-pdf`,
        {},
        {
          ...config,
          responseType: 'blob'
        }
      );
      
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `LeMaitreMot_${titre}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      console.log('📥 PDF téléchargé:', titre);
    } catch (error) {
      console.error('Erreur téléchargement PDF:', error);
      alert('Erreur lors du téléchargement du PDF');
    }
  };

  const handleLogin = () => {
    navigate('/');
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
            Retrouvez toutes vos fiches d'exercices créées
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            <span className="ml-3 text-gray-600">Chargement...</span>
          </div>
        ) : sheets.length === 0 ? (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="text-center py-12">
              <FileText className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Aucune fiche créée
              </h3>
              <p className="text-gray-600 mb-4">
                Commencez par créer votre première fiche d'exercices
              </p>
              <Button onClick={() => navigate('/builder')}>
                Créer une fiche
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sheets.map((sheet) => (
              <Card key={sheet.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{sheet.titre}</CardTitle>
                      <CardDescription className="mt-1">
                        {sheet.niveau}
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
                    
                    <div className="flex items-center text-xs text-gray-500">
                      <span>
                        Créée le {new Date(sheet.created_at).toLocaleDateString('fr-FR')}
                      </span>
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDownloadPDF(sheet.id, sheet.titre)}
                        className="flex-1"
                      >
                        <Download className="h-4 w-4 mr-1" />
                        PDF
                      </Button>
                      
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleDeleteSheet(sheet.id)}
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

        {!loading && sheets.length > 0 && (
          <div className="text-center mt-8">
            <Button 
              variant="outline" 
              onClick={() => navigate('/builder')}
            >
              <FileText className="h-4 w-4 mr-2" />
              Créer une nouvelle fiche
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export default MySheetsPage;
