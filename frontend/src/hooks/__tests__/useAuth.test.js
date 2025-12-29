/**
 * Tests unitaires pour useAuth hook
 * 
 * Vérifie le comportement d'authentification, notamment:
 * - Nettoyage du localStorage après 401
 * - Anti-réentrance lors du cleanup
 * - Gestion des événements auth-changed
 */

import { renderHook, waitFor, act } from '@testing-library/react';
import axios from 'axios';
import { useAuth } from '../useAuth';

// Mock axios
jest.mock('axios');
const mockedAxios = axios;

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: jest.fn((key) => store[key] || null),
    setItem: jest.fn((key, value) => {
      store[key] = value.toString();
    }),
    removeItem: jest.fn((key) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
  };
})();

// Mock window.dispatchEvent
const mockDispatchEvent = jest.fn();

// Mock window.addEventListener/removeEventListener
const mockAddEventListener = jest.fn();
const mockRemoveEventListener = jest.fn();

beforeAll(() => {
  global.localStorage = localStorageMock;
  global.window = {
    ...global.window,
    dispatchEvent: mockDispatchEvent,
    addEventListener: mockAddEventListener,
    removeEventListener: mockRemoveEventListener,
  };
  
  // Mock REACT_APP_BACKEND_URL
  process.env.REACT_APP_BACKEND_URL = 'http://localhost:8000';
});

beforeEach(() => {
  // Reset mocks
  jest.clearAllMocks();
  localStorageMock.clear();
  mockDispatchEvent.mockClear();
  mockAddEventListener.mockClear();
  mockRemoveEventListener.mockClear();
});

describe('useAuth - Token invalide (401)', () => {
  test('token invalide en localStorage + refresh => /api/auth/me renvoie 401 - localStorage nettoyé', async () => {
    // Arrange: Mettre un token invalide dans localStorage
    localStorageMock.setItem('lemaitremot_session_token', 'invalid_token');
    localStorageMock.setItem('lemaitremot_user_email', 'test@example.com');
    localStorageMock.setItem('lemaitremot_login_method', 'session');
    
    // Mock axios pour retourner 401
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });
    
    // Act: Rendre le hook
    const { result } = renderHook(() => useAuth());
    
    // Attendre que le hook ait fini de traiter
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    }, { timeout: 3000 });
    
    // Assert: localStorage doit être nettoyé
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('lemaitremot_session_token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('lemaitremot_user_email');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('lemaitremot_login_method');
    
    // Assert: État final doit être null
    expect(result.current.sessionToken).toBe(null);
    expect(result.current.userEmail).toBe(null);
    expect(result.current.isPro).toBe(false);
    expect(result.current.isLoading).toBe(false);
    
    // Assert: Événement auth-changed doit être dispatché
    await waitFor(() => {
      expect(mockDispatchEvent).toHaveBeenCalled();
    });
  });
  
  test('token invalide - toutes les clés auth sont nettoyées (variantes incluses)', async () => {
    // Arrange: Mettre des clés auth dans localStorage
    localStorageMock.setItem('lemaitremot_session_token', 'invalid');
    localStorageMock.setItem('lemaitremot_user_email', 'test@example.com');
    localStorageMock.setItem('userEmail', 'test@example.com'); // Variante
    localStorageMock.setItem('email', 'test@example.com'); // Variante
    
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });
    
    // Act
    const { result } = renderHook(() => useAuth());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    // Assert: Toutes les clés doivent être supprimées
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('lemaitremot_session_token');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('lemaitremot_user_email');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('userEmail');
    expect(localStorageMock.removeItem).toHaveBeenCalledWith('email');
  });
});

describe('useAuth - handleAuthChanged avec token absent', () => {
  test('handleAuthChanged avec token absent - ne relit pas localStorage, force state à null', async () => {
    // Arrange: Pas de token dans localStorage
    localStorageMock.getItem.mockReturnValue(null);
    
    // Act: Rendre le hook
    const { result } = renderHook(() => useAuth());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    // Simuler l'événement auth-changed
    const authChangedEvent = new Event('lmm:auth-changed');
    
    await act(async () => {
      // Trouver le handler enregistré et l'appeler
      const handlerCall = mockAddEventListener.mock.calls.find(
        call => call[0] === 'lmm:auth-changed'
      );
      if (handlerCall && handlerCall[1]) {
        handlerCall[1](authChangedEvent);
      }
    });
    
    await waitFor(() => {
      expect(result.current.sessionToken).toBe(null);
      expect(result.current.userEmail).toBe(null);
    });
    
    // Assert: getItem ne doit pas être appelé en boucle
    const getItemCalls = localStorageMock.getItem.mock.calls.filter(
      call => call[0] === 'lemaitremot_session_token'
    );
    // Devrait être appelé une fois au montage, pas en boucle
    expect(getItemCalls.length).toBeLessThanOrEqual(2);
  });
});

describe('useAuth - Anti-réentrance', () => {
  test('isClearingRef empêche la relecture pendant cleanup', async () => {
    // Arrange: Token invalide
    localStorageMock.setItem('lemaitremot_session_token', 'invalid');
    
    mockedAxios.get.mockRejectedValueOnce({
      response: { status: 401 }
    });
    
    // Act
    const { result } = renderHook(() => useAuth());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    // Simuler plusieurs événements auth-changed rapidement
    const authChangedEvent = new Event('lmm:auth-changed');
    
    await act(async () => {
      const handlerCall = mockAddEventListener.mock.calls.find(
        call => call[0] === 'lmm:auth-changed'
      );
      if (handlerCall && handlerCall[1]) {
        // Appeler plusieurs fois rapidement
        handlerCall[1](authChangedEvent);
        handlerCall[1](authChangedEvent);
        handlerCall[1](authChangedEvent);
      }
    });
    
    // Assert: getItem ne doit pas être appelé en boucle excessive
    const getItemCalls = localStorageMock.getItem.mock.calls;
    // Devrait être limité (pas de boucle infinie)
    expect(getItemCalls.length).toBeLessThan(20);
  });
});

describe('useAuth - Token valide', () => {
  test('token valide - état mis à jour avec email et isPro', async () => {
    // Arrange: Token valide
    localStorageMock.setItem('lemaitremot_session_token', 'valid_token');
    localStorageMock.setItem('lemaitremot_user_email', 'test@example.com');
    
    mockedAxios.get.mockResolvedValueOnce({
      data: {
        email: 'test@example.com',
        is_pro: true
      }
    });
    
    // Act
    const { result } = renderHook(() => useAuth());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    // Assert: État doit être mis à jour
    expect(result.current.sessionToken).toBe('valid_token');
    expect(result.current.userEmail).toBe('test@example.com');
    expect(result.current.isPro).toBe(true);
    expect(result.current.isLoading).toBe(false);
  });
});

describe('useAuth - Pas de token', () => {
  test('pas de token - état initialisé à null', async () => {
    // Arrange: Pas de token
    localStorageMock.getItem.mockReturnValue(null);
    
    // Act
    const { result } = renderHook(() => useAuth());
    
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
    
    // Assert: État doit être null
    expect(result.current.sessionToken).toBe(null);
    expect(result.current.userEmail).toBe(null);
    expect(result.current.isPro).toBe(false);
    expect(result.current.isLoading).toBe(false);
  });
});

