import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  AppBar,
  Toolbar,
  IconButton,
  Button,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { ArrowBack, Visibility } from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const InterviewsPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [interviews, setInterviews] = useState([]);
  const [selectedInterview, setSelectedInterview] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Mock data for interviews
  const mockInterviews = [
    {
      id: 1,
      employee_name: 'Juan Pérez',
      department: 'Tecnología',
      date: '2024-01-15',
      satisfaction_score: 3.5,
      retention_risk: 'Medium',
      sentiment: 'Neutral',
      status: 'Completed',
    },
    {
      id: 2,
      employee_name: 'María García',
      department: 'Ventas',
      date: '2024-01-14',
      satisfaction_score: 4.2,
      retention_risk: 'Low',
      sentiment: 'Positive',
      status: 'Completed',
    },
    {
      id: 3,
      employee_name: 'Carlos López',
      department: 'Marketing',
      date: '2024-01-13',
      satisfaction_score: 2.1,
      retention_risk: 'High',
      sentiment: 'Negative',
      status: 'Completed',
    },
  ];

  useEffect(() => {
    setInterviews(mockInterviews);
  }, []);

  const handleViewInterview = (interview) => {
    setSelectedInterview(interview);
    setDialogOpen(true);
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'High': return 'error';
      case 'Medium': return 'warning';
      case 'Low': return 'success';
      default: return 'default';
    }
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment) {
      case 'Positive': return 'success';
      case 'Neutral': return 'default';
      case 'Negative': return 'error';
      default: return 'default';
    }
  };

  const columns = [
    { field: 'id', headerName: 'ID', width: 70 },
    { field: 'employee_name', headerName: 'Empleado', width: 150 },
    { field: 'department', headerName: 'Departamento', width: 130 },
    { field: 'date', headerName: 'Fecha', width: 120 },
    { 
      field: 'satisfaction_score', 
      headerName: 'Satisfacción', 
      width: 120,
      renderCell: (params) => (
        <Typography variant="body2" fontWeight="bold">
          {params.value.toFixed(1)}/5.0
        </Typography>
      ),
    },
    {
      field: 'retention_risk',
      headerName: 'Riesgo',
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          color={getRiskColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'sentiment',
      headerName: 'Sentimiento',
      width: 120,
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          color={getSentimentColor(params.value)}
          size="small"
        />
      ),
    },
    {
      field: 'actions',
      headerName: 'Acciones',
      width: 120,
      renderCell: (params) => (
        <IconButton 
          onClick={() => handleViewInterview(params.row)}
          color="primary"
        >
          <Visibility />
        </IconButton>
      ),
    },
  ];

  return (
    <Box sx={{ flexGrow: 1 }}>
      <AppBar position="static" sx={{ background: 'linear-gradient(135deg, #000000 0%, #111111 100%)' }}>
        <Toolbar>
          <IconButton 
            edge="start" 
            color="inherit" 
            onClick={() => navigate('/dashboard')}
            sx={{ mr: 2 }}
          >
            <ArrowBack />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700 }}>
            Entrevistas de Salida
          </Typography>
          <Typography variant="body2">
            {user?.full_name || user?.email}
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Lista de Entrevistas
            </Typography>
            <Box sx={{ height: 400, width: '100%' }}>
              <DataGrid
                rows={interviews}
                columns={columns}
                pageSize={5}
                rowsPerPageOptions={[5]}
                disableSelectionOnClick
                sx={{
                  '& .MuiDataGrid-root': {
                    border: 'none',
                  },
                  '& .MuiDataGrid-cell': {
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                  },
                  '& .MuiDataGrid-columnHeaders': {
                    backgroundColor: 'rgba(90, 227, 134, 0.1)',
                    borderBottom: '1px solid rgba(90, 227, 134, 0.3)',
                  },
                }}
              />
            </Box>
          </CardContent>
        </Card>
      </Container>

      {/* Interview Details Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Detalles de la Entrevista - {selectedInterview?.employee_name}
        </DialogTitle>
        <DialogContent>
          {selectedInterview && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                Información General
              </Typography>
              <Typography><strong>Empleado:</strong> {selectedInterview.employee_name}</Typography>
              <Typography><strong>Departamento:</strong> {selectedInterview.department}</Typography>
              <Typography><strong>Fecha:</strong> {selectedInterview.date}</Typography>
              <Typography><strong>Satisfacción:</strong> {selectedInterview.satisfaction_score}/5.0</Typography>
              
              <Box sx={{ mt: 2, mb: 2 }}>
                <Chip 
                  label={`Riesgo: ${selectedInterview.retention_risk}`} 
                  color={getRiskColor(selectedInterview.retention_risk)}
                  sx={{ mr: 1 }}
                />
                <Chip 
                  label={`Sentimiento: ${selectedInterview.sentiment}`} 
                  color={getSentimentColor(selectedInterview.sentiment)}
                />
              </Box>

              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Resumen del Análisis
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Esta entrevista muestra un nivel de satisfacción de {selectedInterview.satisfaction_score}/5.0 
                con un riesgo de retención {selectedInterview.retention_risk.toLowerCase()}. 
                El análisis de sentimiento indica una percepción {selectedInterview.sentiment.toLowerCase()} 
                por parte del empleado.
              </Typography>

              <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                Recomendaciones
              </Typography>
              <Typography variant="body2" color="text.secondary">
                • Seguimiento personalizado en las próximas semanas<br/>
                • Revisión de las condiciones de trabajo específicas<br/>
                • Implementación de mejoras basadas en el feedback recibido
              </Typography>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>
            Cerrar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default InterviewsPage; 