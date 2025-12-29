import React, { createContext, useContext, useState, useEffect, useCallback } from "react";

const STORAGE_KEY = "lemaitremot_selection";

const SelectionContext = createContext(null);

export function SelectionProvider({ children }) {
  const [selectedExercises, setSelectedExercises] = useState([]);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // Valider que chaque élément a les propriétés minimales
          const validExercises = parsed.filter(ex => ex && ex.uniqueId);
          if (validExercises.length > 0) {
            setSelectedExercises(validExercises);
            console.log(`✅ Sélection restaurée depuis localStorage: ${validExercises.length} exercice(s)`);
          }
        }
      }
    } catch (e) {
      console.warn("❌ Failed to load selection from localStorage:", e);
      // En cas d'erreur, nettoyer le localStorage corrompu
      try {
        localStorage.removeItem(STORAGE_KEY);
      } catch (cleanupError) {
        console.warn("Failed to cleanup corrupted localStorage:", cleanupError);
      }
    }
  }, []);

  // Persist to localStorage on change
  useEffect(() => {
    try {
      if (selectedExercises.length > 0) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(selectedExercises));
        console.log(`💾 Sélection sauvegardée: ${selectedExercises.length} exercice(s)`);
      } else {
        // Si la sélection est vide, on peut soit garder le localStorage vide, soit le supprimer
        // On garde un tableau vide pour éviter les erreurs de parsing
        localStorage.setItem(STORAGE_KEY, JSON.stringify([]));
      }
    } catch (e) {
      console.warn("❌ Failed to save selection to localStorage:", e);
    }
  }, [selectedExercises]);

  const addExercise = useCallback((exercise) => {
    setSelectedExercises((prev) => {
      // Avoid duplicates by checking unique id
      const exists = prev.some((ex) => ex.uniqueId === exercise.uniqueId);
      if (exists) return prev;
      return [...prev, exercise];
    });
  }, []);

  const removeExercise = useCallback((uniqueId) => {
    setSelectedExercises((prev) => prev.filter((ex) => ex.uniqueId !== uniqueId));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedExercises([]);
  }, []);

  const reorderExercises = useCallback((fromIndex, toIndex) => {
    setSelectedExercises((prev) => {
      if (fromIndex < 0 || fromIndex >= prev.length || toIndex < 0 || toIndex >= prev.length) {
        return prev;
      }
      const newList = [...prev];
      const [moved] = newList.splice(fromIndex, 1);
      newList.splice(toIndex, 0, moved);
      return newList;
    });
  }, []);

  const isSelected = useCallback((uniqueId) => {
    return selectedExercises.some((ex) => ex.uniqueId === uniqueId);
  }, [selectedExercises]);

  const selectionCount = selectedExercises.length;

  return (
    <SelectionContext.Provider
      value={{
        selectedExercises,
        selectionCount,
        addExercise,
        removeExercise,
        clearSelection,
        reorderExercises,
        isSelected,
      }}
    >
      {children}
    </SelectionContext.Provider>
  );
}

export function useSelection() {
  const context = useContext(SelectionContext);
  if (!context) {
    throw new Error("useSelection must be used within a SelectionProvider");
  }
  return context;
}
