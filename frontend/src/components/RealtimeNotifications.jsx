import React, { useEffect, useState, useCallback } from 'react';
import {
  Box,
  Snackbar,
  Alert,
  Badge,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Typography,
  Divider,
} from '@mui/material';
import {
  Notifications as NotificationsIcon,
  Warning,
  Info,
  CheckCircle,
} from '@mui/icons-material';

const RealtimeNotifications = () => {
  const [socket, setSocket] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [showSnackbar, setShowSnackbar] = useState(false);
  const [currentNotification, setCurrentNotification] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');

    ws.onopen = () => {
      console.log('WebSocket Connected');
      // Send authentication if needed
      ws.send(JSON.stringify({
        type: 'subscribe',
        event_types: ['violation_detected', 'scan_update', 'system_event']
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleNotification(data);
    };

    ws.onclose = () => {
      console.log('WebSocket Disconnected');
      // Attempt to reconnect after delay
      setTimeout(connectWebSocket, 5000);
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    setSocket(ws);
  }, []);

  useEffect(() => {
    connectWebSocket();
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [connectWebSocket]);

  const handleNotification = (notification) => {
    // Add notification to list
    setNotifications((prev) => [notification, ...prev]);
    setUnreadCount((prev) => prev + 1);

    // Show snackbar for high priority notifications
    if (notification.severity === 'high') {
      setCurrentNotification(notification);
      setShowSnackbar(true);
    }
  };

  const handleSnackbarClose = () => {
    setShowSnackbar(false);
    setCurrentNotification(null);
  };

  const handleDrawerOpen = () => {
    setDrawerOpen(true);
    setUnreadCount(0);
  };

  const handleDrawerClose = () => {
    setDrawerOpen(false);
  };

  const getNotificationIcon = (severity) => {
    switch (severity) {
      case 'high':
        return <Warning color="error" />;
      case 'medium':
        return <Warning color="warning" />;
      case 'low':
        return <Info color="info" />;
      default:
        return <CheckCircle color="success" />;
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  return (
    <>
      <IconButton color="inherit" onClick={handleDrawerOpen}>
        <Badge badgeContent={unreadCount} color="error">
          <NotificationsIcon />
        </Badge>
      </IconButton>

      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={handleDrawerClose}
      >
        <Box sx={{ width: 350, p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Notifications
          </Typography>
          <Divider />
          <List>
            {notifications.map((notification, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  {getNotificationIcon(notification.severity)}
                </ListItemIcon>
                <ListItemText
                  primary={notification.data.title || notification.event_type}
                  secondary={
                    <>
                      <Typography variant="body2" color="textSecondary">
                        {notification.data.message}
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        {formatTimestamp(notification.timestamp)}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      <Snackbar
        open={showSnackbar}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert
          onClose={handleSnackbarClose}
          severity="error"
          sx={{ width: '100%' }}
        >
          {currentNotification?.data.message}
        </Alert>
      </Snackbar>
    </>
  );
};

export default RealtimeNotifications;
