import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Alert, AlertDescription } from './ui/alert';
import { 
  Calendar, 
  BookOpen, 
  Users, 
  Target,
  Clock,
  CheckCircle2,
  ArrowLeft,
  ExternalLink
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL || import.meta.env.REACT_APP_BACKEND_URL;

const RoadmapPage = () => {
  const navigate = useNavigate();
  const [roadmapData, setRoadmapData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchRoadmap();
  }, []);

  const fetchRoadmap = async () => {
    try {
      const response = await axios.get(`${API}/roadmap`);
      setRoadmapData(response.data);
      console.log('🗺️ Roadmap loaded:', response.data);
    } catch (error) {
      console.error('Error fetching roadmap:', error);
      setError('Erreur lors du chargement de la roadmap');
    } finally {
      setLoading(false);
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      active: {
        variant: 'success',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        textColor: 'text-green-800'
      },
      coming_soon: {
        variant: 'warning',
        bgColor: 'bg-orange-50', 
        borderColor: 'border-orange-200',
        textColor: 'text-orange-800'
      },
      planned: {
        variant: 'info',
        bgColor: 'bg-blue-50',
        borderColor: 'border-blue-200', 
        textColor: 'text-blue-800'
      },
      beta: {
        variant: 'secondary',
        bgColor: 'bg-purple-50',
        borderColor: 'border-purple-200',
        textColor: 'text-purple-800'
      },
      future: {
        variant: 'outline',
        bgColor: 'bg-gray-50',
        borderColor: 'border-gray-200',
        textColor: 'text-gray-600'
      }
    };
    return configs[status] || configs.future;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement de la roadmap...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 flex items-center justify-center">
        <Alert className="max-w-md border-red-200 bg-red-50">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const { roadmap, stats, phases } = roadmapData || {};

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Button 
                variant="ghost" 
                onClick={() => navigate('/')}
                className="flex items-center space-x-2"
              >
                <ArrowLeft className="h-4 w-4" />
                <span>Retour à l'app</span>
              </Button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">🗺️ Feuille de Route</h1>
                <p className="text-gray-600">Découvrez quand chaque matière sera disponible</p>
              </div>
            </div>
            <Button 
              onClick={() => navigate('/')}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Essayer maintenant
            </Button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Statistics Overview */}
        {stats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="text-center">
              <CardContent className="p-6">
                <div className="text-3xl font-bold text-blue-600 mb-2">
                  {stats.total.subjects}
                </div>
                <div className="text-sm text-gray-600">Matières totales</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="p-6">
                <div className="text-3xl font-bold text-green-600 mb-2">
                  {stats.total.chapters}
                </div>
                <div className="text-sm text-gray-600">Chapitres disponibles</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="p-6">
                <div className="text-3xl font-bold text-orange-600 mb-2">
                  {stats.active.subject_count}
                </div>
                <div className="text-sm text-gray-600">Matières actives</div>
              </CardContent>
            </Card>
            <Card className="text-center">
              <CardContent className="p-6">
                <div className="text-3xl font-bold text-purple-600 mb-2">
                  {stats.coming_soon.subject_count + stats.planned.subject_count}
                </div>
                <div className="text-sm text-gray-600">En développement</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Phases Timeline */}
        {phases && (
          <div className="mb-12">
            <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
              <Calendar className="h-5 w-5 mr-2" />
              Timeline de développement
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              {Object.entries(phases).map(([phaseKey, phase]) => {
                const statusConfig = getStatusConfig(phase.status);
                return (
                  <Card key={phaseKey} className={`${statusConfig.bgColor} ${statusConfig.borderColor} border-2`}>
                    <CardHeader className="pb-3">
                      <CardTitle className="text-lg">{phase.title}</CardTitle>
                      <CardDescription className="text-sm">
                        {phase.description}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        {phase.subjects.map((subject) => (
                          <Badge key={subject} variant="outline" className="text-xs">
                            {subject}
                          </Badge>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Detailed Roadmap by Status */}
        {roadmap && (
          <div className="space-y-8">
            <h2 className="text-xl font-semibold text-gray-900 flex items-center">
              <Target className="h-5 w-5 mr-2" />
              Matières par statut
            </h2>
            
            {Object.entries(roadmap).map(([status, statusData]) => {
              const statusConfig = getStatusConfig(status);
              const statusInfo = statusData.status_info;
              
              return (
                <div key={status} className="space-y-4">
                  <div className="flex items-center space-x-3">
                    <Badge variant={statusConfig.variant} className="text-sm">
                      {statusInfo.emoji} {statusInfo.label}
                    </Badge>
                    <span className="text-gray-600 text-sm">
                      {statusData.subjects.length} matières
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {statusData.subjects.map((subject) => (
                      <Card 
                        key={subject.name}
                        className={`${statusConfig.bgColor} ${statusConfig.borderColor} border`}
                      >
                        <CardHeader className="pb-3">
                          <div className="flex items-start justify-between">
                            <CardTitle className="text-lg flex items-center">
                              {statusInfo.emoji}
                              <span className="ml-2">{subject.name}</span>
                            </CardTitle>
                            {subject.expected && status !== 'active' && (
                              <Badge variant="outline" className="text-xs">
                                {subject.expected}
                              </Badge>
                            )}
                          </div>
                          <CardDescription className="text-sm">
                            {subject.description}
                          </CardDescription>
                        </CardHeader>
                        <CardContent>
                          <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Chapitres:</span>
                              <span className="font-medium">{subject.chapter_count}</span>
                            </div>
                            <div className="flex justify-between text-sm">
                              <span className="text-gray-600">Niveaux:</span>
                              <span className="font-medium">{subject.level_count}</span>
                            </div>
                            {subject.note && (
                              <div className="text-xs text-gray-500 mt-2 p-2 bg-white/50 rounded">
                                💡 {subject.note}
                              </div>
                            )}
                            {subject.features && subject.features.length > 0 && (
                              <div className="mt-2">
                                <div className="text-xs text-gray-600 mb-1">Fonctionnalités:</div>
                                <div className="flex flex-wrap gap-1">
                                  {subject.features.slice(0, 3).map((feature) => (
                                    <Badge key={feature} variant="secondary" className="text-xs">
                                      {feature}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* CTA Section */}
        <div className="mt-16 text-center">
          <Card className="max-w-2xl mx-auto bg-gradient-to-r from-blue-600 to-indigo-600 text-white border-0">
            <CardContent className="p-8">
              <h3 className="text-2xl font-bold mb-4">Prêt à commencer ?</h3>
              <p className="text-blue-100 mb-6">
                Commencez dès maintenant avec les matières disponibles et découvrez 
                la puissance de la génération d'exercices par IA !
              </p>
              <Button 
                size="lg"
                variant="secondary"
                onClick={() => navigate('/')}
                className="bg-white text-blue-600 hover:bg-gray-50"
              >
                <BookOpen className="h-5 w-5 mr-2" />
                Essayer Le Maître Mot
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default RoadmapPage;