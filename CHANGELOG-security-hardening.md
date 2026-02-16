# App Icon, Server Controls & Security Hardening

## Phase 1: macOS App Icon & Server Controls

| File | What Changed |
|------|-------------|
| `desktop/resources/icon.png` | New 1024x1024 app icon (dark circle + "N" glyph with glow) |
| `desktop/resources/icon.icns` | macOS .icns icon for distribution |
| `desktop/src/main/tray.ts` | Dynamic Start/Stop Server toggle, Restart Server (disabled when stopped), menu rebuilds on state change |
| `desktop/package.json` | Added `electron-builder`, `dist` script, `build` config with icon paths and DMG target |
| `scripts/generate_icon.py` | One-off icon generation script |

## Phase 2: Voice Authentication

| File | What Changed |
|------|-------------|
| `nex/api/voice_auth.py` | **New** — `VoiceAuth` class with `enroll()`, `verify()`, `is_enrolled()`, `reset()` using resemblyzer d-vector embeddings |
| `nex/voice/mic_listener.py` | Voice auth check before command dispatch; enrollment flow captures 3 utterances; blocks unrecognised speakers |
| `nex/api/command_handler.py` | Added `enroll_voice` and `reset_voice_auth` LLM tools |
| `nex/api/routes/settings.py` | Added `/api/settings/voice-auth-status` endpoint |
| `nex/ui/static/index.html` | Voice Authentication settings section (status, Enroll, Reset buttons) |
| `nex/ui/static/js/nex-settings.js` | Voice auth UI controls wired to WebSocket commands |

## Phase 3: API & WebSocket Security

| File | What Changed |
|------|-------------|
| `nex/api/server.py` | CORS restricted to localhost, session token generated on startup, `/api/auth/token` endpoint |
| `nex/api/websocket_handler.py` | Token auth required (5s timeout), unauthenticated connections rejected with code 4001 |
| `nex/ui/static/js/nex-orb.js` | Fetches auth token before WebSocket connect, sends as first message |
| `nex/api/routes/commands.py` | Blocks `python -c/m`, pipes `|`, semicolons `;`, `&&`, backticks, `$()`, `eval`, `exec`, `source` |
| `nex/api/command_handler.py` | Rate limiter (20 cmds/min per source), auto-lock after 15min inactivity |

## Phase 4: Data Protection

| File | What Changed |
|------|-------------|
| `nex/api/memory_manager.py` | Fernet encryption for `facts` and `tasks` at rest; key at `~/.nex/data/.key` (chmod 600); transparent decrypt on load, encrypt on save; graceful fallback if `cryptography` missing |
| `requirements.txt` | Added `resemblyzer>=0.1.3`, `cryptography>=42.0.0` |

## Verification Checklist

1. **Icon**: Launch app — dock shows custom Nex icon, About window shows icon
2. **Tray**: Click tray → "Stop Server" when running, "Start Server" when stopped
3. **Voice auth**: Enroll voice → speak command → accepted. Different person speaks → "I don't recognise your voice"
4. **WebSocket**: Connect without token → rejected. With token → accepted
5. **CORS**: Cross-origin request from random site → blocked
6. **Rate limit**: Spam 25 commands in 1 minute → last 5 rejected
7. **Encryption**: Check `memory.json` — facts/tasks are encrypted blobs, not plaintext
8. **Auto-lock**: Wait 15 min idle → voice command blocked until re-verified
9. **Command bypass**: Try `python -c "import os; os.system('rm -rf /')"` via REST → blocked
