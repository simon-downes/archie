FROM debian:bookworm-slim

# Build args for user creation
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

# Install difftastic
RUN DIFFT_VERSION=$(curl -s https://api.github.com/repos/Wilfred/difftastic/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    case ${TARGETARCH} in \
        amd64) DIFFT_ARCH="x86_64" ;; \
        arm64) DIFFT_ARCH="aarch64" ;; \
    esac && \
    curl -L "https://github.com/Wilfred/difftastic/releases/download/${DIFFT_VERSION}/difft-${DIFFT_ARCH}-unknown-linux-gnu.tar.gz" \
        -o /tmp/difft.tar.gz && \
    tar -xzf /tmp/difft.tar.gz -C /usr/local/bin && \
    chmod +x /usr/local/bin/difft && \
    rm /tmp/difft.tar.gz

# Install xh
RUN XH_VERSION=$(curl -s https://api.github.com/repos/ducaale/xh/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    case ${TARGETARCH} in \
        amd64) XH_ARCH="x86_64" ;; \
        arm64) XH_ARCH="aarch64" ;; \
    esac && \
    curl -L "https://github.com/ducaale/xh/releases/download/${XH_VERSION}/xh-${XH_VERSION}-${XH_ARCH}-unknown-linux-musl.tar.gz" \
        -o /tmp/xh.tar.gz && \
    tar -xzf /tmp/xh.tar.gz -C /tmp && \
    mv /tmp/xh-${XH_VERSION}-${XH_ARCH}-unknown-linux-musl/xh /usr/local/bin/ && \
    chmod +x /usr/local/bin/xh && \
    rm -rf /tmp/xh*

# Install just
RUN JUST_VERSION=$(curl -s https://api.github.com/repos/casey/just/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    case ${TARGETARCH} in \
        amd64) JUST_ARCH="x86_64" ;; \
        arm64) JUST_ARCH="aarch64" ;; \
    esac && \
    curl -L "https://github.com/casey/just/releases/download/${JUST_VERSION}/just-${JUST_VERSION}-${JUST_ARCH}-unknown-linux-musl.tar.gz" \
        -o /tmp/just.tar.gz && \
    tar -xzf /tmp/just.tar.gz -C /usr/local/bin just && \
    chmod +x /usr/local/bin/just && \
    rm /tmp/just.tar.gz

# Install shfmt
RUN SHFMT_VERSION=$(curl -s https://api.github.com/repos/mvdan/sh/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    case ${TARGETARCH} in \
        amd64) SHFMT_ARCH="amd64" ;; \
        arm64) SHFMT_ARCH="arm64" ;; \
    esac && \
    curl -L "https://github.com/mvdan/sh/releases/download/${SHFMT_VERSION}/shfmt_${SHFMT_VERSION}_linux_${SHFMT_ARCH}" \
        -o /usr/local/bin/shfmt && \
    chmod +x /usr/local/bin/shfmt

# Install jq
RUN curl -L "https://github.com/jqlang/jq/releases/latest/download/jq-linux-${TARGETARCH}" \
        -o /usr/local/bin/jq && \
    chmod +x /usr/local/bin/jq

# Install yq
RUN curl -L "https://github.com/mikefarah/yq/releases/latest/download/yq_linux_${TARGETARCH}" \
        -o /usr/local/bin/yq && \
    chmod +x /usr/local/bin/yq

# Install GitHub CLI
RUN GH_VERSION=$(curl -s https://api.github.com/repos/cli/cli/releases/latest | grep '"tag_name"' | cut -d'"' -f4 | sed 's/v//') && \
    curl -L "https://github.com/cli/cli/releases/download/v${GH_VERSION}/gh_${GH_VERSION}_linux_${TARGETARCH}.tar.gz" \
        -o /tmp/gh.tar.gz && \
    tar -xzf /tmp/gh.tar.gz -C /tmp && \
    mv /tmp/gh_${GH_VERSION}_linux_${TARGETARCH}/bin/gh /usr/local/bin/ && \
    rm -rf /tmp/gh*

# Install AWS CLI v2
RUN case ${TARGETARCH} in \
        amd64) AWS_ARCH="x86_64" ;; \
        arm64) AWS_ARCH="aarch64" ;; \
        *) echo "Unsupported architecture: ${TARGETARCH}" && exit 1 ;; \
    esac && \
    curl "https://awscli.amazonaws.com/awscli-exe-linux-${AWS_ARCH}.zip" -o /tmp/awscliv2.zip && \
    unzip /tmp/awscliv2.zip -d /tmp && \
    /tmp/aws/install && \
    rm -rf /tmp/aws*

# Install OpenTofu
RUN TOFU_VERSION=$(curl -s https://api.github.com/repos/opentofu/opentofu/releases/latest | grep '"tag_name"' | cut -d'"' -f4 | sed 's/v//') && \
    curl -L "https://github.com/opentofu/opentofu/releases/download/v${TOFU_VERSION}/tofu_${TOFU_VERSION}_linux_${TARGETARCH}.zip" \
        -o /tmp/tofu.zip && \
    unzip /tmp/tofu.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/tofu && \
    rm /tmp/tofu.zip

# Install terraform-docs
RUN TF_DOCS_VERSION=$(curl -s https://api.github.com/repos/terraform-docs/terraform-docs/releases/latest | grep '"tag_name"' | cut -d'"' -f4) && \
    curl -L "https://github.com/terraform-docs/terraform-docs/releases/download/${TF_DOCS_VERSION}/terraform-docs-${TF_DOCS_VERSION}-linux-${TARGETARCH}.tar.gz" \
        -o /tmp/terraform-docs.tar.gz && \
    tar -xzf /tmp/terraform-docs.tar.gz -C /usr/local/bin terraform-docs && \
    chmod +x /usr/local/bin/terraform-docs && \
    rm /tmp/terraform-docs.tar.gz

# Install Scalr CLI
RUN SCALR_VERSION=$(curl -fsSL https://api.github.com/repos/Scalr/scalr-cli/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")') && \
    curl -fsSL "https://github.com/Scalr/scalr-cli/releases/download/${SCALR_VERSION}/scalr-cli_${SCALR_VERSION#v}_linux_${TARGETARCH}.zip" \
        -o scalr.zip && \
    unzip scalr.zip -d /tmp/scalr && \
    mv /tmp/scalr/scalr /usr/local/bin/scalr && \
    chmod +x /usr/local/bin/scalr && \
    rm -rf scalr.zip /tmp/scalr

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
RUN uv tool install git+https://github.com/simon-downes/agent-kit.git

# Ensure user's tool bin is in PATH
ENV PATH="/home/$USERNAME/.local/bin:$PATH"

CMD ["/bin/bash"]
