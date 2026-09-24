# AGENTS.md - Project Specific Operating Guidelines

## Emoji Usage Rule for WhatsApp and Telegram Messages

- **Permitted and Recommended:** Emojis are explicitly permitted and encouraged in all user-facing messages sent via **WhatsApp** and **Telegram** (including command responses, reminders, status alerts, QR code login captions, error notifications, and help menus) to maintain a friendly, clear, and engaging user experience.
- **Prohibited:** Emojis remain prohibited in code logic, variable names, system logs, code comments, and technical documentation outside of chat message templates.

## Architecture and Environment

- The primary runtime is **Home Assistant OS** running as a Docker add-on.
- The shared configuration path is `/config` (where `credentials.json` is provided by the user).
- The persistent data directory is `/data` (where SQLite databases and secured `credentials.json` reside).
- Local testing configurations are retained for development purposes.

## Testing and Quality Standards

- Maintain comprehensive unit tests in the `tests/` directory.
- Verify all changes before committing.
