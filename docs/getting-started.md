# Getting Started

## 1. Installation

```bash
uv tool install git+https://github.com/simon-downes/archie.git
```

## 2. Initial Setup

Run the one-time setup:

```bash
archie init
```

This creates `~/.archie/` with config, credentials, and the brain directory structure.

Build the sandbox image:

```bash
archie build
```

This builds a Debian-based Docker image with development tools, language runtimes, and
CLI utilities. Use `archie build --quick` for subsequent rebuilds using Docker cache.

## 3. Credentials

Each service below is optional — skip any you don't use.

### GitHub

Enables repository operations via the `gh` CLI inside the sandbox.

1. Create a [personal access token](https://github.com/settings/tokens) with repo scope
2. Store it:

```bash
archie auth set github token
```

### Notion

Enables searching, reading, and writing Notion pages and databases.

1. Run the OAuth login flow (opens your browser):

```bash
archie auth login notion
```

Tokens are refreshed automatically when expired.

### Linear

Enables issue tracking — querying, creating, and updating issues.

1. Create a [personal API key](https://linear.app/settings/api)
2. Store it:

```bash
archie auth set linear token
```

### Jira

Enables Jira Cloud issue tracking — querying, creating, updating, and transitioning issues.

1. Create a [scoped API token](https://id.atlassian.com/manage-profile/security/api-tokens)
   with classic scopes: `read:jira-work`, `read:jira-user`, `write:jira-work`
2. Get your cloud ID from `https://<your-site>.atlassian.net/_edge/tenant_info`
3. Store credentials:

```bash
archie auth set jira email
archie auth set jira token
archie auth set jira cloud_id
```

### Google Workspace

Enables read-only access to Gmail, Calendar, and Google Drive.

1. Create a Google Cloud project with a Desktop App OAuth client
2. Enable Gmail API, Calendar API, and Drive API
3. Store credentials and authenticate:

```bash
archie auth set google client_id
archie auth set google client_secret
archie auth login google
```

### Slack

Enables reading channels and searching messages, plus sending notifications.

**Read access** — requires a Slack app with PKCE OAuth:

```bash
archie auth set slack client_id
archie auth set slack client_secret
archie auth login slack
```

**Write access** — uses an incoming webhook:

```bash
archie auth set slack webhook_url
```

### AWS

Enables AWS CLI operations inside the sandbox.

If you use `aws-vault` or similar, import credentials from your environment:

```bash
aws-vault exec my-profile -- archie auth import aws \
  AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

Otherwise, set them directly:

```bash
archie auth set aws access_key_id secret_access_key session_token
```

### Scalr

Enables Scalr CLI operations for infrastructure management.

1. Create an API token in your Scalr account
2. Store the token and hostname:

```bash
archie auth set scalr token hostname
```

### Verifying Credentials

Check which credentials are configured:

```bash
archie auth status
```

## 4. Brain Setup

The brain is a persistent knowledge base — files on disk in a single git repo.
See [Brain](brain.md) for structure and usage.

`archie init` creates the brain directory structure with a convention guide (`BRAIN.md`),
user profile skeleton, and agent operational files.

## 5. Configure Project Directory

Edit `~/.archie/config.yaml` to set your projects root:

```yaml
project_dir: ~/dev
```

Archie uses this to detect which project you're working in and mount it into the sandbox.

## 6. First Run

From inside a project directory:

```bash
cd ~/dev/my-project
archie
```

This launches Archie in the sandbox with your project mounted read-write and the brain
available for context.

For a named session (isolated working directory):

```bash
archie --name research
```

## 7. Verification

Check that everything is ready:

```bash
archie status
```

This shows:
- Docker status
- Sandbox image state
- Credential configuration and expiry
- Mount availability
- Brain status
- Active sessions
