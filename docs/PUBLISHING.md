# Hue Gradient Studio — Releases and HACS

Repository: https://github.com/derhopp/hue-gradient-studio

## Development

Clone the existing repository and work from the `main` branch:

```bash
git clone https://github.com/derhopp/hue-gradient-studio.git
cd hue-gradient-studio
git switch main
git pull --ff-only origin main
```

Make and review changes to the integration, bundled dashboard editor, tests, or documentation.

## Tests

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js
node tests/test_ui.cjs
```

GitHub Actions runs the same smoke tests plus HACS validation on pushes and pull requests. Check the Actions tab for results.

## Release a new version

Use the maintainer-only helper to update the version in `manifest.json`, both visible version labels in the dashboard JavaScript, and the JavaScript translation import cache parameter (`i18n.js?v=...`):

```bash
python3 scripts/bump_version.py 0.1.5
```

Create `docs/RELEASE_NOTES_0.1.5.md`, including accurate changes for that release. Check that version references match and run the tests.

The script is optional developer tooling; it is **not** used at runtime by Home Assistant, HACS, or GitHub Actions. The repository initialization helper has been removed because this repository is already published.

```bash
git status
git diff --check
git add .
git commit -m "Release 0.1.5"
git push origin main
```

After a successful **Validate** workflow for a push to `main`, the **Publish Version Release** workflow checks the version in `manifest.json` and creates a GitHub Release if it does not already exist.

Do **not** create a duplicate tag or Release for a version already published. Keep every release version unique. GitHub Releases enable normal HACS versioned updates.

Inspect the result with GitHub CLI:

```bash
gh release list
gh release view 0.1.5 --web
```

## Install or update in HACS

1. **HACS → ⋮ → Custom repositories**: add `https://github.com/derhopp/hue-gradient-studio` as **Integration**.
2. Open the integration in HACS and choose **Download** or **Update**.
3. Restart Home Assistant: **Settings → System → Restart**.
4. On first setup, use **Settings → Devices & services → Add integration → Hue Gradient Studio**.
5. Add the dashboard card to an existing tab with [view-only.yaml](view-only.yaml).

The integration serves its own Lovelace JavaScript module at `/hue-gradient-studio/hue-gradient-studio.js?v=<version>`. Check the **Resources** page if the custom element fails to load.

## Repository maintenance

- Keep `hacs.json`, `README.md`, `LICENSE`, and `custom_components/hue_gradient_studio/manifest.json` at the expected paths.
- Maintain a useful GitHub Description and Topics.
- Avoid committing configuration secrets, Home Assistant backups, or `.storage` files.
- Use semantic versions and publish a unique GitHub Release for each HACS update. The current branding refresh release is `0.1.4`.
