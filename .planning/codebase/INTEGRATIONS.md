# External Integrations

**Analysis Date:** 2026-09-09

## External APIs & Protocols
- **Email (IMAP):** Connects to IMAP servers (default configured for Gmail: `imap.gmail.com:993`) to fetch, list, and parse unread user emails using Python's `imaplib` and `email` packages.

## Databases & Storage
- **File-based Local Storage:** Uses local JSON files for persistent data rather than an external database.
  - **Memory & Tasks:** Stored in the user's `Documents/Nexus` directory (Projects, Deadlines, Tasks).
  - **Conversations:** History stored temporarily in the OS temp directory (`%TEMP%/Nexus/conversations/history.json`).

## Authentication Providers
- **Email Authentication:** Uses basic email credentials (username and app password) configured in `.env`. No OAuth or external SSO integrated.

## Webhooks
- No webhooks or incoming external triggers are currently configured.

<!-- refreshed: 2026-09-09 -->
*Integrations analysis: 2026-09-09*
