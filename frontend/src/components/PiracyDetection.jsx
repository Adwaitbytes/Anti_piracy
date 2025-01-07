import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  LinearProgress,
} from '@mui/material';
import { Search, Warning, CheckCircle } from '@mui/icons-material';

const PiracyDetection = () => {
  const [url, setUrl] = useState('');
  const [scanning, setScanning] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [activeScans, setActiveScans] = useState([]);

  useEffect(() => {
    // Poll for active scan updates
    const interval = setInterval(fetchActiveScanUpdates, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchActiveScanUpdates = async () => {
    try {
      const response = await fetch('/api/v1/detect/active-scans');
      const data = await response.json();
      setActiveScans(data);
    } catch (err) {
      console.error('Failed to fetch scan updates:', err);
    }
  };

  const handleScan = async () => {
    setScanning(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/detect/piracy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content_url: url,
          detection_type: 'full',
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to initiate scan');
      }

      const result = await response.json();
      setResults((prev) => [result, ...prev]);
    } catch (err) {
      setError(err.message);
    } finally {
      setScanning(false);
    }
  };

  const renderConfidenceChip = (confidence) => {
    let color = 'success';
    if (confidence > 0.7) color = 'error';
    else if (confidence > 0.4) color = 'warning';

    return (
      <Chip
        label={`${(confidence * 100).toFixed(1)}%`}
        color={color}
        size="small"
      />
    );
  };

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Scan Input */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Content Scan
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                label="Content URL or Platform Link"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                disabled={scanning}
              />
              <Button
                variant="contained"
                startIcon={scanning ? <CircularProgress size={20} /> : <Search />}
                onClick={handleScan}
                disabled={scanning || !url}
              >
                Scan
              </Button>
            </Box>
          </Paper>
        </Grid>

        {/* Active Scans */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Active Scans
            </Typography>
            {activeScans.length === 0 ? (
              <Typography color="textSecondary">No active scans</Typography>
            ) : (
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>URL</TableCell>
                      <TableCell>Progress</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {activeScans.map((scan) => (
                      <TableRow key={scan.id}>
                        <TableCell>{scan.url}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            <Box sx={{ width: '100%', mr: 1 }}>
                              <LinearProgress
                                variant="determinate"
                                value={scan.progress}
                              />
                            </Box>
                            <Box sx={{ minWidth: 35 }}>
                              <Typography variant="body2" color="textSecondary">
                                {`${Math.round(scan.progress)}%`}
                              </Typography>
                            </Box>
                          </Box>
                        </TableCell>
                        <TableCell>{scan.status}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>
        </Grid>

        {/* Scan Results */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Detection Results
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Status</TableCell>
                    <TableCell>Confidence</TableCell>
                    <TableCell>Details</TableCell>
                    <TableCell>Timestamp</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {results.map((result, index) => (
                    <TableRow key={index}>
                      <TableCell>
                        {result.is_pirated ? (
                          <Chip
                            icon={<Warning />}
                            label="Violation Detected"
                            color="error"
                            size="small"
                          />
                        ) : (
                          <Chip
                            icon={<CheckCircle />}
                            label="No Violation"
                            color="success"
                            size="small"
                          />
                        )}
                      </TableCell>
                      <TableCell>
                        {renderConfidenceChip(result.confidence)}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {result.details.frame_results.length} frames analyzed
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {result.details.analysis_type} analysis
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {new Date(result.timestamp).toLocaleString()}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default PiracyDetection;
