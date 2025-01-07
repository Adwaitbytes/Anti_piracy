import React, { useState } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  CircularProgress,
  Alert,
  Paper,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
} from '@mui/material';
import { CloudUpload } from '@mui/icons-material';

const ContentRegistration = ({ onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    owner: '',
    description: '',
    content_type: 'video',
    rights: {},
  });
  const [selectedFile, setSelectedFile] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const formDataToSend = new FormData();
      formDataToSend.append('file', selectedFile);
      formDataToSend.append(
        'registration',
        JSON.stringify({
          title: formData.title,
          owner: formData.owner,
          description: formData.description,
          content_type: formData.content_type,
          rights: {
            distribution: 'restricted',
            reproduction: 'prohibited',
            modification: 'prohibited',
          },
        })
      );

      const response = await fetch('/api/v1/content/register', {
        method: 'POST',
        body: formDataToSend,
      });

      if (!response.ok) {
        throw new Error('Failed to register content');
      }

      const result = await response.json();
      setSuccess(true);
      onSuccess?.();

      // Reset form
      setFormData({
        title: '',
        owner: '',
        description: '',
        content_type: 'video',
        rights: {},
      });
      setSelectedFile(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} noValidate>
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          Content successfully registered and protected!
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <TextField
            required
            fullWidth
            label="Content Title"
            name="title"
            value={formData.title}
            onChange={handleInputChange}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <TextField
            required
            fullWidth
            label="Content Owner"
            name="owner"
            value={formData.owner}
            onChange={handleInputChange}
          />
        </Grid>
        <Grid item xs={12}>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Description"
            name="description"
            value={formData.description}
            onChange={handleInputChange}
          />
        </Grid>
        <Grid item xs={12} md={6}>
          <FormControl fullWidth>
            <InputLabel>Content Type</InputLabel>
            <Select
              value={formData.content_type}
              label="Content Type"
              name="content_type"
              onChange={handleInputChange}
            >
              <MenuItem value="video">Video</MenuItem>
              <MenuItem value="audio">Audio</MenuItem>
              <MenuItem value="image">Image</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12}>
          <Paper
            sx={{
              p: 2,
              border: '2px dashed #ccc',
              textAlign: 'center',
              cursor: 'pointer',
            }}
            onClick={() => document.getElementById('file-input').click()}
          >
            <input
              type="file"
              id="file-input"
              style={{ display: 'none' }}
              onChange={handleFileSelect}
              accept=".mp4,.mp3,.jpg,.png"
            />
            <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="h6" gutterBottom>
              Upload Content
            </Typography>
            <Typography variant="body2" color="textSecondary">
              {selectedFile
                ? `Selected: ${selectedFile.name}`
                : 'Click or drag file to upload'}
            </Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          type="submit"
          variant="contained"
          disabled={loading || !selectedFile}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          Register & Protect Content
        </Button>
      </Box>
    </Box>
  );
};

export default ContentRegistration;
