from typing import Dict, List
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for group chats"""
    
    def __init__(self):
        # Dictionary mapping group_id to list of active WebSocket connections
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, group_id: int):
        """Accept a new WebSocket connection and add it to the group"""
        await websocket.accept()
        if group_id not in self.active_connections:
            self.active_connections[group_id] = []
        self.active_connections[group_id].append(websocket)
        logger.info(f"Client connected to group {group_id}. Total connections: {len(self.active_connections[group_id])}")
    
    def disconnect(self, websocket: WebSocket, group_id: int):
        """Remove a WebSocket connection from the group"""
        if group_id in self.active_connections:
            self.active_connections[group_id].remove(websocket)
            logger.info(f"Client disconnected from group {group_id}. Remaining connections: {len(self.active_connections[group_id])}")
            # Clean up empty group lists
            if not self.active_connections[group_id]:
                del self.active_connections[group_id]
    
    async def broadcast_to_group(self, group_id: int, message: dict):
        """Send a message to all connected clients in a group"""
        if group_id in self.active_connections:
            # Create a copy of the list to avoid modification during iteration
            connections = self.active_connections[group_id].copy()
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    # Remove dead connections
                    self.disconnect(connection, group_id)


# Global connection manager instance
manager = ConnectionManager()
