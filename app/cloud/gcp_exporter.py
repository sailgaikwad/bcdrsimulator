import json
import logging
import streamlit as st
from google.cloud import storage
from google.oauth2 import service_account
from google.api_core.exceptions import GoogleAPICallError, RetryError
from google.auth.exceptions import DefaultCredentialsError
from app.models.simulation import SimulationRun

logger = logging.getLogger(__name__)

class GCPExporter:
    """Exports SimulationRun data to Google Cloud Storage."""

    def __init__(self, bucket_name: str = "bcdrsimulator-exports-507135369511"):
        self.bucket_name = bucket_name
        self._client = None

    def _get_client(self):
        # Lazy initialization to handle missing ADC gracefully
        if self._client is None:
            try:
                # 1. Try to load credentials from Streamlit Cloud Secrets
                if "gcp_service_account" in st.secrets:
                    # st.secrets converts the TOML section to a dict-like object
                    creds_dict = dict(st.secrets["gcp_service_account"])
                    credentials = service_account.Credentials.from_service_account_info(creds_dict)
                    self._client = storage.Client(credentials=credentials, project=creds_dict.get("project_id"))
                else:
                    # 2. Fallback to local environment Application Default Credentials (ADC)
                    self._client = storage.Client()
            except Exception as e:
                logger.debug(f"Failed to load from st.secrets, falling back to local ADC: {e}")
                self._client = storage.Client()
                
        return self._client

    def export_simulation_run(self, run: SimulationRun) -> bool:
        """
        Exports the simulation run to GCS.
        Returns True if successful, False if it failed.
        Never raises exceptions (graceful degradation).
        """
        try:
            client = self._get_client()
            bucket = client.bucket(self.bucket_name)
            
            # Construct the stable JSON payload
            payload = {
                "id": run.id,
                "org_id": run.org_id,
                "scenario_id": run.scenario_id,
                "rng_seed": run.rng_seed,
                "status": run.status.value,
                "start_time": run.start_time,
                "end_time": run.end_time,
                "total_downtime_hours": run.total_downtime_hours,
                "final_resilience_score": run.final_resilience_score,
                "final_risk_level": run.final_risk_level.value if run.final_risk_level else None,
                "decisions_json": run.decisions_json,
                "config_json": run.config_json,
                "schema_version": run.schema_version,
                "state_snapshot_json": run.state_snapshot_json,
                "event_ledger_json": run.event_ledger_json,
                "timeline_json": run.timeline_json,
                "team_id": run.team_id,
            }
            
            blob = bucket.blob(f"runs/{run.id}.json")
            
            # Upload as application/json
            blob.upload_from_string(
                json.dumps(payload),
                content_type="application/json"
            )
            
            logger.info(f"Successfully exported run {run.id} to GCS bucket {self.bucket_name}.")
            return True
            
        except DefaultCredentialsError:
            logger.warning(
                f"Skipped GCS export for run {run.id}: Application Default Credentials (ADC) missing."
            )
            return False
        except (GoogleAPICallError, RetryError) as e:
            logger.warning(
                f"Failed to export run {run.id} to GCS due to API/Network error: {str(e)}"
            )
            return False
        except Exception as e:
            logger.error(
                f"Unexpected error exporting run {run.id} to GCS: {str(e)}"
            )
            return False
