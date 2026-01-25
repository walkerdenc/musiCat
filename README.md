# gpttest

Design notes for the catalog system live in `docs/catalog_design.md`.

## Web UI
Serve the `web` directory so the browser can load JSON files from `catalog/`:

```
python -m http.server 8000 --directory web
```

Then open `http://localhost:8000` in a browser.
