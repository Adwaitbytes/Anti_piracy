import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Grid,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import { UploadFile, Security, History, Analytics } from '@mui/icons-material';
import ContentRegistration from './ContentRegistration';
import PiracyDetection from './PiracyDetection';
import ContentHistory from './ContentHistory';
import AnalyticsDashboard from './AnalyticsDashboard';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('register');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({
    totalContent: 0,
    activeMonitoring: 0,
    detectedViolations: 0,
  });

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      setLoading(true);
      // Fetch stats from API
      const response = await fetch('/api/v1/dashboard/stats');
      const data = await response.json();
      setStats(data);
    } catch (err) {
      setError('Failed to load dashboard statistics');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'register':
        return <ContentRegistration onSuccess={fetchDashboardStats} />;
      case 'detect':
        return <PiracyDetection />;
      case 'history':
        return <ContentHistory />;
      case 'analytics':
        return <AnalyticsDashboard />;
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Stats Overview */}
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
            }}
          >
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Protected Content
            </Typography>
            <Typography component="p" variant="h4">
              {loading ? <CircularProgress size={20} /> : stats.totalContent}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
            }}
          >
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Active Monitoring
            </Typography>
            <Typography component="p" variant="h4">
              {loading ? <CircularProgress size={20} /> : stats.activeMonitoring}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              height: 140,
            }}
          >
            <Typography component="h2" variant="h6" color="primary" gutterBottom>
              Detected Violations
            </Typography>
            <Typography component="p" variant="h4">
              {loading ? <CircularProgress size={20} /> : stats.detectedViolations}
            </Typography>
          </Paper>
        </Grid>

        {/* Navigation */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2, display: 'flex', gap: 2 }}>
            <Button
              variant={activeTab === 'register' ? 'contained' : 'outlined'}
              startIcon={<UploadFile />}
              onClick={() => setActiveTab('register')}
            >
              Register Content
            </Button>
            <Button
              variant={activeTab === 'detect' ? 'contained' : 'outlined'}
              startIcon={<Security />}
              onClick={() => setActiveTab('detect')}
            >
              Piracy Detection
            </Button>
            <Button
              variant={activeTab === 'history' ? 'contained' : 'outlined'}
              startIcon={<History />}
              onClick={() => setActiveTab('history')}
            >
              Content History
            </Button>
            <Button
              variant={activeTab === 'analytics' ? 'contained' : 'outlined'}
              startIcon={<Analytics />}
              onClick={() => setActiveTab('analytics')}
            >
              Analytics
            </Button>
          </Paper>
        </Grid>

        {/* Main Content */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>{renderContent()}</Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;
