# Heroku

## CLI
```bash
npm install -g heroku
heroku login
heroku create my-app
git push heroku main
```

## Config: Procfile
```
web: npm start
```

## Detection
- `Procfile`, `app.json`, buildpack detection

## Free Tier
- Gone (pulled Nov 2022)
- Eco dynos: $5/mo
- Held in "sustaining engineering mode" since Feb 2026 — nothing new coming

## Rollback
```bash
heroku releases
heroku rollback v123
```

## Best For
Old workloads and nothing else. For a fresh project, skip it — move to Railway, Render, or Fly instead.
