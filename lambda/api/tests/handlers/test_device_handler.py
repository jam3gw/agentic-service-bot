import pytest
from unittest.mock import patch, MagicMock
import json
from decimal import Decimal
from handlers.device_handler import handle_get_devices, handle_update_device, CORS_HEADERS

# Test data
MOCK_CUSTOMER_ID = "test-customer-123"
MOCK_DEVICE_ID = "test-device-456"

@pytest.fixture
def mock_dynamodb_service():
    with patch('handlers.device_handler.dynamodb_service') as mock_service:
        yield mock_service

@pytest.fixture
def mock_audio_device():
    return {
        'id': MOCK_DEVICE_ID,
        'type': 'speaker',
        'power': 'on',
        'volume': Decimal('50'),
        'currentSongIndex': Decimal('0'),
        'playlist': [
            "Let's Get It Started - The Black Eyed Peas",
            "Imagine - John Lennon",
            "Don't Stop Believin' - Journey",
            "Sweet Caroline - Neil Diamond",
            "I Wanna Dance with Somebody - Whitney Houston",
            "Walking on Sunshine - Katrina & The Waves",
            "Happy - Pharrell Williams",
            "Uptown Funk - Mark Ronson ft. Bruno Mars",
            "Can't Stop the Feeling! - Justin Timberlake",
            "Good Vibrations - The Beach Boys",
            "Three Little Birds - Bob Marley & The Wailers"
        ],
        'currentSong': "Let's Get It Started - The Black Eyed Peas"
    }

@pytest.fixture
def mock_customer_with_device(mock_audio_device):
    return {
        'id': MOCK_CUSTOMER_ID,
        'name': 'Test Customer',
        'device': mock_audio_device
    }

class TestHandleGetDevices:
    def test_missing_customer_id(self):
        """Test handling of missing customer ID."""
        response = handle_get_devices("", CORS_HEADERS)
        
        assert response['statusCode'] == 400
        assert 'error' in json.loads(response['body'])
        assert 'Missing required parameter' in json.loads(response['body'])['error']

    def test_customer_not_found(self, mock_dynamodb_service):
        """Test handling of non-existent customer."""
        mock_dynamodb_service.get_customer.return_value = None
        
        response = handle_get_devices(MOCK_CUSTOMER_ID, CORS_HEADERS)
        
        assert response['statusCode'] == 404
        assert 'error' in json.loads(response['body'])
        assert 'not found' in json.loads(response['body'])['error']
        mock_dynamodb_service.get_customer.assert_called_once_with(MOCK_CUSTOMER_ID)

    def test_decimal_handling(self, mock_dynamodb_service, mock_customer_with_device):
        """Test proper handling of Decimal types from DynamoDB."""
        mock_customer_with_device['device']['currentSongIndex'] = Decimal('1')
        mock_customer_with_device['device']['volume'] = Decimal('75')
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        
        response = handle_get_devices(MOCK_CUSTOMER_ID, CORS_HEADERS)
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        device = response_body['devices'][0]
        
        assert device['currentSongIndex'] == 1
        assert device['volume'] == '75'
        assert device['currentSong'] == 'Imagine - John Lennon'

    def test_successful_get_audio_device(self, mock_dynamodb_service, mock_customer_with_device):
        """Test successful retrieval of an audio device."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        
        response = handle_get_devices(MOCK_CUSTOMER_ID, CORS_HEADERS)
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert 'devices' in response_body
        devices = response_body['devices']
        assert len(devices) == 1
        
        device = devices[0]
        assert device['id'] == MOCK_DEVICE_ID
        assert device['type'] == 'speaker'
        assert device['power'] == 'on'
        assert device['volume'] == '50'
        assert device['currentSong'] == "Let's Get It Started - The Black Eyed Peas"
        assert device['currentSongIndex'] == 0
        assert len(device['playlist']) == 11
        
        mock_dynamodb_service.get_customer.assert_called_once_with(MOCK_CUSTOMER_ID)

    def test_device_with_power_off(self, mock_dynamodb_service, mock_customer_with_device):
        """Test device retrieval when power is off."""
        mock_customer_with_device['device']['power'] = 'off'
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        
        response = handle_get_devices(MOCK_CUSTOMER_ID, CORS_HEADERS)
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        device = response_body['devices'][0]
        assert device['power'] == 'off'

    def test_customer_without_device(self, mock_dynamodb_service):
        """Test handling of customer without any devices."""
        mock_dynamodb_service.get_customer.return_value = {
            'id': MOCK_CUSTOMER_ID,
            'name': 'Test Customer'
        }
        
        response = handle_get_devices(MOCK_CUSTOMER_ID, CORS_HEADERS)
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['devices'] == []

class TestHandleUpdateDevice:
    def test_missing_parameters(self):
        """Test handling of missing customer or device ID."""
        response = handle_update_device("", MOCK_DEVICE_ID, {}, CORS_HEADERS)
        assert response['statusCode'] == 400
        
        response = handle_update_device(MOCK_CUSTOMER_ID, "", {}, CORS_HEADERS)
        assert response['statusCode'] == 400

    def test_device_not_found(self, mock_dynamodb_service):
        """Test handling of non-existent device."""
        mock_dynamodb_service.get_customer.return_value = None
        
        response = handle_update_device(MOCK_CUSTOMER_ID, MOCK_DEVICE_ID, {'power': 'on'}, CORS_HEADERS)
        
        assert response['statusCode'] == 404
        assert 'error' in json.loads(response['body'])
        assert 'not found' in json.loads(response['body'])['error']

    def test_update_power_state(self, mock_dynamodb_service, mock_customer_with_device):
        """Test updating device power state."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = {
            **mock_customer_with_device['device'],
            'power': 'off'
        }
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'power': 'off'},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['device']['power'] == 'off'
        
        mock_dynamodb_service.update_device_state.assert_called_once()
        call_args = mock_dynamodb_service.update_device_state.call_args[0]
        assert call_args[0] == MOCK_CUSTOMER_ID
        assert call_args[1] == MOCK_DEVICE_ID
        assert call_args[2]['power'] == 'off'

    def test_update_volume(self, mock_dynamodb_service, mock_customer_with_device):
        """Test updating device volume."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = {
            **mock_customer_with_device['device'],
            'volume': '75'
        }
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'volume': '75'},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['device']['volume'] == '75'

    def test_update_song_next(self, mock_dynamodb_service, mock_customer_with_device):
        """Test changing to next song."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = {
            **mock_customer_with_device['device'],
            'currentSongIndex': 1,
            'currentSong': 'Imagine - John Lennon'
        }
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'songAction': 'next'},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['device']['currentSong'] == 'Imagine - John Lennon'
        assert response_body['device']['currentSongIndex'] == 1

    def test_update_song_previous(self, mock_dynamodb_service, mock_customer_with_device):
        """Test changing to previous song."""
        mock_customer_with_device['device']['currentSongIndex'] = 1
        mock_customer_with_device['device']['currentSong'] = 'Imagine - John Lennon'
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = {
            **mock_customer_with_device['device'],
            'currentSongIndex': 0,
            'currentSong': "Let's Get It Started - The Black Eyed Peas"
        }
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'songAction': 'previous'},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['device']['currentSong'] == "Let's Get It Started - The Black Eyed Peas"
        assert response_body['device']['currentSongIndex'] == 0

    def test_update_song_specific(self, mock_dynamodb_service, mock_customer_with_device):
        """Test changing to a specific song by index."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = {
            **mock_customer_with_device['device'],
            'currentSongIndex': 2,
            'currentSong': "Don't Stop Believin' - Journey"
        }
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'songAction': 'specific', 'songIndex': 2},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        assert response_body['device']['currentSong'] == "Don't Stop Believin' - Journey"
        assert response_body['device']['currentSongIndex'] == 2

    def test_invalid_song_index(self, mock_dynamodb_service, mock_customer_with_device):
        """Test handling of invalid song index."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'songAction': 'specific', 'songIndex': 99},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 400
        assert 'error' in json.loads(response['body'])
        assert 'Invalid song index' in json.loads(response['body'])['error']

    def test_no_updates_provided(self, mock_dynamodb_service, mock_customer_with_device):
        """Test handling when no valid updates are provided."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 400
        assert 'error' in json.loads(response['body'])
        assert 'No valid updates provided' in json.loads(response['body'])['error']

    def test_update_failure(self, mock_dynamodb_service, mock_customer_with_device):
        """Test handling of update failure."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = None
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'power': 'off'},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 404
        assert 'error' in json.loads(response['body'])
        assert 'Failed to update device' in json.loads(response['body'])['error']

    def test_decimal_handling_in_updates(self, mock_dynamodb_service, mock_customer_with_device):
        """Test proper handling of Decimal types in device updates."""
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        
        # Create an updated device state with the correct song from the playlist
        updated_device = {
            **mock_customer_with_device['device'],
            'currentSongIndex': Decimal('2'),
            'volume': Decimal('75'),
            'currentSong': "Don't Stop Believin' - Journey"  # Set the correct song for index 2
        }
        mock_dynamodb_service.update_device_state.return_value = updated_device
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {
                'songAction': 'specific',
                'songIndex': 2,
                'volume': '75'
            },
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        device = response_body['device']
        assert device['currentSongIndex'] == 2
        assert device['volume'] == '75'
        assert device['currentSong'] == "Don't Stop Believin' - Journey"

    def test_update_song_with_decimal_index(self, mock_dynamodb_service, mock_customer_with_device):
        """Test updating song when current index is a Decimal."""
        mock_customer_with_device['device']['currentSongIndex'] = Decimal('1')
        mock_dynamodb_service.get_customer.return_value = mock_customer_with_device
        mock_dynamodb_service.update_device_state.return_value = {
            **mock_customer_with_device['device'],
            'currentSongIndex': Decimal('2'),
            'currentSong': 'Song 3'
        }
        
        response = handle_update_device(
            MOCK_CUSTOMER_ID,
            MOCK_DEVICE_ID,
            {'songAction': 'next'},
            CORS_HEADERS
        )
        
        assert response['statusCode'] == 200
        response_body = json.loads(response['body'])
        device = response_body['device']
        assert device['currentSongIndex'] == 2
        assert device['currentSong'] == 'Song 3'