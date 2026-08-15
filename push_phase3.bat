@echo off
echo Authenticating Docker to Google Artifact Registry...
call gcloud.cmd auth configure-docker us-central1-docker.pkg.dev --quiet

echo Tagging local image...
docker tag bcdrsimulator:local us-central1-docker.pkg.dev/bcdrsimulator-sail/bcdr-images/bcdrsimulator:phase3

echo Pushing image to Artifact Registry...
docker push us-central1-docker.pkg.dev/bcdrsimulator-sail/bcdr-images/bcdrsimulator:phase3

echo Done. Please return to Antigravity.
