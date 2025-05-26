# Fragment Service
### A compositon of minimalistic services for hosting fragmented audio files and images with metadata stored in PostgreSQL Database and file integrity checks (MD5) upon upload and download. Made in Python FastAPI with Caddy automatic TLS certificates, pgAdmin for DB management and configured GitHub Actions CI/CD pipelines for automated testing, building and pushing to GitHub Container Registry. Bash scripts for testing and deployment purposes. Files uploaded to the service are be stored in `uploaded_files` directory under UUID identified user directory.

### Requirements: Live Supabase instance with Auth and `.secrets` file with `SUPABASE_JWT_SECRET`, `SUPABASE_URL`, `SUPABASE_KEY`, `GHCR_TOKEN`.

To start run:
```docker compose up```

Available Services:
`https://localhost:5050`    - PostgreSQL pgAdmin
`https://localhost/docs`    - SwaggerUI FastAPI UI
`https://localhost`         - FastAPI Endpoints

To run tests locally run (using GitHub Actions pipeline):
```act -j test --secret-file .secrets```