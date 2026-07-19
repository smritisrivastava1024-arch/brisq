// In-memory JWT store — survives re-renders, cleared on tab close by design.
let memoryToken: string | null = null;

// Subscriber pattern so React components can react to token changes
// without needing a full Context or external state library.
type Listener = (token: string | null) => void;
const listeners = new Set<Listener>();

export const authStore = {
  setToken: (token: string) => {
    memoryToken = token;
    listeners.forEach((l) => l(token));
  },
  getToken: (): string | null => memoryToken,
  clearToken: () => {
    memoryToken = null;
    listeners.forEach((l) => l(null));
  },
  subscribe: (listener: Listener): (() => void) => {
    listeners.add(listener);
    return () => listeners.delete(listener);
  },
};

// React hook — gives components reactivity on login/logout
import { useState, useEffect } from 'react';

export function useAuthToken(): string | null {
  const [token, setToken] = useState<string | null>(authStore.getToken());

  useEffect(() => {
    // Sync initial value in case something set the token before mount
    setToken(authStore.getToken());
    return authStore.subscribe(setToken);
  }, []);

  return token;
}

export function useAuth() {
  const login = async (password: string) => {
    const res = await fetch('/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password }),
    });
    if (!res.ok) {
      throw Object.assign(new Error('Login failed'), { status: res.status });
    }
    const data = await res.json();
    authStore.setToken(data.access_token);
  };

  const logout = () => {
    authStore.clearToken();
  };

  return { login, logout };
}
