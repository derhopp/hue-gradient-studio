# Hue Gradient Studio 0.1.0 auf GitHub veröffentlichen und mit HACS installieren

**Alle folgenden Terminal-Befehle beziehen sich auf macOS**. Führe sie im lokal entpackten Repository-Ordner aus. Die sichtbaren Home-Assistant-Menüs sind auf Englisch angegeben.

## A. Vorbereitung

1. Erstelle auf Home Assistant zuerst ein vollständiges Backup. Sichere besonders `/config/.storage/hue_gradient_studio` (Vorsicht: `.storage` nicht ins öffentliche GitHub-Repository kopieren).
2. Erzeuge auf [GitHub](https://github.com/) ein Konto, falls noch keines vorhanden ist.
3. Installiere Git und GitHub CLI (falls nötig):

```bash
# Falls Homebrew noch nicht vorhanden ist: https://brew.sh/
brew install git gh

git --version
gh --version
gh auth login
# Wähle GitHub.com -> HTTPS -> Login with a web browser

gh auth status
```

4. Lade das bereitgestellte ZIP auf deinen Mac, entpacke es, und wechsle in den Repository-Ordner. Beispiel, wenn es in `~/Downloads` liegt:

```bash
cd ~/Downloads
unzip Hue_Gradient_Studio_HACS_0.1.0_GitHub_Ready.zip
cd hue-gradient-studio-hacs-0.1.0
```

## B. Eigene GitHub-Daten eintragen

Ersetze `DEIN_GITHUB_NAME` durch deinen tatsächlichen Benutzernamen. Das Script aktualisiert `manifest.json` und die Links im README.

```bash
python3 scripts/prepare_repository.py DEIN_GITHUB_NAME
cat custom_components/hue_gradient_studio/manifest.json
cat hacs.json
```

Soll das Repository anders als `hue-gradient-studio` heißen, übergib den Repository-Namen als zweites Argument:

```bash
python3 scripts/prepare_repository.py DEIN_GITHUB_NAME mein-hue-projekt
```

In diesem Fall musst du auch in den folgenden `gh`-Befehlen den Repository-Namen entsprechend anpassen.

**Prüfe außerdem:** Soll das Projekt öffentlich sein? HACS Custom Repositories sind üblicherweise öffentliche GitHub-Repositories. Überlege dir eine Lizenz; wir haben bewusst keine erfunden.

## C. Tests lokal ausführen

```bash
python3 -m compileall -q custom_components tests
python3 -m unittest discover -s tests -p 'test_*.py' -v
node --check custom_components/hue_gradient_studio/frontend/hue-gradient-studio.js
node tests/test_ui.cjs
```

Wenn Node.js fehlt, kannst du es über `brew install node` installieren. Python und Git sind die Mindestvoraussetzung für die Veröffentlichung; Node wird nur für den JavaScript-Test benötigt.

## D. Neues GitHub-Repository anlegen und ersten Commit pushen

Im ausgepackten Repository-Ordner:

```bash
git init -b main
git add .
git commit -m "Initial HACS integration release 0.1.0"

gh repo create DEIN_GITHUB_NAME/hue-gradient-studio \
  --public --source=. --remote=origin --push
```

Damit wird ein **öffentliches** GitHub-Repository erstellt und dein erster Commit auf `main` hochgeladen. Das Repository darf für diesen Befehl noch nicht existieren.

**Falls du das leere Repository zuvor im Browser erstellt hast**, verwende stattdessen:

```bash
git remote add origin https://github.com/DEIN_GITHUB_NAME/hue-gradient-studio.git
git push -u origin main
```

Falls `origin` schon existiert: `git remote -v` prüfen und nicht erneut hinzufügen.

## E. GitHub Release 0.1.0 veröffentlichen

```bash
git tag -a 0.1.0 -m "Hue Gradient Studio 0.1.0"
git push origin 0.1.0

gh release create 0.1.0 \
  --verify-tag \
  --title "Hue Gradient Studio 0.1.0" \
  --notes-file docs/RELEASE_NOTES_0.1.0.md

gh release view 0.1.0 --web
```

**Wichtig:** HACS orientiert sich an **veröffentlichten Releases**, nicht nur an vorhandenen Git-Tags. Das Release ist deshalb ein notwendiger Schritt für eine saubere Versionsverwaltung. Die GitHub-Source-Archive sind ausreichend: `zip_release` und eigens hochgeladene Binär-ZIPs sind **nicht nötig**, da HACS direkt `custom_components/hue_gradient_studio/` installiert.

## F. Mit HACS installieren

In Home Assistant:

1. **HACS → ⋮ → Custom repositories**.
2. URL: `https://github.com/DEIN_GITHUB_NAME/hue-gradient-studio`.
3. **Category:** `Integration` → **Add**.
4. **HACS → Hue Gradient Studio → Download**. Wähle Release `0.1.0`.
5. **Settings → System → Restart**.
6. Bei **neuer Einrichtung**: **Settings → Devices & services → Add integration → Hue Gradient Studio**.
7. Unter **Settings → Dashboards → ⋮ → Resources** überprüfen, ob automatisch `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.0` als `JavaScript Module` angelegt wurde.
8. Optional im vorhandenen Dashboard einen **neuen Tab** anlegen und `docs/view-only.yaml` nur in dessen **View configuration → Edit in YAML** einfügen. Niemals die gesamte Raw-Konfiguration des bestehenden Dashboards überschreiben.

**Wenn du bereits die v3.0.1 manuell installiert hast:** HACS überschreibt den bestehenden Custom-Component-Code. Lass die Presets in `.storage` bestehen. Entferne den alten Resource-Eintrag `/local/hue-gradient-studio.js?v=3`, damit nur die von HACS verwaltete Karte geladen wird. Du kannst die alte YAML-Aktivierung vorerst behalten oder nach **Add integration** entfernen und neu starten. Die Anleitung steht auch in der `README.md`.

## G. Update veröffentlichen (Beispiel: 0.1.1)

1. Änderungen an den Python-/JavaScript-Dateien durchführen.
2. Version von `manifest.json` auf **0.1.1** anheben (das Script aktualisiert auch die JS-Kartenbezeichnung):

```bash
python3 scripts/bump_version.py 0.1.1
```

3. Tests durchführen:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_ui.cjs
```

4. Neue Release Notes schreiben und committen:

```bash
cp docs/RELEASE_NOTES_0.1.0.md docs/RELEASE_NOTES_0.1.1.md
# Inhalt von docs/RELEASE_NOTES_0.1.1.md mit tatsächlichen Änderungen aktualisieren.

git add .
git commit -m "Release 0.1.1"
git push origin main

git tag -a 0.1.1 -m "Hue Gradient Studio 0.1.1"
git push origin 0.1.1

gh release create 0.1.1 \
  --verify-tag \
  --title "Hue Gradient Studio 0.1.1" \
  --notes-file docs/RELEASE_NOTES_0.1.1.md
```

5. In Home Assistant auf die neue HACS-Version aktualisieren und **Settings → System → Restart** ausführen. Die Integration aktualisiert den Resource-Query-Parameter automatisch, um veraltete JS-Dateien im Browsercache zu vermeiden.

**Versionierungsregel:** GitHub Release-Tag `0.1.1` = `manifest.json`-Version `0.1.1`. `hacs.json` braucht keine Versionsnummer.

## H. Troubleshooting

- **Custom repository invalid**: Prüfe, ob `hacs.json`, `README.md`, `custom_components/hue_gradient_studio/manifest.json` und `__init__.py` im GitHub-Repository auf der `main`-Branch vorhanden sind. Die echten GitHub-URLs in `manifest.json` müssen eingetragen sein.
- **No HACS updates**: Prüfe, dass du nicht nur einen Git-Tag, sondern wirklich einen GitHub **Release** veröffentlicht hast, und dass `manifest.json` dieselbe Version enthält.
- **Custom element doesn't exist**: Prüfe die Ressource `/hue-gradient-studio/hue-gradient-studio.js?v=0.1.0` unter **Settings → Dashboards → ⋮ → Resources** sowie **Settings → System → Logs**. Browser neu laden.
- **Old UI after update**: Entferne die alte `/local/hue-gradient-studio.js?v=3` Ressource; die neue wird unter `/hue-gradient-studio/...` geladen. Gegebenenfalls Browsercache leeren.
- **No Philips lights**: ZHA überprüfen und gegebenenfalls unter **Settings → Devices & services → ZHA** die Lampen kontrollieren. Nur ZHA-Hue-Leuchten werden im Studio aufgelistet.
- **WebSocket error**: Bei `AttributeError: ActiveConnection.require_admin` läuft noch altes v3.0.0; die hier gebündelte v0.1.0 enthält den Fix.
- **YAML resource mode**: `lovelace.resources` muss manuell in `configuration.yaml` gepflegt werden, siehe README.

## Sicherheit

Keine GitHub-Zugangsdaten, Home Assistant Tokens, Backups oder `.storage/`-Dateien ins Repository committen. `git status` und `git diff --cached --stat` vor dem ersten Push überprüfen.
