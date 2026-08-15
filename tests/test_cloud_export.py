import pytest
from unittest.mock import patch, MagicMock
from google.auth.exceptions import DefaultCredentialsError
from google.api_core.exceptions import GoogleAPICallError
import json

from app.cloud.gcp_exporter import GCPExporter
from app.models.simulation import SimulationRun
from app.models.enums import SimulationStatus


@pytest.fixture
def sample_run():
    return SimulationRun(
        org_id="org-123",
        scenario_id="scenario-123",
        rng_seed=42,
        status=SimulationStatus.COMPLETED,
        start_time=0.0,
        end_time=12.0,
        total_downtime_hours=5.0,
        final_resilience_score=85.0,
        schema_version="1.0",
        state_snapshot_json='{"services": []}',
        event_ledger_json='[]'
    )


def test_gcs_export_success(sample_run):
    """Test successful GCS export."""
    exporter = GCPExporter("test-bucket")
    
    with patch("app.cloud.gcp_exporter.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        
        result = exporter.export_simulation_run(sample_run)
        
        assert result is True
        mock_client.assert_called_once()
        mock_bucket.blob.assert_called_once_with(f"runs/{sample_run.id}.json")
        
        # Verify the payload structure
        call_args = mock_blob.upload_from_string.call_args[0]
        payload = json.loads(call_args[0])
        assert payload["id"] == sample_run.id
        assert payload["schema_version"] == "1.0"
        assert payload["org_id"] == "org-123"


def test_gcs_export_auth_failure(sample_run):
    """Test graceful handling of missing ADC."""
    exporter = GCPExporter("test-bucket")
    
    with patch("app.cloud.gcp_exporter.storage.Client") as mock_client:
        mock_client.side_effect = DefaultCredentialsError("No credentials")
        
        result = exporter.export_simulation_run(sample_run)
        
        assert result is False


def test_gcs_export_api_failure(sample_run):
    """Test graceful handling of network/API errors."""
    exporter = GCPExporter("test-bucket")
    
    with patch("app.cloud.gcp_exporter.storage.Client") as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client.return_value.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.upload_from_string.side_effect = GoogleAPICallError("Network timeout")
        
        result = exporter.export_simulation_run(sample_run)
        
        assert result is False


@patch("app.ui.state_manager.st")
@patch("app.ui.state_manager.SimulationRunRepository")
@patch("app.ui.state_manager.GCPExporter")
def test_sqlite_persistence_resilience(mock_exporter_class, mock_repo_class, mock_st):
    """
    Test that SQLite persistence remains completely intact and successful 
    even when GCS export fails.
    """
    from app.ui.state_manager import save_current_run
    from app.core.simulation_engine import SimulationEngine
    
    # Mock engine
    mock_engine = MagicMock(spec=SimulationEngine)
    mock_engine.run_data = SimulationRun(org_id="org-1", scenario_id="scen-1", rng_seed=1)
    mock_engine.services = []
    mock_engine.system_states = {}
    mock_engine.bia = MagicMock()
    mock_engine.scoring = MagicMock()
    mock_engine.scoring.get_ledger.return_value = []
    
    # Mock Repo to succeed
    mock_repo = mock_repo_class.return_value
    
    # Mock Exporter to FAIL
    mock_exporter = mock_exporter_class.return_value
    mock_exporter.export_simulation_run.return_value = False
    
    # Run the save function
    save_current_run(mock_engine)
    
    # Verify repo saved
    mock_repo.save.assert_called_once_with(mock_engine.run_data)
    
    # Verify export was attempted
    mock_exporter.export_simulation_run.assert_called_once_with(mock_engine.run_data)
    
    # Verify UI warning was shown due to failure
    mock_st.warning.assert_called_once()
