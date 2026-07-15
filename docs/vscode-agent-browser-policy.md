# VS Code Agent Browser Policy

Default browser posture is deny-by-default for camera, microphone, and location.

Remote-workspace browser proxying is prohibited for Oracle, infrastructure, and physical-AI repositories. Agent browsing is restricted to public documentation domains and localhost test ports listed in `.vscode/settings.security.example.json`.

Blocked targets include production URLs, corporate hostnames, and private network ranges. The agent must ask for confirmation before screenshots, downloads, form submission, authentication, or file upload.

Verification checklist:

- Confirm camera, microphone, and location are denied.
- Confirm remote workspace browser proxying is disabled.
- Confirm localhost ports are limited to expected dev/test ports.
- Confirm public documentation domains are allowlisted explicitly.
- Confirm production URLs and private network ranges are blocked.
- Confirm screenshots, downloads, forms, authentication, and uploads require confirmation.

Rollback:

1. Remove copied workspace overrides.
2. Restore the previous VS Code settings file from source control or local backup.
3. Re-open the workspace and verify policy prompts return to the previous behavior.
4. Do not relax policy for Oracle, infrastructure, or physical-AI repositories without a written approval record.
