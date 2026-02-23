# Fanvue Post Creator

Automated content posting system for Fanvue using n8n workflows.

## Architecture

- **n8n instance**: `https://n8.srv1212151.hstgr.cloud`
- **Main workflow**: Fanvue Auto Post v2.3 (`EFqAicul5W6swAEM`, 32 nodes)
- **Social media workflow**: Social Media Auto Post via Make (`8cYFbdjbo8s6luCA`, 16 nodes)
- **Digest workflow**: Fanvue Weekly Digest (`mF91qgEFusnlYcmt`, 7 nodes)

## What the system does

1. **Auto-posting (Fanvue)**: Picks random unused NSFW media (`source_folder: "nsfw"`) from Dropbox, generates AI caption (GPT-4o), uploads to Fanvue. Runs 2-4 times/day between 9-21h.
2. **Dynamic PPV**: Videos get PPV pricing - weekday $4.99, weekend $6.99, evening (18-21h) +$1.00. Images are free.
3. **Post history**: Every post logged to n8n DataTable `post_history`.
4. **Social media posting (Instagram)**: Separate workflow picks random SFW images (`source_folder: "socialmedia"`), sends to Make.com webhook for Instagram publishing. Runs 1-2 times/day between 10-20h.
5. **Revenue tracking**: Every post logged to Google Sheets "Revenue" tab.
6. **Low content alerts**: Warning in success email when < 10 media files remaining.
7. **Weekly digest**: Monday 9AM email with weekly stats summary.

## Files

- `fanvue-auto-post-v2.json` - Main Fanvue workflow definition (source of truth is n8n, this is a backup)
- `fanvue-social-media-post.json` - Social media/Instagram workflow via Make.com
- `fanvue-weekly-digest.json` - Weekly digest workflow definition

## Credentials

All credentials are stored in n8n, NOT in this repo. API keys are in `.claude/mcp_settings.json` (gitignored).

- Dropbox, Fanvue OAuth2, OpenAI, Gmail, Google Sheets OAuth2

## Deploying changes

1. Edit workflow JSON locally
2. PUT to `https://n8.srv1212151.hstgr.cloud/api/v1/workflows/{id}` with API key
3. Strip settings to only: `executionOrder`, `callerPolicy`, `availableInMCP`
4. After deploying, always export latest JSON back from n8n to keep repo in sync

## Testing

```bash
# Trigger a test Fanvue post
curl -s -X POST "https://n8.srv1212151.hstgr.cloud/webhook/fanvue-auto-post-v2" -H "Content-Type: application/json" -d '{}'

# Trigger a test social media post (Instagram via Make.com)
curl -s -X POST "https://n8.srv1212151.hstgr.cloud/webhook/social-media-auto-post" -H "Content-Type: application/json" -d '{}'

# Trigger weekly digest
curl -s -X POST "https://n8.srv1212151.hstgr.cloud/webhook/fanvue-weekly-digest" -H "Content-Type: application/json" -d '{}'
```

## Conventions

- Commit messages in English
- Conversation in Polish
- Do not store API keys, passwords, or tokens in git
