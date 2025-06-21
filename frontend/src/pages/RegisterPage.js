import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import {
  Box,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Paper,
} from '@mui/material';
import { useAuth } from '../contexts/AuthContext';

const RegisterPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    full_name: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    setLoading(true);

    const result = await register({
      email: formData.email,
      password: formData.password,
      full_name: formData.full_name,
    });
    
    if (result.success) {
      navigate('/login');
    } else {
      setError(result.error);
    }
    
    setLoading(false);
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #000000 0%, #111111 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 2,
      }}
    >
      <Container maxWidth="sm">
        <Paper
          elevation={24}
          sx={{
            p: 4,
            borderRadius: 3,
            background: 'rgba(17, 17, 17, 0.95)',
            border: '1px solid rgba(90, 227, 134, 0.2)',
            backdropFilter: 'blur(10px)',
          }}
        >
          <Box textAlign="center" mb={4}>
            <Typography
              variant="h3"
              component="h1"
              sx={{
                fontWeight: 700,
                background: 'linear-gradient(135deg, #5AE386 0%, #3FC26B 100%)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                mb: 1,
              }}
            >
              I.A PRIORI
            </Typography>
            <Typography variant="h6" color="text.secondary">
              Crear Cuenta
            </Typography>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label="Nombre Completo"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              margin="normal"
              required
            />

            <TextField
              fullWidth
              label="Email"
              name="email"
              type="email"
              value={formData.email}
              onChange={handleChange}
              margin="normal"
              required
            />
            
            <TextField
              fullWidth
              label="Contraseña"
              name="password"
              type="password"
              value={formData.password}
              onChange={handleChange}
              margin="normal"
              required
            />

            <TextField
              fullWidth
              label="Confirmar Contraseña"
              name="confirmPassword"
              type="password"
              value={formData.confirmPassword}
              onChange={handleChange}
              margin="normal"
              required
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={loading}
              sx={{
                mt: 3,
                mb: 2,
                py: 1.5,
                background: 'linear-gradient(135deg, #5AE386 0%, #3FC26B 100%)',
                '&:hover': {
                  background: 'linear-gradient(135deg, #7FEB9F 0%, #5AE386 100%)',
                },
              }}
            >
              {loading ? 'Registrando...' : 'Crear Cuenta'}
            </Button>

            <Box textAlign="center">
              <Typography variant="body2" color="text.secondary">
                ¿Ya tienes una cuenta?{' '}
                <Link
                  to="/login"
                  style={{
                    color: '#5AE386',
                    textDecoration: 'none',
                  }}
                >
                  Inicia sesión aquí
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>
      </Container>
    </Box>
  );
};

export default RegisterPage; 