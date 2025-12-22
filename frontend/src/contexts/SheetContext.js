import React, { createContext, useContext, useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const SheetContext = createContext();

export const useSheet = () => {
  const context = useContext(SheetContext);
  if (!context) {
    return { currentSheetId: null };
  }
  return context;
};

export const SheetProvider = ({ children }) => {
  const [currentSheetId, setCurrentSheetId] = useState(null);
  const location = useLocation();

  // Détecter le sheetId depuis l'URL
  useEffect(() => {
    const match = location.pathname.match(/\/builder\/([^/]+)/);
    if (match) {
      setCurrentSheetId(match[1]);
      localStorage.setItem('current_sheet_id', match[1]);
    }
  }, [location.pathname]);

  return (
    <SheetContext.Provider value={{ currentSheetId, setCurrentSheetId }}>
      {children}
    </SheetContext.Provider>
  );
};
