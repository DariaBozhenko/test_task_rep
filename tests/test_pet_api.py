import os
import random
import string
import time
import logging
import pytest
import requests

BASE_URL = 'https://petstore.swagger.io/v2' # Base URL for the Petstore API
MAX_WAIT_SECONDS = 30  # Max wait time for polling
POLL_INTERVAL = 2     # Polling interval in seconds
TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'core', 'test_data')
file_path = os.path.join(TEST_DATA_DIR, 'premium_photo-1694819488591-a43907d1c5cc.jpeg')

# Module-level logger - initialized once and reused throughout the module
logger = logging.getLogger(__name__)

@pytest.fixture
def create_pet():
    """
    Pytest fixture to create a pet with default or specified attributes.
    Keeps track of created pet IDs for cleanup or reference.
    """
    created_pets = []

    def _create_pet(
            id=None,
            category={ "id": 1, "name": "dog" },
            name="Fluffy",
            photo_urls=["http://img1"],
            tags={ "id": 1, "name": "friendly" },
            status="available"
    ):
        # Prepare pet data, use random ID and name if not provided
        pet_data ={
            "id": random_pet_id() if id is None else id ,
            "category": { "id": 1, "name": "dog" } if category is None else category,
            "name": random_pet_name() if name is None else name ,
            "photoUrls": photo_urls,
            "tags": [tags],
            "status": status
        }
        # Send POST request to add the pet to the store
        response = requests.post(f'{BASE_URL}/pet', json=pet_data)

        # Verify the pet was created successfully (status 200 or 201)
        assert_successful_response(response)

        # Track created pet ID
        created_pets.append(pet_data["id"])
        return pet_data

    yield _create_pet  # Provide the inner function as the fixture output


def random_pet_id():
    """Generate a random pet ID within a specified range."""
    return random.randint(1000000, 9999999)

def random_pet_name():
    """Generate a random pet name consisting of 6 letters."""
    return ''.join(random.choices(string.ascii_letters, k=6))

def assert_successful_response(response, expected_codes=(200, 201)):
    """Helper to assert successful HTTP response."""
    assert response.status_code in expected_codes, \
        f"Expected {expected_codes}, got {response.status_code}"

class TestPetApi:


    def test_post_pet_valid_data(self, create_pet):
        """
        Test creating a pet with valid data.
        Verifies that the pet is created with expected attributes.
        """
        pet = create_pet()
        assert pet["name"] == pet["name"]
        assert pet["id"] == pet["id"]
        logger.info(f"✅ Test passed: Pet added successfully with {pet['id']}")

    def test_post_pet_invalid_data(self):
        """
        Test POST request without required body.
        Expects HTTP 415 Unsupported Media Type response.
        """
        response = requests.post(f'{BASE_URL}/pet')
        assert response.status_code == 415, f"Unexpected status code: {response.status_code}"
        logger.info("✅ Test passed: Proper error code is returned")

    def test_get_pet_valid_pet_id(self, create_pet):
        """
        Test retrieving an existing pet by valid pet ID.
        Polls until the pet is available or timeout is reached.
        """
        pet = create_pet()
        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_SECONDS:
            response_get = requests.get(f'{BASE_URL}/pet/{pet["id"]}')
            if response_get.status_code == 200:
                logger.info(f"Record found: {response_get.json()}")
                break
            time.sleep(POLL_INTERVAL)
        else:
            raise AssertionError(f"Record {pet['id']} was not available within {MAX_WAIT_SECONDS} seconds")

        assert_successful_response(response_get)
        data = response_get.json()
        assert data["id"] == pet["id"]
        assert data["name"] == pet["name"]
        logger.info(f"✅ Test passed: Pet returned successfully with {data['id']}")

    def test_get_pet_invalid_pet_id(self):
        """
        Test retrieving a pet with invalid ID (0).
        Expects HTTP 404 Not Found and a specific error message.
        """
        pet_id = 0
        response = requests.get(f'{BASE_URL}/pet/{pet_id}')
        assert response.status_code == 404, f"Unexpected status code: {response.status_code}"
        data = response.json()
        assert data == {'code': 1, 'type': 'error', 'message': 'Pet not found'}
        logger.info(f"✅ Test passed: Proper error message and code is returned")

    @pytest.mark.parametrize('status', ["available", "sold", "pending"])
    def test_get_pet_by_valid_status(self, status, create_pet):
        """
        Test filtering pets by valid status.
        Verifies that the created pet with the given status is included in the response.
        """
        pet = create_pet(status=status)
        response_get = requests.get(f'{BASE_URL}/pet/findByStatus?status={pet["status"]}')
        assert_successful_response(response_get)
        data = response_get.json()
        for pet_in_response in data:
            if pet_in_response["id"] == pet["id"]:
                assert pet_in_response["id"] == pet["id"]
                assert pet_in_response["name"] == pet["name"]
                assert pet_in_response["status"] == pet["status"]
                logger.info(f"✅ Test passed: Pet returned successfully with {pet_in_response['id']}")

    def test_get_pet_by_invalid_status(self):
        """
        Test filtering pets by invalid status value.
        Expects HTTP 400 Bad Request.
        """
        response_get = requests.get(f'{BASE_URL}/pet/findByStatus?status=unknown')
        assert response_get.status_code == 400, f"Unexpected status code: {response_get.status_code}"


    def test_update_pet_valid_data(self, create_pet):
        """
        Test updating an existing pet with valid data.
        Verifies the updated pet details are returned correctly.
        """
        pet = create_pet()

        updated_pet = {
            "id": pet["id"],
            "category": { "id": 2, "name": "updatedhound" },
            "name": "Rexie",
            "photoUrls": ["http://updatedimg2"],
            "tags": [{ "id": 2, "name": "updatedcute" }],
            "status": "pending"
            }
        response = requests.put(f'{BASE_URL}/pet', json=updated_pet)
        assert_successful_response(response)
        data = response.json()
        assert data == updated_pet


    def test_update_pet_invalid_id(self):
        """
        Test updating a pet with an invalid ID (too large number format).
        Expects HTTP 400 Bad Request.
        """

        payload = ("{\r\n  \"id\": 00012345678900,\r\n  \"category\": {\r\n    \"id\": 2,\r\n    \"name\": "
                   "\"category_updated\"\r\n  },\r\n  \"name\": \"updated_name\",\r\n  \"photoUrls\": [\r\n    "
                   "\"photo_urls_update\"\r\n  ],\r\n  \"tags\": [\r\n    {\r\n      \"id\": 8,\r\n      \"name\": "
                   "\"Updated name\"\r\n    }\r\n  ],\r\n  \"status\": \"sold\"\r\n}")
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("PUT", f"{BASE_URL}/pet", headers=headers, data=payload)

        assert response.status_code == 400, f"Unexpected status code: {response.status_code}"

    def test_update_pet_not_found(self):
        """
        Test updating a pet with ID 0 (non-existent).
        Expects HTTP 404 Not Found.
        """
        payload = {
            "id": 0,
            "category": {
                "id": 0,
                "name": "test category updated"
            },
            "name": "test name updated",
            "photoUrls": [
                "test photo updated"
            ],
            "tags": [
                {
                    "id": 0,
                    "name": "test tag updated"
                }
            ],
            "status": "pending"
        }
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("PUT", f"{BASE_URL}/pet", headers=headers, data=payload)

        assert response.status_code == 404, f"Unexpected status code: {response.status_code}"


    def test_update_pet_and_status_with_form_data(self, create_pet):
        """
        Test updating pet's name and status using form data (x-www-form-urlencoded).
        Verifies correct response and message.
        """
        pet=create_pet()
        response = requests.post(f'{BASE_URL}/pet/{pet["id"]}', data={"name":"12", "status":"12"},
                                 headers={"Content-Type": "application/x-www-form-urlencoded", "accept": "application/json"})
        logger.info(f"Response: {response.json()}")
        assert_successful_response(response)

        data = response.json()
        assert data["message"] == str(pet["id"])

    def test_delete_pet_valid_pet_id(self, create_pet):
        """
        Test deleting a pet with valid pet ID.
        Expects HTTP 200 OK.
        """
        pet = create_pet()
        response = requests.delete(f'{BASE_URL}/pet/{pet["id"]}', headers={"api_key": "special-key"})
        assert_successful_response(response)

    def test_delete_pet_no_apikey(self, create_pet):
        """
        Test deleting a pet without providing API key.
        Expects HTTP 404 Not Found.
        """
        pet = create_pet()
        response = requests.delete(f'{BASE_URL}/pet/{pet["id"]}')
        assert response.status_code == 404, f"Unexpected status code: {response.status_code}"

    def test_upload_image_with_valid_pet_id(self, create_pet):
        """
        Test uploading an image for a valid pet ID.
        Verifies HTTP 200 response and non-empty message.
        """
        pet = create_pet()
        url=f'{BASE_URL}/pet/{pet["id"]}/uploadImage'
        headers = {
            'accept': 'application/json',
        }
        files = {
            'file': ('premium_photo-1694819488591-a43907d1c5cc.jpeg',
                     open(file_path, 'rb'), 'image/jpeg')
        }
        data = {
            'additionalMetadata': '45g43ewf34wef'
        }

        response = requests.post(url, headers=headers, files=files, data=data)
        assert_successful_response(response)
        assert response.json()["message"] is not None

    def test_upload_image_with_invalid_pet_id(self):
        """
        Test uploading an image for an invalid pet ID (0).
        Expects HTTP 404 Not Found.
        """
        file_path = os.path.join(TEST_DATA_DIR, 'premium_photo-1694819488591-a43907d1c5cc.jpeg')

        with open(file_path, 'rb') as image_file:
            response = requests.post(
                f'{BASE_URL}/pet/0/uploadImage',
                files={'image': image_file},
                headers={"accept": "application/json"},
                data={"additionalMetadata": "uploadimagemetadata"}
            )
        assert response.status_code == 404, f"Unexpected status code: {response.status_code}"

