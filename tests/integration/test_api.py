"""Integration tests for FastAPI endpoints."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.mark.integration
class TestRootEndpoint:
    """Test cases for root endpoint."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns healthy status."""
        # Act
        response = client.get("/")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.integration
class TestHealthEndpoint:
    """Test cases for health endpoint."""

    def test_health_endpoint(self, client):
        """Test health endpoint returns healthy status."""
        # Act
        response = client.get("/health")

        # Assert
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.integration
class TestPredictEndpoint:
    """Test cases for predict endpoint."""

    @patch("api.main.predict")
    def test_predict_endpoint_success(self, mock_predict, client):
        """Test successful prediction request."""
        # Arrange
        mock_predict.return_value = None
        params = {
            "env": "dev",
            "input_table": "test-project.dataset.input",
            "output_table": "test-project.dataset.output",
            "model_name": "titanic-survival",
            "model_version": "v1",
        }

        # Act
        response = client.get("/predict", params=params)

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Predictions completed for titanic-survival v1",
        }
        mock_predict.assert_called_once_with(
            env="dev",
            input_table="test-project.dataset.input",
            output_table="test-project.dataset.output",
            model_name="titanic-survival",
            model_version="v1",
        )

    @patch("api.main.predict")
    def test_predict_endpoint_with_different_environments(self, mock_predict, client):
        """Test prediction endpoint with different environments."""
        mock_predict.return_value = None

        # Test dev
        response = client.get(
            "/predict",
            params={
                "env": "dev",
                "input_table": "t.in",
                "output_table": "t.out",
                "model_name": "model",
                "model_version": "v1",
            },
        )
        assert response.status_code == 200

        # Test staging
        response = client.get(
            "/predict",
            params={
                "env": "staging",
                "input_table": "t.in",
                "output_table": "t.out",
                "model_name": "model",
                "model_version": "v1",
            },
        )
        assert response.status_code == 200

        # Test prod
        response = client.get(
            "/predict",
            params={
                "env": "prod",
                "input_table": "t.in",
                "output_table": "t.out",
                "model_name": "model",
                "model_version": "v1",
            },
        )
        assert response.status_code == 200

    def test_predict_endpoint_missing_parameters(self, client):
        """Test that missing required parameters return 422."""
        # Missing all parameters
        response = client.get("/predict")
        assert response.status_code == 422

        # Missing some parameters
        response = client.get("/predict", params={"env": "dev"})
        assert response.status_code == 422

    @patch("api.main.predict")
    def test_predict_endpoint_handles_errors(self, mock_predict, client):
        """Test that prediction errors are handled properly."""
        # Arrange
        mock_predict.side_effect = ValueError("Invalid model")
        params = {
            "env": "dev",
            "input_table": "t.in",
            "output_table": "t.out",
            "model_name": "invalid",
            "model_version": "v1",
        }

        # Act
        response = client.get("/predict", params=params)

        # Assert
        assert response.status_code == 500
        assert "Invalid model" in response.json()["detail"]

    @patch("api.main.predict")
    def test_predict_endpoint_with_different_model_versions(self, mock_predict, client):
        """Test prediction with different model versions."""
        mock_predict.return_value = None

        # Test v1
        response = client.get(
            "/predict",
            params={
                "env": "dev",
                "input_table": "t.in",
                "output_table": "t.out",
                "model_name": "model",
                "model_version": "v1",
            },
        )
        assert response.status_code == 200

        # Test v10
        response = client.get(
            "/predict",
            params={
                "env": "dev",
                "input_table": "t.in",
                "output_table": "t.out",
                "model_name": "model",
                "model_version": "v10",
            },
        )
        assert response.status_code == 200


@pytest.mark.integration
class TestModelRegistryEndpoint:
    """Test cases for model registry endpoint."""

    @patch("api.main.model_registry")
    def test_model_registry_endpoint_success_dev(self, mock_model_registry, client):
        """Test successful model registration in dev."""
        # Arrange
        mock_model_registry.return_value = None

        # Act
        response = client.get("/model-registry", params={"env": "dev"})

        # Assert
        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Models registered for dev environment",
        }
        mock_model_registry.assert_called_once_with(env="dev")

    @patch("api.main.model_registry")
    def test_model_registry_endpoint_success_staging(self, mock_model_registry, client):
        """Test successful model registration in staging."""
        # Arrange
        mock_model_registry.return_value = None

        # Act
        response = client.get("/model-registry", params={"env": "staging"})

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Models registered for staging environment"
        mock_model_registry.assert_called_once_with(env="staging")

    @patch("api.main.model_registry")
    def test_model_registry_endpoint_success_prod(self, mock_model_registry, client):
        """Test successful model registration in prod."""
        # Arrange
        mock_model_registry.return_value = None

        # Act
        response = client.get("/model-registry", params={"env": "prod"})

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == "Models registered for prod environment"
        mock_model_registry.assert_called_once_with(env="prod")

    def test_model_registry_endpoint_missing_env(self, client):
        """Test that missing env parameter returns 422."""
        # Act
        response = client.get("/model-registry")

        # Assert
        assert response.status_code == 422

    @patch("api.main.model_registry")
    def test_model_registry_endpoint_handles_errors(self, mock_model_registry, client):
        """Test that model registry errors are handled properly."""
        # Arrange
        mock_model_registry.side_effect = ValueError("Invalid environment")

        # Act
        response = client.get("/model-registry", params={"env": "invalid"})

        # Assert
        assert response.status_code == 500
        assert "Invalid environment" in response.json()["detail"]

    @patch("api.main.model_registry")
    def test_model_registry_endpoint_handles_runtime_errors(self, mock_model_registry, client):
        """Test that runtime errors are handled properly."""
        # Arrange
        mock_model_registry.side_effect = RuntimeError("BigQuery insert failed")

        # Act
        response = client.get("/model-registry", params={"env": "dev"})

        # Assert
        assert response.status_code == 500
        assert "BigQuery insert failed" in response.json()["detail"]


@pytest.mark.integration
class TestAPIDocumentation:
    """Test cases for API documentation."""

    def test_openapi_schema_available(self, client):
        """Test that OpenAPI schema is available."""
        # Act
        response = client.get("/openapi.json")

        # Assert
        assert response.status_code == 200
        schema = response.json()
        assert schema["info"]["title"] == "mlsys"
        assert "paths" in schema

    def test_docs_endpoint_available(self, client):
        """Test that Swagger UI docs are available."""
        # Act
        response = client.get("/docs")

        # Assert
        assert response.status_code == 200

    def test_redoc_endpoint_available(self, client):
        """Test that ReDoc documentation is available."""
        # Act
        response = client.get("/redoc")

        # Assert
        assert response.status_code == 200
