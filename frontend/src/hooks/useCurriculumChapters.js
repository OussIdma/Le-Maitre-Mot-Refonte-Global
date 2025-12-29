/**
 * Hook pour charger et rechercher les chapitres du curriculum
 * 
 * PR9: Parcours "3 clics" - Chargement curriculum depuis MongoDB
 * - Fetch chapters depuis /api/admin/curriculum/{niveau} ou /api/catalogue/levels/{niveau}/chapters
 * - Index par niveau
 * - Recherche par nom, code officiel, tags
 */

import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

/**
 * Hook pour charger et rechercher les chapitres du curriculum
 * 
 * @param {string} niveau - Niveau scolaire (CP, CE1, ..., Tle)
 * @returns {Object} { chapters, loading, error, search, groupByLevel }
 */
export function useCurriculumChapters(niveau = null) {
  const [chapters, setChapters] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [chaptersByLevel, setChaptersByLevel] = useState({});

  // Charger les chapitres pour un niveau donné
  const loadChapters = async (niveauToLoad) => {
    if (!niveauToLoad) {
      setChapters([]);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let transformedChapters = [];

      // Essayer d'abord l'API curriculum (source DB)
      try {
        const response = await axios.get(`${API}/admin/curriculum/${niveauToLoad}`);
        const data = response.data;
        const chaptersList = data.chapitres || [];
        transformedChapters = chaptersList.map(ch => ({
          id: ch.code_officiel || ch.id,
          code_officiel: ch.code_officiel || ch.id,
          titre: ch.titre,
          domaine: ch.domaine,
          niveau: ch.niveau || niveauToLoad,
          nb_exercises: ch.nb_exercises || null,
          tags: ch.tags || [],
          ordre: ch.ordre || 0
        }));
      } catch (err) {
        // Fallback sur l'API catalogue
        const response = await axios.get(`${API}/catalogue/levels/${niveauToLoad}/chapters`);
        const chaptersList = response.data || [];
        transformedChapters = chaptersList.map(ch => ({
          id: ch.id || ch.code_officiel,
          code_officiel: ch.code || ch.code_officiel || ch.id,
          titre: ch.titre,
          domaine: ch.domaine,
          niveau: ch.niveau || niveauToLoad,
          nb_exercises: ch.nb_exercises || null,
          tags: [],
          ordre: ch.ordre || 0
        }));
      }

      setChapters(transformedChapters);

      // Mettre à jour l'index par niveau
      setChaptersByLevel(prev => ({
        ...prev,
        [niveauToLoad]: transformedChapters
      }));

    } catch (err) {
      console.error('❌ Erreur chargement chapitres:', err);
      setError(err.response?.data?.detail || err.message || 'Impossible de charger les chapitres');
      setChapters([]);
    } finally {
      setLoading(false);
    }
  };

  // Charger automatiquement si niveau fourni
  useEffect(() => {
    if (niveau) {
      loadChapters(niveau);
    } else {
      setChapters([]);
    }
  }, [niveau]);

  /**
   * Rechercher des chapitres par texte
   * 
   * @param {string} searchText - Texte de recherche
   * @param {string} niveauFilter - Filtrer par niveau (optionnel)
   * @returns {Array} Liste des chapitres correspondants
   */
  const search = (searchText, niveauFilter = null) => {
    if (!searchText || searchText.trim() === '') {
      return niveauFilter ? chaptersByLevel[niveauFilter] || [] : chapters;
    }

    const searchLower = searchText.toLowerCase().trim();
    const chaptersToSearch = niveauFilter 
      ? (chaptersByLevel[niveauFilter] || [])
      : chapters;

    return chaptersToSearch.filter(ch => {
      // Recherche dans le titre
      if (ch.titre?.toLowerCase().includes(searchLower)) return true;
      
      // Recherche dans le code officiel
      if (ch.code_officiel?.toLowerCase().includes(searchLower)) return true;
      
      // Recherche dans le domaine
      if (ch.domaine?.toLowerCase().includes(searchLower)) return true;
      
      // Recherche dans les tags
      if (ch.tags && Array.isArray(ch.tags)) {
        if (ch.tags.some(tag => tag.toLowerCase().includes(searchLower))) return true;
      }
      
      return false;
    });
  };

  /**
   * Grouper les chapitres par niveau
   * 
   * @returns {Object} { "6e": [...], "5e": [...], ... }
   */
  const groupByLevel = useMemo(() => {
    return chaptersByLevel;
  }, [chaptersByLevel]);

  return {
    chapters,
    loading,
    error,
    search,
    groupByLevel,
    loadChapters,
    reload: () => niveau && loadChapters(niveau)
  };
}

