"""
WebSocket support for real-time updates in Aker Property Model GUI.

This module provides WebSocket functionality for real-time data updates
across all dashboard components.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.subscriptions: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)

        # Initialize subscriptions for this client
        self.subscriptions[client_id] = set()
        self.subscriptions[client_id].add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)

        # Remove from all subscription groups
        for client_connections in self.subscriptions.values():
            client_connections.discard(websocket)

    async def subscribe(self, client_id: str, websocket: WebSocket, topic: str):
        """Subscribe a client to a specific topic."""
        if client_id not in self.subscriptions:
            self.subscriptions[client_id] = set()

        self.subscriptions[client_id].add(websocket)

        # Also subscribe to the topic for broadcasting
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(websocket)

    async def unsubscribe(self, client_id: str, websocket: WebSocket, topic: str):
        """Unsubscribe a client from a specific topic."""
        if client_id in self.subscriptions:
            self.subscriptions[client_id].discard(websocket)

        if topic in self.subscriptions:
            self.subscriptions[topic].discard(websocket)

    async def broadcast(self, topic: str, message: Any):
        """Broadcast a message to all subscribers of a topic."""
        if topic in self.subscriptions:
            disconnected_connections = set()

            for connection in self.subscriptions[topic].copy():
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected_connections.add(connection)

            # Remove disconnected connections
            for connection in disconnected_connections:
                self.disconnect(connection)

    async def send_personal_message(self, client_id: str, message: Any):
        """Send a message to a specific client."""
        if client_id in self.subscriptions:
            disconnected_connections = set()

            for connection in self.subscriptions[client_id].copy():
                try:
                    await connection.send_json(message)
                except WebSocketDisconnect:
                    disconnected_connections.add(connection)

            # Remove disconnected connections
            for connection in disconnected_connections:
                self.disconnect(connection)


class WebSocketManager:
    """High-level WebSocket manager for the GUI application."""

    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.background_tasks = set()

    async def handle_websocket(self, websocket: WebSocket, client_id: str):
        """Handle a WebSocket connection."""
        await self.connection_manager.connect(websocket, client_id)

        try:
            while True:
                data = await websocket.receive_text()

                # Handle subscription requests
                try:
                    message = json.loads(data)
                    if message.get("type") == "subscribe":
                        topic = message.get("topic")
                        if topic:
                            await self.connection_manager.subscribe(client_id, websocket, topic)
                    elif message.get("type") == "unsubscribe":
                        topic = message.get("topic")
                        if topic:
                            await self.connection_manager.unsubscribe(client_id, websocket, topic)

                except json.JSONDecodeError:
                    # Invalid JSON, ignore
                    pass

        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)

    async def broadcast_data_update(self, topic: str, data: Any):
        """Broadcast data updates to subscribers."""
        message = {
            "type": "data_update",
            "topic": topic,
            "data": data,
            "timestamp": asyncio.get_event_loop().time(),
        }
        await self.connection_manager.broadcast(topic, message)

    async def broadcast_market_update(self, msa_id: str, data: Any):
        """Broadcast market data updates."""
        topic = f"market:{msa_id}"
        await self.broadcast_data_update(topic, data)

    async def broadcast_asset_update(self, asset_id: str, data: Any):
        """Broadcast asset data updates."""
        topic = f"asset:{asset_id}"
        await self.broadcast_asset_update(asset_id, data)

    async def broadcast_portfolio_update(self, data: Any):
        """Broadcast portfolio data updates."""
        topic = "portfolio"
        await self.broadcast_data_update(topic, data)

    async def broadcast_system_update(self, data: Any):
        """Broadcast system-wide updates."""
        topic = "system"
        await self.broadcast_data_update(topic, data)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.connection_manager.active_connections)

    def get_subscription_count(self, topic: str) -> int:
        """Get the number of subscribers for a topic."""
        return len(self.subscriptions.get(topic, set()))


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


def create_websocket_endpoint(client_id: str):
    """Create a WebSocket endpoint function."""
    async def websocket_endpoint(websocket: WebSocket):
        await websocket_manager.handle_websocket(websocket, client_id)
    return websocket_endpoint
