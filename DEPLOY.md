# VPS deployment

The repository includes a manual GitHub Actions deployment workflow. It deploys into the isolated directory `/opt/ai-shorts-factory`; it does not touch other services or project directories.

## Required GitHub Actions secrets
Add these in **Settings → Secrets and variables → Actions**:
- `VPS_HOST`: VPS IP or hostname
- `VPS_USER`: SSH account with permission to run Docker Compose
- `VPS_SSH_KEY`: private SSH key for that account
- `VPS_KNOWN_HOSTS`: trusted host-key line for the VPS (obtain and verify it independently)
- `FACTORY_API_KEY`: long random API key for the application

Optional secrets: `TELEGRAM_BOT_TOKEN`, `LLM_API_KEY`.
Optional repository variables: `LLM_BASE_URL`, `LLM_MODEL`.

The VPS must already have Docker Engine and the Docker Compose plugin installed. The workflow does not install system packages or modify firewall settings.

After adding the secrets, open **Actions → Deploy to VPS → Run workflow**. The workflow writes its own `.env` on the VPS and starts the Compose stack. Application data remains in a named Docker volume. The deployment path is separate from existing projects.
