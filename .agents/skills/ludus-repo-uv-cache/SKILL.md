---
name: ludus-repo-uv-cache
description: Use when running `uv` commands in this Ludus repo and the default global `uv` cache path causes local permission failures. Apply this skill before `uv run ...` commands in `C:\Users\arod741\src\work\labs\ludus`, especially for `scripts/apply_ludus_nomad_lab.py`, `scripts/render_nomad_lab.py`, or inline Python used to poll the tunneled Ludus API.
---

# Ludus Repo Uv Cache

Set the `uv` cache to the repo-local `.uv-cache` directory before any `uv run ...` command in this repo.

Use this when `uv` fails with access errors under the default cache path in `C:\Users\arod741\AppData\Local\uv\cache`.

## Workflow

1. In Powershell, set:

```powershell
$env:UV_CACHE_DIR='C:\Users\arod741\src\work\labs\ludus\.uv-cache'
```

2. Then run the intended `uv` command normally.

3. Keep the setting in the same shell session for follow-up `uv run ...` commands.

## Common Commands

Render the range config:

```powershell
$env:UV_CACHE_DIR='C:\Users\arod741\src\work\labs\ludus\.uv-cache'
uv run -- python scripts/render_nomad_lab.py
```

Upload roles/config and deploy:

```powershell
$env:LUDUS_API_KEY='<current-key>'
$env:UV_CACHE_DIR='C:\Users\arod741\src\work\labs\ludus\.uv-cache'
uv run -- python scripts/apply_ludus_nomad_lab.py --deploy --status
```

Poll the Ludus API directly through inline Python:

```powershell
Start-Sleep -Seconds 210; $env:UV_CACHE_DIR = Join-Path $PWD.Path '.uv-cache'; $env:PYTHONIOENCODING='utf-8'; @'
    import ssl, urllib.request, json, sys
    ctx = ssl._create_unverified_context()
    key = '<current-key>'
    for path in ['https://127.0.0.1:8080/range', 'https://127.0.0.1:8080/range/logs']:
        req = urllib.request.Request(path, headers={'X-API-Key': key})
        with urllib.request.urlopen(req, context=ctx, timeout=30) as r:
            if path.endswith('/range/logs'):
                obj = json.loads(r.read().decode('utf-8', errors='replace'))
                text = 'URL %s CURSOR %s\n%s\n---\n' % (path, obj['cursor'], obj['result'][-28000:])
            else:
                text = 'URL %s\n%s\n---\n' % (path, r.read().decode('utf-8', errors='replace'))
            sys.stdout.buffer.write(text.encode('utf-8', errors='replace'))
    '@ | uv run -- python -
```

## Notes

- This skill is repo-specific. The path is fixed to `C:\Users\arod741\src\work\labs\ludus\.uv-cache`.
- Use it only for this repo unless the repo path changes and the skill is updated.
- The purpose is local execution reliability, not behavior changes in the Ludus API scripts themselves.
