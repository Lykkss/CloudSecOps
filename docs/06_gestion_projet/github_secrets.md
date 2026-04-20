# Configuration des secrets GitHub Actions

Pour que la CI/CD fonctionne complètement (envoi des résultats Trivy à la webapp),
configurer les secrets suivants dans **Settings → Secrets → Actions** du repo.

| Secret | Valeur | Requis pour |
|---|---|---|
| `API_URL` | URL publique de l'API, ex: `https://api.cloudsecops.dev` | POST résultats Trivy vers `/scans` |
| `CI_API_KEY` | Même valeur que `CI_API_KEY` dans `.env` | Authentification machine-to-machine |

En développement local (sans `API_URL` configuré), le step de publication est ignoré
et les résultats Trivy sont disponibles en tant qu'**artifact GitHub Actions**
(onglet Actions → run → Artifacts → `trivy-results-<sha>`).
