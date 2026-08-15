gcloud.cmd storage buckets create gs://bcdrsimulator-exports-507135369511 --location=us-central1 --default-storage-class=STANDARD
if %errorlevel% neq 0 exit /b %errorlevel%

gcloud.cmd storage buckets update gs://bcdrsimulator-exports-507135369511 --lifecycle-file=lifecycle.json
if %errorlevel% neq 0 exit /b %errorlevel%

bq mk --location=us-central1 bcdr_analytics
if %errorlevel% neq 0 exit /b %errorlevel%

gcloud.cmd iam service-accounts create bcdr-cloudrun-sa --display-name="BCDR Simulator Cloud Run SA"
if %errorlevel% neq 0 exit /b %errorlevel%

gcloud.cmd storage buckets add-iam-policy-binding gs://bcdrsimulator-exports-507135369511 --member="serviceAccount:bcdr-cloudrun-sa@bcdrsimulator-sail.iam.gserviceaccount.com" --role="roles/storage.objectUser"
if %errorlevel% neq 0 exit /b %errorlevel%

bq query --use_legacy_sql=false "GRANT `roles/bigquery.dataEditor` ON SCHEMA bcdr_analytics TO 'serviceAccount:bcdr-cloudrun-sa@bcdrsimulator-sail.iam.gserviceaccount.com'"
if %errorlevel% neq 0 exit /b %errorlevel%

echo "All provisioning completed successfully."
