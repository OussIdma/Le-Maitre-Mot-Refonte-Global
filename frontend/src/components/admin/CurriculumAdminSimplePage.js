import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle 
} from '../ui/card';
import { Badge } from '../ui/badge';
import { Input } from '../ui/input';
import { Button } from '../ui/button';
import { Alert, AlertDescription } from '../ui/alert';
import { 
  Search, 
  RefreshCw, 
  AlertCircle, 
  BookOpen,
  Pencil,
  Loader2
} from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

/**
 * Page d'administration du curriculum (version simplifiée et fonctionnelle)
 * 
 * Utilise les vraies routes backend :
 * - GET /api/v1/curriculum/6e/catalog
 * - Liens vers /admin/curriculum/{code}/exercises pour édition
 */
const CurriculumAdminSimplePage = () => {
  const navigate = useNavigate();
  
  const [catalog, setCatalog] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('all');

  // Charger le catalogue au montage
  useEffect(() => {
    fetchCatalog();
  }, []);

  const fetchCatalog = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${BACKEND_URL}/api/v1/curriculum/6e/catalog`);
      setCatalog(response.data);
    } catch (err) {
      console.error('Erreur chargement catalogue:', err);
      setError(err.response?.data?.detail?.message || err.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  // Filtrer les chapitres
  const filteredChapters = React.useMemo(() => {
    if (!catalog?.domains) return [];
    
    let chapters = [];
    catalog.domains.forEach(domain => {
      domain.chapters.forEach(ch => {
        chapters.push({ ...ch, domain: domain.name });
      });
    });

    // Filtre par domaine
    if (selectedDomain !== 'all') {
      chapters = chapters.filter(ch => ch.domain === selectedDomain);
    }

    // Filtre par recherche
    if (searchTerm) {
      const search = searchTerm.toLowerCase();
      chapters = chapters.filter(ch => 
        ch.code_officiel.toLowerCase().includes(search) ||
        ch.libelle.toLowerCase().includes(search)
      );
    }

    return chapters;
  }, [catalog, searchTerm, selectedDomain]);

  const handleEditChapter = (code) => {
    navigate(`/admin/curriculum/${code}/exercises`);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        <span className="ml-3 text-lg">Chargement du curriculum...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button onClick={fetchCatalog} className="mt-4">
          <RefreshCw className="h-4 w-4 mr-2" />
          Réessayer
        </Button>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-3">
              <BookOpen className="h-8 w-8 text-blue-600" />
              Administration Curriculum 6e
            </h1>
            <p className="text-gray-600 mt-2">
              Gérer les chapitres et leurs générateurs d'exercices
            </p>
          </div>
          <Button variant="outline" onClick={fetchCatalog}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Actualiser
          </Button>
        </div>

        {catalog && (
          <div className="flex gap-2">
            <Badge variant="outline" className="bg-blue-50 text-blue-700">
              {filteredChapters.length} chapitres
            </Badge>
            <Badge variant="outline" className="bg-green-50 text-green-700">
              {catalog.domains?.length || 0} domaines
            </Badge>
          </div>
        )}
      </div>

      {/* Filtres */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Filtres</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Recherche */}
            <div>
              <label className="text-sm font-medium mb-2 block">Rechercher</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Code ou libellé..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Domaine */}
            <div>
              <label className="text-sm font-medium mb-2 block">Domaine</label>
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="w-full px-3 py-2 border rounded-md"
              >
                <option value="all">Tous les domaines</option>
                {catalog?.domains?.map(domain => (
                  <option key={domain.name} value={domain.name}>
                    {domain.name} ({domain.chapters.length})
                  </option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Liste des chapitres */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredChapters.map(chapter => (
          <Card key={chapter.code_officiel} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <CardTitle className="text-lg">{chapter.libelle}</CardTitle>
                  <CardDescription className="mt-1">
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {chapter.code_officiel}
                    </code>
                  </CardDescription>
                </div>
                <Badge 
                  variant={chapter.status === 'prod' ? 'default' : 'secondary'}
                  className="ml-2"
                >
                  {chapter.status}
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {/* Domaine */}
                <div className="text-sm text-gray-600">
                  <strong>Domaine :</strong> {chapter.domain}
                </div>

                {/* Générateurs */}
                <div>
                  <div className="text-sm font-medium mb-2">
                    Générateurs ({chapter.generators?.length || 0})
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {chapter.generators?.slice(0, 3).map(gen => (
                      <Badge key={gen} variant="outline" className="text-xs">
                        {gen}
                      </Badge>
                    ))}
                    {chapter.generators?.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{chapter.generators.length - 3}
                      </Badge>
                    )}
                  </div>
                </div>

                {/* Actions */}
                <Button 
                  onClick={() => handleEditChapter(chapter.code_officiel)}
                  className="w-full mt-4"
                  size="sm"
                >
                  <Pencil className="h-4 w-4 mr-2" />
                  Gérer les exercices
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {filteredChapters.length === 0 && (
        <Card className="py-12">
          <CardContent className="text-center text-gray-500">
            <AlertCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p>Aucun chapitre trouvé</p>
            <p className="text-sm mt-2">
              Essayez de modifier les filtres ou la recherche
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default CurriculumAdminSimplePage;




