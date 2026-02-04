# Deploying ScamBee to Google Cloud Run

Follow these steps to deploy your API to a serverless authentication-managed container.

## Prerequisites
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed and initialized.
- A Google Cloud Project created.

## 1. Authenticate & Set Project
> **Troubleshooting:** If you see `gcloud : The term 'gcloud' is not recognized`, **close and reopen your terminal** (PowerShell/CMD) to refresh your system PATH after installation.

```powershell
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

## 2. Deploy using Source
This command builds the container securely using Cloud Build and deploys it to Cloud Run.

Replace `YOUR_GEMINI_KEY` and `YOUR_SCAMBEE_KEY` with your actual secrets.

```powershell
gcloud run deploy scambee-api --source . --platform managed --region us-central1 --allow-unauthenticated --set-env-vars "GEMINI_API_KEY=YOUR_GEMINI_KEY,SCAMBEE_API_KEY=YOUR_SCAMBEE_KEY"
```

> **Tip:** If the multi-line command fails, copy and run the single-line version above.

> **Note:** For production, it is recommended to use [Secret Manager](https://cloud.google.com/run/docs/configuring/secrets) instead of plain environment variables.

## 3. Verify Deployment
Once the command finishes, it will output a **Service URL** (e.g., `https://scambee-api-xyz-uc.a.run.app`).

Test it:
```powershell
curl -X POST "https://YOUR-SERVICE-URL/chat" `
     -H "x-api-key: YOUR_SCAMBEE_KEY" `
     -H "Content-Type: application/json" `
     -d '{"session_id": "test", "message": "You won lottery!", "history": []}'
```
