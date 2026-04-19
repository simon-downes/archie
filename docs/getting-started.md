# Getting Started

## 1. Installation

Install both archie and agent-kit:

```bash
uv tool install git+https://github.com/simon-downes/archie.git
uv tool install git+https://github.com/simon-downes/agent-kit.git
```

## 2. Initial Setup

Deploy the persona and default config:

```bash
archie install
```

This creates `~/.archie/` with the persona files and a default `config.yaml`. Config
changes are picked up immediately; persona changes require re-running `archie install`.

Build the sandbox image:

```bash
archie build
```

This builds a Debian-based Docker image with development tools, language runtimes, and
CLI utilities. Use `archie build --quick` for subsequent rebuilds using Docker cache.

## 3. Credentials

Archie uses [agent-kit](../agent-kit/README.md) for credential management. Each service
below is optional — skip any you don't use.

### GitHub

Enables repository operations via the `gh` CLI inside the sandbox.

1. Create a [personal access token](https://github.com/settings/tokens) with repo scope
2. Store it:

```bash
ak auth set github token
```

### Notion

Enables searching, reading, and writing Notion pages and databases.

1. Run the OAuth login flow (opens your browser):

```bash
ak auth login notion
```

Tokens are refreshed automatically when expired. See
[Notion docs](../agent-kit/docs/notion.md) for access scoping configuration.

### Linear

Enables issue tracking — querying, creating, and updating issues.

1. Create a [personal API key](https://linear.app/settings/api)
2. Store it:

```bash
ak auth set linear token
```

See [Linear docs](../agent-kit/docs/linear.md) for team and project filtering.

### Slack

Enables sending messages to Slack channels via incoming webhooks.

1. Create an [incoming webhook](https://api.slack.com/messaging/webhooks) for your workspace
2. Store the URL:

```bash
ak auth set slack webhook_url
```

### AWS

Enables AWS CLI operations inside the sandbox.

If you use `aws-vault` or similar, import credentials from your environment:

```bash
aws-vault exec my-profile -- ak auth import aws \
  AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

Otherwise, set them directly:

```bash
ak auth set aws access_key_id secret_access_key session_token
```

### Scalr

Enables Scalr CLI operations for infrastructure management.

1. Create an API token in your Scalr account
2. Store the token and hostname:

```bash
ak auth set scalr token hostname
```

### Verifying Credentials

Check which credentials are configured:

```bash
ak auth status
```

## 4. Brain Setup

The brain is Archie's persistent knowledge store — files on disk, organised into contexts
(each a separate git repo). See [Brain](brain.md) for how Archie uses it.

### Configure Contexts

Edit `~/.agent-kit/config.yaml` to define your brain contexts:

```yaml
brain:
  dir: ~/.archie/brain
  contexts:
    shared: null                                    # local-only
    work-acme: git@github.com:you/brain-acme.git    # cloned from remote
    personal: git@github.com:you/brain-personal.git
```

`shared` is the default context for cross-cutting knowledge (identity, contacts, general
reference). Additional contexts separate different areas of life or work. Contexts with a
git URL are cloned; `null` contexts are created locally.

### Initialise

```bash
ak brain init
```

This creates the brain directory structure, the raw processing pipeline, and
initialises/clones all configured contexts.

See [agent-kit brain docs](../agent-kit/docs/brain.md) for context structure, indexing,
and project configuration.

## 5. Configure Project Directory

Agent-kit needs to know where your projects live. Edit `~/.agent-kit/config.yaml`:

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
mounted read-only. Archie has full context of your project and can read from the brain.

From outside a project directory (or from the archie project itself):

```bash
cd ~/dev/archie
archie
```

This starts an Archie session with the brain mounted read-write — used for knowledge
work, ingestion, planning, and self-extension.

For a named general session (not tied to a project):

```bash
archie --session research
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
- Brain contexts
- Active sessions
