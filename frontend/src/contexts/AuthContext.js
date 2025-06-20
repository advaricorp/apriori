import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import Cookies from 'js-cookie';
import toast from 'react-hot-toast';

const AuthContext = createContext({});

// Configure axios defaults
axios.defaults.baseURL = process.env.REACT_APP_API_URL || '';
axios.defaults.headers.common['Content-Type'] = 'application/json';

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(null);

  // Initialize auth state from cookies
  useEffect(() => {
    const initializeAuth = async () => {
      const savedToken = Cookies.get('apriori_token');
      const savedUser = Cookies.get('apriori_user');
      const savedOrg = Cookies.get('apriori_org');

      if (savedToken && savedUser && savedOrg) {
        try {
          // Set axios default header
          axios.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`;
          
          // Parse saved data
          setToken(savedToken);
          setUser(JSON.parse(savedUser));
          setOrganization(JSON.parse(savedOrg));
          
          // Verify token is still valid
          await getCurrentUser();
        } catch (error) {
          console.error('Error initializing auth:', error);
          logout();
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  // Set up axios interceptor for token refresh
  useEffect(() => {
    const interceptor = axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          logout();
          toast.error('Sesión expirada. Por favor inicia sesión nuevamente.');
        }
        return Promise.reject(error);
      }
    );

    return () => {
      axios.interceptors.response.eject(interceptor);
    };
  }, []);

  const login = async (email, password) => {
    try {
      setLoading(true);
      
      const response = await axios.post('/auth/login', {
        email,
        password,
      });

      const { access_token, user: userData, organization: orgData } = response.data;

      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // Save to state
      setToken(access_token);
      setUser(userData);
      setOrganization(orgData);

      // Save to cookies (7 days)
      Cookies.set('apriori_token', access_token, { expires: 7, secure: true, sameSite: 'strict' });
      Cookies.set('apriori_user', JSON.stringify(userData), { expires: 7, secure: true, sameSite: 'strict' });
      Cookies.set('apriori_org', JSON.stringify(orgData), { expires: 7, secure: true, sameSite: 'strict' });

      toast.success(`¡Bienvenido ${userData.full_name}!`);
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      const message = error.response?.data?.detail || 'Error de autenticación';
      toast.error(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const register = async (formData) => {
    try {
      setLoading(true);
      
      const response = await axios.post('/auth/register', formData);

      const { access_token, user: userData, organization: orgData } = response.data;

      // Set axios default header
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;

      // Save to state
      setToken(access_token);
      setUser(userData);
      setOrganization(orgData);

      // Save to cookies
      Cookies.set('apriori_token', access_token, { expires: 7, secure: true, sameSite: 'strict' });
      Cookies.set('apriori_user', JSON.stringify(userData), { expires: 7, secure: true, sameSite: 'strict' });
      Cookies.set('apriori_org', JSON.stringify(orgData), { expires: 7, secure: true, sameSite: 'strict' });

      toast.success(`¡Registro exitoso! Bienvenido ${userData.full_name}!`);
      return { success: true };
    } catch (error) {
      console.error('Register error:', error);
      const message = error.response?.data?.detail || 'Error en el registro';
      toast.error(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // Clear state
    setUser(null);
    setOrganization(null);
    setToken(null);

    // Clear cookies
    Cookies.remove('apriori_token');
    Cookies.remove('apriori_user');
    Cookies.remove('apriori_org');

    // Clear axios default header
    delete axios.defaults.headers.common['Authorization'];

    toast.success('Sesión cerrada correctamente');
  };

  const getCurrentUser = async () => {
    try {
      const response = await axios.get('/me');
      const { user: userData, organization: orgData } = response.data;
      
      setUser(userData);
      setOrganization(orgData);
      
      // Update cookies with fresh data
      Cookies.set('apriori_user', JSON.stringify(userData), { expires: 7, secure: true, sameSite: 'strict' });
      Cookies.set('apriori_org', JSON.stringify(orgData), { expires: 7, secure: true, sameSite: 'strict' });
      
      return userData;
    } catch (error) {
      console.error('Get current user error:', error);
      throw error;
    }
  };

  const isAuthenticated = () => {
    return !!token && !!user;
  };

  const hasRole = (roles) => {
    if (!user) return false;
    if (Array.isArray(roles)) {
      return roles.includes(user.role);
    }
    return user.role === roles;
  };

  const value = {
    user,
    organization,
    token,
    loading,
    login,
    register,
    logout,
    getCurrentUser,
    isAuthenticated,
    hasRole,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}; 