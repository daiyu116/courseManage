#!/usr/bin/env bash
# ============================================================
# courseManage 仓库初始化脚本
# 用于首次发布到 GitHub / Gitee
# ============================================================
set -euo pipefail

# ---------- 配置区 ----------
GITHUB_USER=""       # 填入你的 GitHub 用户名
GITEE_USER=""        # 填入你的 Gitee 用户名
REPO_NAME="courseManage"

# ---------- 前置检查 ----------
command -v git >/dev/null 2>&1 || { echo "ERROR: git not found"; exit 1; }

if [ -z "$GITHUB_USER" ]; then
    read -rp "Enter your GitHub username: " GITHUB_USER
fi
if [ -z "$GITEE_USER" ]; then
    read -rp "Enter your Gitee username: " GITEE_USER
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================"
echo " courseManage Repository Initialization"
echo "============================================"
echo "GitHub:  $GITHUB_USER/$REPO_NAME"
echo "Gitee:   $GITEE_USER/$REPO_NAME"
echo "============================================"

# ---------- 1. 替换 CODEOWNERS 占位符 ----------
echo ""
echo "[1/4] Updating CODEOWNERS placeholder..."
if [ -f ".github/CODEOWNERS" ]; then
    sed -i "s/@YOUR_GITHUB_USERNAME/@$GITHUB_USER/g" .github/CODEOWNERS
    echo "  -> Replaced @YOUR_GITHUB_USERNAME with @$GITHUB_USER"
fi

# ---------- 2. 替换 docker-compose.deploy.yml 镜像路径 ----------
echo ""
echo "[2/4] Updating docker-compose.deploy.yml image path..."
if [ -f "docker-compose.deploy.yml" ]; then
    sed -i "s/YOUR_GITHUB_USERNAME/$GITHUB_USER/g" docker-compose.deploy.yml
    echo "  -> Replaced ghcr.io/YOUR_GITHUB_USERNAME with ghcr.io/$GITHUB_USER"
fi

# ---------- 3. 初始化 Git 仓库 ----------
echo ""
echo "[3/4] Initializing Git repository..."
if [ ! -d ".git" ]; then
    git init
    git checkout -b main
    echo "  -> Git repo initialized on branch 'main'"
else
    echo "  -> Git repo already exists, skipping init"
fi

# ---------- 4. 添加远程仓库 + 首次提交 ----------
echo ""
echo "[4/4] Adding remote repositories and committing..."
GITHUB_URL="git@github.com:$GITHUB_USER/$REPO_NAME.git"
GITEE_URL="git@gitee.com:$GITEE_USER/$REPO_NAME.git"

if git remote | grep -q "^origin$"; then
    git remote set-url origin "$GITHUB_URL"
    echo "  -> origin -> $GITHUB_URL"
else
    git remote add origin "$GITHUB_URL"
    echo "  -> origin added -> $GITHUB_URL"
fi

if git remote | grep -q "^gitee$"; then
    git remote set-url gitee "$GITEE_URL"
    echo "  -> gitee -> $GITEE_URL"
else
    git remote add gitee "$GITEE_URL"
    echo "  -> gitee added -> $GITEE_URL"
fi

git add -A
git status --short | head -20
echo ""
echo "  The above files will be committed."
echo ""
read -rp "Proceed with commit? [y/N] " CONFIRM
if [ "$CONFIRM" = "y" ] || [ "$CONFIRM" = "Y" ]; then
    git commit -m "feat: initial release - courseManage v1.0.0

- AGPL-3.0 + Commercial dual licensing
- Cython compilation for critical modules
- RSA + HMAC license verification system
- Supplier discovery mechanism for seamless URL updates
- Docker-only deployment with multi-stage builds
- Premium feature access control (backend + frontend)
- Nginx anti-crawling and rate limiting
- GitHub Actions CI/CD with Trivy security scanning
- Gitee mirror sync"

    echo ""
    echo "============================================"
    echo " Initial commit created successfully!"
    echo "============================================"
    echo ""
    echo "Next steps:"
    echo "  1. Create repositories on GitHub and Gitee"
    echo "  2. Push to GitHub:  git push -u origin main"
    echo "  3. Push to Gitee:   git push -u gitee main"
    echo "  4. Set GitHub Secrets for CI/CD"
    echo ""
else
    echo "  Commit cancelled. Run 'git commit' manually when ready."
fi