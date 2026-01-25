# Catalog Design Notes (JSON + Web UI)

## Goals
- Keep the catalog JSON-based, with plugins and samples in separate files.
- Support expandable tree views in a browser.
- Allow rich fields like `description`, `tags`, and optional metadata.
- Make updates low-friction: rerun a scan script and keep manual notes stable.

## File Layout
```
catalog/
  plugins.json
  samples.json
  notes.json
  schema/
    plugins.schema.json
    samples.schema.json
```

## JSON Structure (Plugins)
```json
{
  "generated_at": "2025-01-25T00:00:00Z",
  "sources": [
    "/Library/Audio/Plug-Ins/VST3",
    "/Library/Audio/Plug-Ins/Components",
    "~/Library/Audio/Plug-Ins/VST3",
    "~/Library/Audio/Plug-Ins/Components"
  ],
  "plugins": [
    {
      "name": "Example Synth",
      "type": "vst3",
      "vendor": "Vendor Name",
      "description": "",
      "tags": ["synth", "analog"],
      "path": "/Library/Audio/Plug-Ins/VST3/Example Synth.vst3",
      "added_at": "2025-01-25T00:00:00Z"
    }
  ]
}
```

## JSON Structure (Samples)
```json
{
  "generated_at": "2025-01-25T00:00:00Z",
  "roots": [
    "/Volumes/External SSD/Sample Kits",
    "/Volumes/External SSD/Samples Local"
  ],
  "nodes": [
    {
      "path": "Drums/Acoustic/Kit A",
      "description": "",
      "tags": ["drums", "acoustic"]
    }
  ]
}
```

## Suggested Approach for Notes (Descriptions, Tags)
- Keep *scanned data* and *manual notes* separate to avoid losing edits on refresh.
- Store manual notes in a `notes.json` keyed by `path` or `name`.
- Merge notes at runtime in the UI.

Example `notes.json`:
```json
{
  "plugins": {
    "Example Synth": {
      "description": "Warm analog-style synth with rich unison.",
      "tags": ["synth", "warm"]
    }
  },
  "samples": {
    "Drums/Acoustic/Kit A": {
      "description": "Live kit recorded at 96k.",
      "tags": ["drums", "live"]
    }
  }
}
```

## Browser UI (Expandable Tree)
- Use a simple static site with:
  - Tree view (collapsible folders)
  - Search/filter field
  - Detail pane for descriptions/tags
- Consider a lightweight UI stack:
  - Vanilla JS + CSS for portability
  - Or a small React app if you want richer interactions

### Tree Model Suggestion
- Convert flat `nodes` into a tree:
  - Split `path` by `/`
  - Build nested objects with `children`
  - Render expand/collapse nodes

## Update Flow
1. Run scanner scripts to rebuild `plugins.json` and `samples.json`.
2. Keep `notes.json` untouched (manual edits remain).
3. UI merges base data + notes on load.

## Future Extensions
- Add `software.json` later with installed apps and licenses.
- Track counts for sample folders (wav/aif counts).
- Add `last_seen` for soft deletion detection.
