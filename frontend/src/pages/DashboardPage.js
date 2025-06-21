import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  AppBar,
  Toolbar,
  IconButton,
} from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
} from 'recharts';
import { LogoutOutlined } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const DashboardPage = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [stats] = useState({
    totalInterviews: 125,
    averageSatisfaction: 3.7,
    highRiskEmployees: 8,
    retentionRate: 87,
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Mock data for charts
  const satisfactionData = [
    { month: 'Ene', satisfaction: 3.2 },
    { month: 'Feb', satisfaction: 3.5 },
    { month: 'Mar', satisfaction: 3.1 },
    { month: 'Abr', satisfaction: 3.8 },
    { month: 'May', satisfaction: 4.1 },
    { month: 'Jun', satisfaction: 3.9 },
  ];

  const departmentData = [
    { name: 'Tecnología', value: 35, color: '#5AE386' },
    { name: 'Ventas', value: 25, color: '#FF6B6B' },
    { name: 'Marketing', value: 20, color: '#4ECDC4' },
    { name: 'RRHH', value: 12, color: '#45B7D1' },
    { name: 'Otros', value: 8, color: '#96CEB4' },
  ];

  const riskData = [
    { category: 'Bajo Riesgo', count: 45 },
    { category: 'Riesgo Medio', count: 23 },
    { category: 'Alto Riesgo', count: 12 },
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #000000 0%, #111111 100%)' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
            I.A PRIORI - Dashboard
          </Typography>
          <Typography variant="body2" sx={{ mr: 2 }}>
            {user?.full_name || user?.email}
          </Typography>
          <IconButton color="inherit" onClick={handleLogout}>
            <LogoutOutlined />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        {/* Stats Cards */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #5AE386 0%, #3FC26B 100%)' }}>
              <CardContent>
                <Typography variant="h4" component="div" sx={{ color: 'black', fontWeight: 700 }}>
                  {stats.totalInterviews}
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(0,0,0,0.7)' }}>
                  Entrevistas Totales
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%)' }}>
              <CardContent>
                <Typography variant="h4" component="div" sx={{ color: 'white', fontWeight: 700 }}>
                  {stats.averageSatisfaction.toFixed(1)}
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                  Satisfacción Promedio
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #FF6B6B 0%, #E55555 100%)' }}>
              <CardContent>
                <Typography variant="h4" component="div" sx={{ color: 'white', fontWeight: 700 }}>
                  {stats.highRiskEmployees}
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                  Empleados Alto Riesgo
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} sm={6} md={3}>
            <Card sx={{ background: 'linear-gradient(135deg, #45B7D1 0%, #2E86AB 100%)' }}>
              <CardContent>
                <Typography variant="h4" component="div" sx={{ color: 'white', fontWeight: 700 }}>
                  {stats.retentionRate}%
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(255,255,255,0.8)' }}>
                  Tasa de Retención
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Charts */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Tendencia de Satisfacción
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={satisfactionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis domain={[1, 5]} />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="satisfaction" 
                      stroke="#5AE386" 
                      strokeWidth={3}
                      dot={{ fill: '#5AE386', strokeWidth: 2, r: 6 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            <Card sx={{ height: 400 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Distribución por Departamento
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={departmentData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {departmentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Distribución de Riesgo de Rotación
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={riskData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#5AE386" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Action Buttons */}
        <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/interviews')}
            sx={{
              background: 'linear-gradient(135deg, #5AE386 0%, #3FC26B 100%)',
              '&:hover': {
                background: 'linear-gradient(135deg, #7FEB9F 0%, #5AE386 100%)',
              },
            }}
          >
            Ver Entrevistas
          </Button>
        </Box>
      </Container>
    </Box>
  );
};

export default DashboardPage; 