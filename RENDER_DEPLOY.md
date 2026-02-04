# Deploying ScamBee to Render.com

Render is a unified cloud to build and run all your apps and websites. We will use the **Blueprint** feature to deploy easily.

## Prerequisites
1.  **Render Account**: Sign up at [render.com](https://render.com).
2.  **Git Repository**: Push your code (`ScamBee/`) to GitHub or GitLab.

## Steps

### 1. Connect Repository
- Go to your [Render Dashboard](https://dashboard.render.com/).
- Click **New +** -> **Blueprint**.
- Connect your GitHub/GitLab account and select the **ScamBee** repository.

### 2. Configure Blueprint
- Render will detect the `render.yaml` file automatically.
- It will ask for the Environment Variables defined in the YAML (`sync: false`):
    - `GEMINI_API_KEY`: Paste your key.
    - `SCAMBEE_API_KEY`: Paste your key.

### 3. Deploy
- Click **Apply** or **Create Web Service**.
- Render will:
    1.  Pull your code.
    2.  Build the Docker image (using your `Dockerfile`).
    3.  Deploy it to a public URL (e.g., `https://scambee-api.onrender.com`).

### 4. Test
Once deployed (green checkmark), copy the **Service URL** and test:
```powershell
curl -X POST "https://YOUR-RENDER-URL.onrender.com/chat" `
     -H "x-api-key: YOUR_SECRET_KEY" `
     -H "Content-Type: application/json" `
     -d '{"session_id": "render-test", "message": "Scam message", "history": []}'
```
