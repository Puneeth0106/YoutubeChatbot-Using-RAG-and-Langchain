Deployment options for Youtube_Chatbot Streamlit app

This folder contains a Streamlit app (`streamlit_app.py`) that indexes YouTube transcripts and answers questions.

Two recommended deployment paths are provided below:

1) Streamlit Community Cloud (fastest)

- Push your project to a GitHub repository (public or private with Streamlit credentials).
- On https://streamlit.io/cloud, create a new app and point it to the GitHub repo and the path `Youtube_Chatbot/streamlit_app.py`.
- Add required secrets (OPENAI_API_KEY) under the app settings or use a `.env` file checked into the repo (not recommended).
- Streamlit Cloud will install dependencies from `requirements.txt` and run the app.

Pros: simplest, automatic builds, built-in domain.
Cons: limited compute, needs repo push.

2) Docker (flexible, runs anywhere)

- Build the Docker image locally and run it, or push to a container registry (Docker Hub, GitHub Container Registry) and deploy to any container host (Railway, Fly, AWS, GCP, etc.).

Build and run locally:

```bash
# from repository root
cd Youtube_Chatbot
# build (tags image 'ytqa')
docker build -t ytqa .
# run (exposes streamlit on 8501 in container)
docker run -it --rm -p 8501:8501 -p 8000:8000 --name ytqa_container ytqa
```

This image runs the Streamlit app by default. If you want the FastAPI server (api_server.py) instead, run:

```bash
# to run uvicorn inside container (example)
docker run -it --rm -p 8000:8000 ytqa bash -lc "uvicorn Youtube_Chatbot.api_server:app --host 0.0.0.0 --port 8000"
```

3) Using a PaaS (Railway, Fly, Render, Heroku)

- Most PaaS providers can build from a Dockerfile or from the Git repository directly. See each provider's docs for linking your GitHub repo.
- Add environment variables (OPENAI_API_KEY) in the provider's dashboard.

Notes and prerequisites

- Ensure your `requirements.txt` contains all packages you need. If you add functionality (e.g., persistence to disk), add extra libraries accordingly.
- For FAISS (`faiss-cpu`) the Docker base image `python:3.11-slim` works, but if you run into binary issues, try `python:3.11-bullseye` or build faiss from source (more complex).
- The Streamlit app and API server expect the OpenAI credentials in env (e.g., `OPENAI_API_KEY`). Use the PAAS secrets or export locally:

```bash
export OPENAI_API_KEY="sk-..."
```

Questions I can implement for you

- Add docker-compose with both Streamlit and FastAPI containers wired together.
- Persist FAISS indices to disk and load them on startup to avoid re-indexing.
- Add CI to build and push Docker images to a registry on git push.

Which deployment target should I prepare files for (Streamlit Cloud, Docker-compose, or a specific host like Railway)?
