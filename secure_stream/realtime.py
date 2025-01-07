from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set, Any, Optional
import json
import asyncio
import logging
from datetime import datetime
from dataclasses import dataclass, asdict

@dataclass
class RealtimeEvent:
    event_type: str
    data: Dict[str, Any]
    timestamp: str
    severity: str = "info"

class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a new client.
        
        Args:
            websocket: WebSocket connection
            client_id: Unique client identifier
        """
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)
        self.logger.info(f"Client {client_id} connected")

    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Disconnect a client.
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        self.logger.info(f"Client {client_id} disconnected")

    async def broadcast(self, event: RealtimeEvent, client_id: Optional[str] = None):
        """
        Broadcast event to connected clients.
        
        Args:
            event: Event to broadcast
            client_id: Optional specific client to send to
        """
        message = json.dumps(asdict(event))
        
        if client_id:
            # Send to specific client
            if client_id in self.active_connections:
                for connection in self.active_connections[client_id]:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        self.logger.error(f"Failed to send to client {client_id}: {str(e)}")
        else:
            # Broadcast to all clients
            for client_connections in self.active_connections.values():
                for connection in client_connections:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        self.logger.error(f"Failed to broadcast message: {str(e)}")

class RealtimeNotificationService:
    """Handles real-time notifications and events."""
    
    def __init__(self):
        self.manager = ConnectionManager()
        self.logger = logging.getLogger(__name__)

    async def handle_violation_event(
        self, violation_data: Dict[str, Any], client_id: Optional[str] = None
    ):
        """Handle content violation event."""
        event = RealtimeEvent(
            event_type="violation_detected",
            data=violation_data,
            timestamp=datetime.utcnow().isoformat(),
            severity="high"
        )
        await self.manager.broadcast(event, client_id)

    async def handle_scan_update(
        self, scan_data: Dict[str, Any], client_id: Optional[str] = None
    ):
        """Handle scan progress update."""
        event = RealtimeEvent(
            event_type="scan_update",
            data=scan_data,
            timestamp=datetime.utcnow().isoformat(),
            severity="info"
        )
        await self.manager.broadcast(event, client_id)

    async def handle_system_event(
        self, event_data: Dict[str, Any], client_id: Optional[str] = None
    ):
        """Handle system-level event."""
        event = RealtimeEvent(
            event_type="system_event",
            data=event_data,
            timestamp=datetime.utcnow().isoformat(),
            severity=event_data.get("severity", "info")
        )
        await self.manager.broadcast(event, client_id)

class WebSocketHandler:
    """Handles WebSocket connections and message routing."""
    
    def __init__(self, notification_service: RealtimeNotificationService):
        self.notification_service = notification_service
        self.logger = logging.getLogger(__name__)

    async def handle_websocket(self, websocket: WebSocket, client_id: str):
        """
        Handle WebSocket connection.
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        await self.notification_service.manager.connect(websocket, client_id)
        
        try:
            while True:
                # Wait for messages from client
                data = await websocket.receive_text()
                try:
                    message = json.loads(data)
                    await self._handle_client_message(message, client_id)
                except json.JSONDecodeError:
                    self.logger.error(f"Invalid message format from client {client_id}")
                except Exception as e:
                    self.logger.error(f"Error handling message: {str(e)}")
                    
        except WebSocketDisconnect:
            self.notification_service.manager.disconnect(websocket, client_id)
        except Exception as e:
            self.logger.error(f"WebSocket error: {str(e)}")
            self.notification_service.manager.disconnect(websocket, client_id)

    async def _handle_client_message(self, message: Dict[str, Any], client_id: str):
        """
        Handle message from client.
        
        Args:
            message: Client message
            client_id: Client identifier
        """
        message_type = message.get("type")
        
        if message_type == "subscribe":
            # Handle subscription request
            await self._handle_subscription(message, client_id)
        elif message_type == "acknowledge":
            # Handle event acknowledgment
            await self._handle_acknowledgment(message, client_id)
        else:
            self.logger.warning(f"Unknown message type: {message_type}")

    async def _handle_subscription(self, message: Dict[str, Any], client_id: str):
        """Handle client subscription request."""
        event_types = message.get("event_types", [])
        # Implementation for subscription logic
        pass

    async def _handle_acknowledgment(self, message: Dict[str, Any], client_id: str):
        """Handle client event acknowledgment."""
        event_id = message.get("event_id")
        # Implementation for acknowledgment logic
        pass
