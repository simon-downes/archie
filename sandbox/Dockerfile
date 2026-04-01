## ---------- Fetcher stage: download GitHub releases ----------
FROM debian:bookworm-slim AS fetcher

ARG TARGETARCH
ARG GH_TOKEN=""

RUN apt-get update && apt-get install -y curl unzip && rm -rf /var/lib/apt/lists/*

# Set up GitHub auth if token provided
RUN if [ -n "$GH_TOKEN" ]; then \
        printf 'machine github.com\n  login x-access-token\n  password %s\n' "$GH_TOKEN" > /root/.netrc && \
        chmod 600 /root/.netrc; \
    fi

# Helper: resolve latest version from GitHub redirect
# Usage: $(gh_version owner/repo) → tag (e.g. "0.68.0" or "v1.2.3")
RUN echo '#!/bin/sh\ncurl --netrc-optional -sL -o /dev/null -w "%{url_effective}" "https://github.com/$1/releases/latest" | sed "s|.*/tag/||"' \
        > /usr/local/bin/gh_version && chmod +x /usr/local/bin/gh_version

RUN mkdir -p /out/bin /out/aws-cli

# difftastic
RUN V=$(gh_version Wilfred/difftastic) && \
    case ${TARGETARCH} in amd64) A="x86_64";; arm64) A="aarch64";; esac && \
    curl --netrc-optional -sL "https://github.com/Wilfred/difftastic/releases/download/${V}/difft-${A}-unknown-linux-gnu.tar.gz" \
        | tar -xz -C /out/bin

# xh
RUN V=$(gh_version ducaale/xh) && \
    case ${TARGETARCH} in amd64) A="x86_64";; arm64) A="aarch64";; esac && \
    curl --netrc-optional -sL "https://github.com/ducaale/xh/releases/download/${V}/xh-${V}-${A}-unknown-linux-musl.tar.gz" \
        | tar -xz --strip-components=1 -C /out/bin --wildcards '*/xh'

# just
RUN V=$(gh_version casey/just) && \
    case ${TARGETARCH} in amd64) A="x86_64";; arm64) A="aarch64";; esac && \
    curl --netrc-optional -sL "https://github.com/casey/just/releases/download/${V}/just-${V}-${A}-unknown-linux-musl.tar.gz" \
        | tar -xz -C /out/bin just

# shfmt
RUN V=$(gh_version mvdan/sh) && \
    case ${TARGETARCH} in amd64) A="amd64";; arm64) A="arm64";; esac && \
    curl --netrc-optional -sL "https://github.com/mvdan/sh/releases/download/${V}/shfmt_${V}_linux_${A}" \
        -o /out/bin/shfmt

# jq
RUN curl --netrc-optional -sL "https://github.com/jqlang/jq/releases/latest/download/jq-linux-${TARGETARCH}" \
        -o /out/bin/jq

# yq
RUN curl --netrc-optional -sL "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${TARGETARCH}" \
        -o /out/bin/yq

# GitHub CLI
RUN V=$(gh_version cli/cli | sed 's/^v//') && \
    curl --netrc-optional -sL "https://github.com/cli/cli/releases/download/v${V}/gh_${V}_linux_${TARGETARCH}.tar.gz" \
        | tar -xz --strip-components=2 -C /out/bin --wildcards '*/bin/gh'

# OpenTofu
RUN V=$(gh_version opentofu/opentofu | sed 's/^v//') && \
    curl --netrc-optional -sL "https://github.com/opentofu/opentofu/releases/download/v${V}/tofu_${V}_linux_${TARGETARCH}.zip" \
        -o /tmp/tofu.zip && \
    unzip -o /tmp/tofu.zip tofu -d /out/bin

# terraform-docs
RUN V=$(gh_version terraform-docs/terraform-docs) && \
    curl --netrc-optional -sL "https://github.com/terraform-docs/terraform-docs/releases/download/${V}/terraform-docs-${V}-linux-${TARGETARCH}.tar.gz" \
        | tar -xz -C /out/bin terraform-docs

# Scalr CLI
RUN V=$(gh_version Scalr/scalr-cli) && \
    curl --netrc-optional -sL "https://github.com/Scalr/scalr-cli/releases/download/${V}/scalr-cli_${V#v}_linux_${TARGETARCH}.zip" \
        -o /tmp/scalr.zip && \
    unzip -o /tmp/scalr.zip scalr -d /out/bin

# AWS CLI v2
RUN case ${TARGETARCH} in amd64) A="x86_64";; arm64) A="aarch64";; esac && \
    curl -sL "https://awscli.amazonaws.com/awscli-exe-linux-${A}.zip" -o /tmp/aws.zip && \
    unzip /tmp/aws.zip -d /tmp && \
    /tmp/aws/install --install-dir /out/aws-cli --bin-dir /out/bin

# Make all binaries executable
RUN chmod +x /out/bin/*


## ---------- Final image ----------
FROM debian:bookworm-slim

ARG USERNAME
ARG USER_UID
ARG TARGETARCH

# Install system packages
RUN apt-get update && apt-get install -y \
    git \
    curl \
    bash \
    ca-certificates \
    unzip \
    zip \
    poppler-utils \
    procps \
    dnsutils \
    wget \
    nano \
    sqlite3 \
    ripgrep \
    fd-find \
    tree \
    shellcheck \
    postgresql-client \
    mariadb-client \
    redis-tools \
    netcat-openbsd \
    iputils-ping \
    sudo \
    apt-transport-https \
    lsb-release \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install PHP from Ondřej Surý's repository (latest stable)
RUN curl -sSLo /tmp/debsuryorg-archive-keyring.deb https://packages.sury.org/debsuryorg-archive-keyring.deb \
    && dpkg -i /tmp/debsuryorg-archive-keyring.deb \
    && rm /tmp/debsuryorg-archive-keyring.deb \
    && echo "deb [signed-by=/usr/share/keyrings/deb.sury.org-php.gpg] https://packages.sury.org/php/ $(lsb_release -sc) main" \
        > /etc/apt/sources.list.d/sury-php.list \
    && apt-get update \
    && PHP_VERSION=$(apt-cache showpkg php-cli | grep -oP '^\d+\.\d+' | sort -V | tail -1) \
    && apt-get install -y \
        php${PHP_VERSION}-cli \
        php${PHP_VERSION}-mbstring \
        php${PHP_VERSION}-xml \
        php${PHP_VERSION}-curl \
        php${PHP_VERSION}-sqlite3 \
        php${PHP_VERSION}-zip \
    && rm -rf /var/lib/apt/lists/*

# Create fd symlink (Debian packages it as fdfind)
RUN ln -s /usr/bin/fdfind /usr/local/bin/fd

# Install uv to system location
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh

# Install Python using uv to system location
RUN UV_PYTHON_INSTALL_DIR=/usr/local uv python install && \
    PYTHON_PATH=$(find /usr/local -name "cpython-*" -type d | head -1) && \
    ln -s "$PYTHON_PATH/bin/python3" /usr/local/bin/python3 && \
    ln -s /usr/local/bin/python3 /usr/local/bin/python

# Copy binaries from fetcher stage
COPY --from=fetcher /out/bin/ /usr/local/bin/
COPY --from=fetcher /out/aws-cli/ /usr/local/aws-cli/

# Pre-seed GitHub SSH host keys
RUN ssh-keyscan github.com >> /etc/ssh/ssh_known_hosts 2>/dev/null

# Create user with matching UID from host (group uses username)
RUN groupadd $USERNAME \
    && useradd --uid $USER_UID --gid $USERNAME -m -s /bin/bash $USERNAME \
    && mkdir -p /home/$USERNAME/dev \
    && chown -R $USERNAME:$USERNAME /home/$USERNAME \
    && echo "$USERNAME ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/agent-sudo \
    && chmod 0440 /etc/sudoers.d/agent-sudo

# Switch to user
USER $USERNAME
WORKDIR /home/$USERNAME

# Install kiro-cli (frequent updates)
RUN case ${TARGETARCH} in \
        amd64) KIRO_ARCH="x86_64" ;; \
        arm64) KIRO_ARCH="aarch64" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl --proto '=https' --tlsv1.2 -sSf \
        "https://desktop-release.q.us-east-1.amazonaws.com/latest/kirocli-${KIRO_ARCH}-linux.zip" \
        -o kirocli.zip && \
    unzip kirocli.zip && \
    ./kirocli/install.sh --force --no-confirm && \
    rm -rf kirocli.zip kirocli

# Install toad as user (frequent updates)
RUN uv tool install batrachian-toad

# Install agent-kit tools as user (frequent updates)
ARG CACHEBUST_AK=1
RUN uv tool install git+https://github.com/simon-downes/agent-kit.git

# Ensure user's tool bin is in PATH
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

CMD ["/bin/bash"]
