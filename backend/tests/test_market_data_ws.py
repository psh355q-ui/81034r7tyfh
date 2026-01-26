"""
Tests for Market Data WebSocket Manager

Phase 4 - Real-time Execution
Tests WebSocket connection, subscription, and quote streaming functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from backend.api.market_data_ws import MarketDataWebSocketManager


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.messages = []
        self.accepted = False
        self.closed = False
        
    async def accept(self):
        self.accepted = True
        
    async def send_json(self, data):
        self.messages.append(data)
        
    async def close(self):
        self.closed = True


@pytest.fixture
def ws_manager():
    """Create a fresh WebSocket manager for each test"""
    return MarketDataWebSocketManager()


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket"""
    return MockWebSocket()


@pytest.mark.asyncio
async def test_connect_websocket(ws_manager, mock_websocket):
    """Test WebSocket connection"""
    # Connect
    await ws_manager.connect(mock_websocket)
    
    # Verify
    assert mock_websocket.accepted is True
    assert mock_websocket in ws_manager.active_connections
    assert len(ws_manager.active_connections) == 1


@pytest.mark.asyncio
async def test_disconnect_websocket(ws_manager, mock_websocket):
    """Test WebSocket disconnection"""
    # Connect first
    await ws_manager.connect(mock_websocket)
    
    # Disconnect
    ws_manager.disconnect(mock_websocket)
    
    # Verify
    assert mock_websocket not in ws_manager.active_connections
    assert len(ws_manager.active_connections) == 0


@pytest.mark.asyncio
async def test_subscribe_to_symbols(ws_manager, mock_websocket):
    """Test subscribing to market data symbols"""
    # Connect
    await ws_manager.connect(mock_websocket)
    
    # Subscribe to symbols
    symbols = ['NVDA', 'AAPL', 'TSLA']
    await ws_manager.subscribe(mock_websocket, symbols)
    
    # Verify subscriptions
    subscribed = ws_manager.get_subscribed_symbols(mock_websocket)
    assert len(subscribed) == 3
    assert 'NVDA' in subscribed
    assert 'AAPL' in subscribed
    assert 'TSLA' in subscribed
    
    # Verify streaming tasks started
    assert 'NVDA' in ws_manager.quote_tasks
    assert 'AAPL' in ws_manager.quote_tasks
    assert 'TSLA' in ws_manager.quote_tasks


@pytest.mark.asyncio
async def test_unsubscribe_from_symbols(ws_manager, mock_websocket):
    """Test unsubscribing from symbols"""
    # Connect and subscribe
    await ws_manager.connect(mock_websocket)
    symbols = ['NVDA', 'AAPL', 'TSLA']
    await ws_manager.subscribe(mock_websocket, symbols)
    
    # Unsubscribe from some symbols
    await ws_manager.unsubscribe(mock_websocket, ['AAPL', 'TSLA'])
    
    # Verify
    subscribed = ws_manager.get_subscribed_symbols(mock_websocket)
    assert len(subscribed) == 1
    assert 'NVDA' in subscribed
    assert 'AAPL' not in subscribed
    
    # Streaming tasks should be cancelled for unsubscribed symbols
    assert 'AAPL' not in ws_manager.quote_tasks
    assert 'TSLA' not in ws_manager.quote_tasks


@pytest.mark.asyncio
async def test_multiple_clients(ws_manager):
    """Test handling multiple WebSocket clients"""
    # Create multiple clients
    client1 = MockWebSocket()
    client2 = MockWebSocket()
    client3 = MockWebSocket()
    
    # Connect all clients
    await ws_manager.connect(client1)
    await ws_manager.connect(client2)
    await ws_manager.connect(client3)
    
    # Subscribe to different symbols
    await ws_manager.subscribe(client1, ['NVDA'])
    await ws_manager.subscribe(client2, ['AAPL', 'NVDA'])
    await ws_manager.subscribe(client3, ['TSLA'])
    
    # Verify connection count
    assert ws_manager.get_connection_count() == 3
    
    # Verify all subscribed symbols
    all_symbols = ws_manager.get_all_subscribed_symbols()
    assert len(all_symbols) == 3
    assert 'NVDA' in all_symbols
    assert 'AAPL' in all_symbols
    assert 'TSLA' in all_symbols


@pytest.mark.asyncio
async def test_broadcast_to_subscribers(ws_manager):
    """Test broadcasting messages to subscribers"""
    # Setup multiple clients
    client1 = MockWebSocket()
    client2 = MockWebSocket()
    
    await ws_manager.connect(client1)
    await ws_manager.connect(client2)
    
    # Both subscribe to NVDA
    await ws_manager.subscribe(client1, ['NVDA'])
    await ws_manager.subscribe(client2, ['NVDA'])
    
    # Broadcast a message
    test_message = {
        'type': 'quote',
        'data': {
            'symbol': 'NVDA',
            'price': 500.0,
            'change': 2.5
        }
    }
    
    await ws_manager._broadcast_to_subscribers('NVDA', test_message)
    
    # Verify both clients received the message
    assert len(client1.messages) == 1
    assert len(client2.messages) == 1
    assert client1.messages[0] == test_message
    assert client2.messages[0] == test_message


@pytest.mark.asyncio
async def test_cleanup_on_disconnect(ws_manager, mock_websocket):
    """Test cleanup when client disconnects"""
    # Connect and subscribe
    await ws_manager.connect(mock_websocket)
    await ws_manager.subscribe(mock_websocket, ['NVDA', 'AAPL'])
    
    # Verify tasks are running
    assert 'NVDA' in ws_manager.quote_tasks
    assert 'AAPL' in ws_manager.quote_tasks
    
    # Disconnect
    ws_manager.disconnect(mock_websocket)
    
    # Verify cleanup
    assert mock_websocket not in ws_manager.active_connections
    # Tasks should be cancelled if no other subscribers
    assert 'NVDA' not in ws_manager.quote_tasks
    assert 'AAPL' not in ws_manager.quote_tasks


@pytest.mark.asyncio
async def test_shutdown(ws_manager):
    """Test graceful shutdown"""
    # Setup clients
    client1 = MockWebSocket()
    client2 = MockWebSocket()
    
    await ws_manager.connect(client1)
    await ws_manager.connect(client2)
    await ws_manager.subscribe(client1, ['NVDA'])
    await ws_manager.subscribe(client2, ['AAPL'])
    
    # Shutdown
    await ws_manager.shutdown()
    
    # Verify cleanup
    assert ws_manager.is_running is False
    assert len(ws_manager.active_connections) == 0
    assert len(ws_manager.quote_tasks) == 0
    assert client1.closed is True
    assert client2.closed is True


@pytest.mark.asyncio
async def test_has_subscribers(ws_manager, mock_websocket):
    """Test _has_subscribers helper method"""
    # No subscribers initially
    assert ws_manager._has_subscribers('NVDA') is False
    
    # Connect and subscribe
    await ws_manager.connect(mock_websocket)
    await ws_manager.subscribe(mock_websocket, ['NVDA'])
    
    # Now has subscribers
    assert ws_manager._has_subscribers('NVDA') is True
    assert ws_manager._has_subscribers('AAPL') is False


@pytest.mark.asyncio
async def test_broadcast_all(ws_manager):
    """Test broadcasting to all connected clients"""
    # Setup clients
    client1 = MockWebSocket()
    client2 = MockWebSocket()
    
    await ws_manager.connect(client1)
    await ws_manager.connect(client2)
    
    # Broadcast message to all
    test_message = {'type': 'system', 'message': 'Market closed'}
    await ws_manager.broadcast_all(test_message)
    
    # Verify all clients received it
    assert len(client1.messages) == 1
    assert len(client2.messages) == 1
    assert client1.messages[0] == test_message
    assert client2.messages[0] == test_message


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
