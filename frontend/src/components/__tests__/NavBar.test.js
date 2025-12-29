/**
 * Tests pour NavBar component
 * 
 * Vérifie l'affichage correct selon l'état d'authentification
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import NavBar from '../NavBar';
import { useAuth } from '../../hooks/useAuth';
import { useLogin } from '../../contexts/LoginContext';
import { useSelection } from '../../contexts/SelectionContext';

// Mock des hooks
jest.mock('../../hooks/useAuth');
jest.mock('../../contexts/LoginContext');
jest.mock('../../contexts/SelectionContext');
jest.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key,
  }),
}));

const mockUseAuth = useAuth;
const mockUseLogin = useLogin;
const mockUseSelection = useSelection;

// Helper pour rendre NavBar avec les mocks
const renderNavBar = (authState, loginContext = {}, selectionContext = {}) => {
  mockUseAuth.mockReturnValue(authState);
  mockUseLogin.mockReturnValue({
    openLogin: jest.fn(),
    ...loginContext
  });
  mockUseSelection.mockReturnValue({
    selectionCount: 0,
    ...selectionContext
  });
  
  return render(
    <BrowserRouter>
      <NavBar />
    </BrowserRouter>
  );
};

describe('NavBar - Affichage selon userEmail', () => {
  test('userEmail null => affiche "Se connecter"', () => {
    renderNavBar({
      userEmail: null,
      isPro: false,
      isLoading: false,
      sessionToken: null
    });
    
    expect(screen.getByText(/Se connecter/i)).toBeInTheDocument();
    expect(screen.queryByText(/test@example.com/i)).not.toBeInTheDocument();
  });
  
  test('userEmail undefined => affiche "Se connecter"', () => {
    renderNavBar({
      userEmail: undefined,
      isPro: false,
      isLoading: false,
      sessionToken: null
    });
    
    expect(screen.getByText(/Se connecter/i)).toBeInTheDocument();
  });
  
  test('userEmail chaîne vide => affiche "Se connecter"', () => {
    renderNavBar({
      userEmail: '',
      isPro: false,
      isLoading: false,
      sessionToken: null
    });
    
    expect(screen.getByText(/Se connecter/i)).toBeInTheDocument();
  });
  
  test('userEmail espaces uniquement => affiche "Se connecter"', () => {
    renderNavBar({
      userEmail: '   ',
      isPro: false,
      isLoading: false,
      sessionToken: null
    });
    
    expect(screen.getByText(/Se connecter/i)).toBeInTheDocument();
  });
  
  test('userEmail non vide => affiche email', () => {
    renderNavBar({
      userEmail: 'test@example.com',
      isPro: false,
      isLoading: false,
      sessionToken: 'valid_token'
    });
    
    expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
    expect(screen.queryByText(/Se connecter/i)).not.toBeInTheDocument();
  });
  
  test('userEmail avec isPro => affiche email + badge Pro', () => {
    renderNavBar({
      userEmail: 'pro@example.com',
      isPro: true,
      isLoading: false,
      sessionToken: 'valid_token'
    });
    
    expect(screen.getByText(/pro@example.com/i)).toBeInTheDocument();
    expect(screen.getByText(/Pro/i)).toBeInTheDocument();
  });
});

describe('NavBar - État de chargement', () => {
  test('isLoading true => affiche "Chargement..."', () => {
    renderNavBar({
      userEmail: null,
      isPro: false,
      isLoading: true,
      sessionToken: null
    });
    
    expect(screen.getByText(/Chargement/i)).toBeInTheDocument();
    expect(screen.queryByText(/Se connecter/i)).not.toBeInTheDocument();
  });
  
  test('isLoading false + userEmail null => affiche "Se connecter"', () => {
    renderNavBar({
      userEmail: null,
      isPro: false,
      isLoading: false,
      sessionToken: null
    });
    
    expect(screen.getByText(/Se connecter/i)).toBeInTheDocument();
    expect(screen.queryByText(/Chargement/i)).not.toBeInTheDocument();
  });
});

describe('NavBar - Après event auth-changed avec userEmail null', () => {
  test('après auth-changed avec userEmail null => repasse à "Se connecter"', () => {
    // Arrange: Initialement avec email
    const { rerender } = renderNavBar({
      userEmail: 'test@example.com',
      isPro: false,
      isLoading: false,
      sessionToken: 'token'
    });
    
    expect(screen.getByText(/test@example.com/i)).toBeInTheDocument();
    
    // Act: Simuler auth-changed avec userEmail null
    mockUseAuth.mockReturnValue({
      userEmail: null,
      isPro: false,
      isLoading: false,
      sessionToken: null
    });
    
    rerender(
      <BrowserRouter>
        <NavBar />
      </BrowserRouter>
    );
    
    // Assert: Doit afficher "Se connecter"
    expect(screen.getByText(/Se connecter/i)).toBeInTheDocument();
    expect(screen.queryByText(/test@example.com/i)).not.toBeInTheDocument();
  });
});

describe('NavBar - Bouton déconnexion', () => {
  test('utilisateur connecté => affiche bouton déconnexion', () => {
    renderNavBar({
      userEmail: 'test@example.com',
      isPro: false,
      isLoading: false,
      sessionToken: 'token'
    });
    
    // Le bouton de déconnexion devrait être présent (icône LogOut)
    const logoutButton = screen.getByTitle(/Se déconnecter/i);
    expect(logoutButton).toBeInTheDocument();
  });
});

