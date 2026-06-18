# ============================================================
# CourseArrange 仓库初始化脚本 (PowerShell)
# 用于首次发布到 GitHub / Gitee
# ============================================================

param(
    [string]$GitHubUser = "",
    [string]$GiteeUser = ""
)

$RepoName = "coursearrange"
$ErrorActionPreference = "Stop"

# ---------- 前置检查 ----------
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: git not found, please install Git first" -ForegroundColor Red
    exit 1
}

if (-not $GitHubUser) {
    $GitHubUser = Read-Host "Enter your GitHub username (supplier/your username)"
}
if (-not $GiteeUser) {
    $GiteeUser = Read-Host "Enter your Gitee username (supplier/your username)"
}

Set-Location $PSScriptRoot

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " CourseArrange Repository Initialization" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "GitHub:  $GitHubUser/$RepoName"
Write-Host "Gitee:   $GiteeUser/$RepoName"
Write-Host "============================================" -ForegroundColor Cyan

# ---------- 1. 替换 CODEOWNERS 占位符 ----------
Write-Host ""
Write-Host "[1/5] Updating CODEOWNERS placeholder..." -ForegroundColor Yellow
$codeownersPath = ".github\CODEOWNERS"
if (Test-Path $codeownersPath) {
    $content = Get-Content $codeownersPath -Raw -Encoding UTF8
    $content = $content -replace "@YOUR_GITHUB_USERNAME", "@$GitHubUser"
    Set-Content $codeownersPath -Value $content -Encoding UTF8 -NoNewline
    Write-Host "  -> Replaced @YOUR_GITHUB_USERNAME with @$GitHubUser" -ForegroundColor Green
}

# ---------- 2. 替换 docker-compose.deploy.yml 镜像路径 ----------
Write-Host ""
Write-Host "[2/5] Updating docker-compose.deploy.yml image path..." -ForegroundColor Yellow
$deployPath = "docker-compose.deploy.yml"
if (Test-Path $deployPath) {
    $content = Get-Content $deployPath -Raw -Encoding UTF8
    $content = $content -replace "YOUR_GITHUB_USERNAME", $GitHubUser
    Set-Content $deployPath -Value $content -Encoding UTF8 -NoNewline
    Write-Host "  -> Replaced ghcr.io/YOUR_GITHUB_USERNAME with ghcr.io/$GitHubUser" -ForegroundColor Green
}

# ---------- 3. 初始化 Git 仓库 ----------
Write-Host ""
Write-Host "[3/5] Initializing Git repository..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    git init
    git checkout -b main
    Write-Host "  -> Git repo initialized on branch 'main'" -ForegroundColor Green
} else {
    Write-Host "  -> Git repo already exists, skipping init" -ForegroundColor DarkGray
}

# ---------- 4. 添加远程仓库 ----------
Write-Host ""
Write-Host "[4/5] Adding remote repositories..." -ForegroundColor Yellow
$githubUrl = "git@github.com:${GitHubUser}/${RepoName}.git"
$giteeUrl = "git@gitee.com:${GiteeUser}/${RepoName}.git"

$remotes = git remote 2>$null
if ($remotes -match "origin") {
    git remote set-url origin $githubUrl
    Write-Host "  -> origin -> $githubUrl" -ForegroundColor Green
} else {
    git remote add origin $githubUrl
    Write-Host "  -> origin added -> $githubUrl" -ForegroundColor Green
}

if ($remotes -match "gitee") {
    git remote set-url gitee $giteeUrl
    Write-Host "  -> gitee -> $giteeUrl" -ForegroundColor Green
} else {
    git remote add gitee $giteeUrl
    Write-Host "  -> gitee added -> $giteeUrl" -ForegroundColor Green
}

# ---------- 5. 首次提交 ----------
Write-Host ""
Write-Host "[5/5] Creating initial commit..." -ForegroundColor Yellow
git add -A
git status --short | Select-Object -First 20
Write-Host ""
Write-Host "  The above files will be committed." -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Proceed with commit? [y/N]"
if ($confirm -eq "y" -or $confirm -eq "Y") {
    git commit -m "feat: initial release - CourseArrange v1.0.0`n`n- AGPL-3.0 + Commercial dual licensing`n- Cython compilation for critical modules`n- RSA + HMAC license verification system`n- Supplier discovery mechanism for seamless URL updates`n- Docker-only deployment with multi-stage builds`n- Premium feature access control (backend + frontend)`n- Nginx anti-crawling and rate limiting`n- GitHub Actions CI/CD with Trivy security scanning`n- Gitee mirror sync"

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host " Initial commit created successfully!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Create repositories on GitHub and Gitee"
    Write-Host "  2. Push to GitHub:  git push -u origin main"
    Write-Host "  3. Push to Gitee:   git push -u gitee main"
    Write-Host "  4. Set GitHub Secrets for CI/CD (see guide)"
    Write-Host ""
} else {
    Write-Host "  Commit cancelled. Run 'git commit' manually when ready." -ForegroundColor DarkGray
}