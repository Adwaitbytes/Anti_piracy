import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
} from '@mui/material';
import {
  Visibility,
  Download,
  Security,
  Warning,
  CheckCircle,
  History as HistoryIcon,
} from '@mui/icons-material';

const ContentHistory = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [contents, setContents] = useState([]);
  const [selectedContent, setSelectedContent] = useState(null);
  const [historyDialog, setHistoryDialog] = useState(false);
  const [contentHistory, setContentHistory] = useState([]);

  useEffect(() => {
    fetchContents();
  }, []);

  const fetchContents = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/content/list');
      if (!response.ok) {
        throw new Error('Failed to fetch content list');
      }
      const data = await response.json();
      setContents(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchContentHistory = async (contentId) => {
    try {
      const response = await fetch(`/api/v1/content/${contentId}/history`);
      if (!response.ok) {
        throw new Error('Failed to fetch content history');
      }
      const data = await response.json();
      setContentHistory(data);
      setHistoryDialog(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleExport = async (contentId) => {
    try {
      const response = await fetch(`/api/v1/content/${contentId}/export`);
      if (!response.ok) {
        throw new Error('Failed to export content data');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `content-${contentId}-report.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message);
    }
  };

  const renderProtectionStatus = (status) => {
    switch (status) {
      case 'protected':
        return (
          <Chip
            icon={<Security />}
            label="Protected"
            color="success"
            size="small"
          />
        );
      case 'violated':
        return (
          <Chip
            icon={<Warning />}
            label="Violation Detected"
            color="error"
            size="small"
          />
        );
      default:
        return (
          <Chip
            icon={<CheckCircle />}
            label="Registered"
            color="primary"
            size="small"
          />
        );
    }
  };

  const renderHistoryTimeline = () => (
    <Timeline>
      {contentHistory.map((event, index) => (
        <TimelineItem key={index}>
          <TimelineSeparator>
            <TimelineDot color={event.type === 'violation' ? 'error' : 'primary'} />
            {index < contentHistory.length - 1 && <TimelineConnector />}
          </TimelineSeparator>
          <TimelineContent>
            <Typography variant="h6" component="span">
              {event.action}
            </Typography>
            <Typography color="textSecondary">
              {new Date(event.timestamp).toLocaleString()}
            </Typography>
            <Typography>{event.details}</Typography>
            {event.platform && (
              <Chip
                label={event.platform}
                size="small"
                sx={{ mt: 1 }}
              />
            )}
          </TimelineContent>
        </TimelineItem>
      ))}
    </Timeline>
  );

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Protected Content History
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Title</TableCell>
                    <TableCell>Type</TableCell>
                    <TableCell>Owner</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Registration Date</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {contents.map((content) => (
                    <TableRow key={content.id}>
                      <TableCell>{content.title}</TableCell>
                      <TableCell>
                        <Chip label={content.content_type} size="small" />
                      </TableCell>
                      <TableCell>{content.owner}</TableCell>
                      <TableCell>
                        {renderProtectionStatus(content.status)}
                      </TableCell>
                      <TableCell>
                        {new Date(content.registration_date).toLocaleDateString()}
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => fetchContentHistory(content.id)}
                          title="View History"
                        >
                          <HistoryIcon />
                        </IconButton>
                        <IconButton
                          size="small"
                          onClick={() => handleExport(content.id)}
                          title="Export Report"
                        >
                          <Download />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>
        </Grid>
      </Grid>

      {/* History Dialog */}
      <Dialog
        open={historyDialog}
        onClose={() => setHistoryDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Content History</DialogTitle>
        <DialogContent>
          {renderHistoryTimeline()}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialog(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => handleExport(selectedContent?.id)}
          >
            Export Report
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ContentHistory;
