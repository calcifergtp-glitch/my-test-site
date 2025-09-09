# fix-all.ps1 — ASCII-safe, no emojis, no smart quotes
param(
  [string]$Repo = "calcifergtp-glitch/my-test-site",
  [string]$SiteUrl = "https://calcifergtp-glitch.github.io/my-test-site",
  [string]$Brand = "My Test Blog",
  [string]$Ga4 = "",
  [string]$Plausible = "",
  [string]$CustomDomain = "",
  [string]$Token = ""
)

$ErrorActionPreference = "Stop"

function Log($msg){ Write-Host ("[{0}] {1}" -f (Get-Date -Format HH:mm:ss), $msg) -ForegroundColor Cyan }
function Warn($msg){ Write-Warning $msg }
function Die($msg){ Write-Error $msg; exit 1 }

# Make sure we are in the script folder if run from elsewhere
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

# 1) Ensure project structure exists / restore defaults from script folder if present
$required = @(
  "build.py",
  "requirements.txt",
  "templates/base.html",
  "templates/index.html",
  "templates/post.html",
  "templates/page.html",
  "templates/category.html",
  "templates/tag.html",
  "templates/pages/about.html",
  "templates/pages/privacy.html",
  "templates/pages/disclosure.html",
  "templates/pages/contact.html",
  "content/posts",
  "ssg/utils.py",
  "ssg/templates.py",
  "ssg/content.py",
  "ssg/monetize.py",
  "ssg/analytics.py",
  ".github/workflows/deploy.yml"
)

foreach($p in $required){
  if(-not (Test-Path -Path $p)){
    Warn "Missing $p — creating or restoring"
    $src = Join-Path -Path $PSScriptRoot -ChildPath $p
    if(Test-Path -Path $src){
      $parent = Split-Path -Parent $p
      if($parent){ New-Item -ItemType Directory -Force -Path $parent | Out-Null }
      Copy-Item -Path $src -Destination $p -Force
    } else {
      if($p.EndsWith("/")){
        New-Item -ItemType Directory -Force -Path $p | Out-Null
      } else {
        $parent = Split-Path -Parent $p
        if($parent){ New-Item -ItemType Directory -Force -Path $parent | Out-Null }
        New-Item -ItemType File -Force -Path $p | Out-Null
      }
    }
  }
}

# 2) Python env & local build
# Try a few python launchers
$python = ""
foreach($c in @("py -3","py","python","python3")){
  try{
    & $c --version *>$null
    if($LASTEXITCODE -eq 0){ $python = $c; break }
  } catch {}
}
if(-not $python){ Die "Python 3.x not found. Install from https://www.python.org/downloads/ and re-run." }

if(-not (Test-Path ".venv")){
  Log "Creating virtual environment"
  & $python -m venv .venv
}
$venvPython = Join-Path ".venv" "Scripts/python.exe"
if(-not (Test-Path $venvPython)){ Die "Virtual environment python not found at $venvPython" }

Log "Upgrading pip and installing requirements"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

# Build site
$env:GA4_ID = $Ga4
$env:PLAUSIBLE_DOMAIN = $Plausible
$env:CUSTOM_DOMAIN = $CustomDomain

Log "Building site"
& $venvPython build.py --site_url $SiteUrl --brand $Brand
if($LASTEXITCODE -ne 0){ Die "Local build failed" }

if(-not (Test-Path "site/index.html")){ Die "site/index.html missing after build" }

# 3) Git init and push
if(-not (Test-Path ".git")){
  Log "Initializing git repository"
  git init | Out-Null
  git branch -M main
  git config core.autocrlf true
}

git add -A
try{ git commit -m "sync: ensure all files included" | Out-Null } catch {}

$owner,$name = $Repo.Split("/")
if(-not (git remote | Select-String -SimpleMatch "origin")){
  Log "Adding remote origin"
  git remote add origin ("https://github.com/{0}.git" -f $Repo)
}

# Create remote repo if it does not exist
$needCreate = $false
try{
  git ls-remote --exit-code origin | Out-Null
} catch {
  $needCreate = $true
}
if($needCreate){
  Warn "Remote not reachable; creating $Repo"
  if($Token){
    $hdr = @{ Authorization = "token $Token"; Accept = "application/vnd.github+json" }
    $body = @{ name = $name } | ConvertTo-Json
    Invoke-RestMethod -Headers $hdr -Method POST -Body $body -Uri "https://api.github.com/user/repos" | Out-Null
  } elseif(Get-Command gh -ErrorAction SilentlyContinue){
    gh repo create $Repo --private --confirm | Out-Null
  } else {
    Die "Remote missing and neither Token nor gh CLI available."
  }
}

# Push with rebase fallback
try{
  Log "Pushing to origin main"
  git push -u origin main
} catch {
  Warn "Push failed; attempting fetch + rebase"
  git fetch origin main
  git rebase origin/main
  git push -u origin main
}

# Ensure workflow is up to date and pushed
git add -A
try{ git commit -m "ci: add or refresh GitHub Pages deploy workflow" | Out-Null } catch {}
try{ git push } catch {
  Warn "Second push failed; attempting fetch + rebase"
  git fetch origin main
  git rebase origin/main
  git push
}

# 4) Configure Pages via gh if available
if(Get-Command gh -ErrorAction SilentlyContinue){
  try{
    Log "Configuring GitHub Pages to use Actions"
    gh api -X PUT ("repos/{0}/pages" -f $Repo) -f "build_type=workflow" | Out-Null
  } catch {}
  if($CustomDomain){
    try{
      Log "Setting Pages CNAME to $CustomDomain"
      gh api -X PUT ("repos/{0}/pages" -f $Repo) -F ("cname={0}" -f $CustomDomain) | Out-Null
    } catch {}
  }
} else {
  Warn "gh CLI not found; verify Settings -> Pages is set to GitHub Actions and HTTPS enforced."
}

# 5) Final status
Write-Host ""
Write-Host "==================== STATUS ====================" -ForegroundColor Green
Write-Host "Local build completed; output in /site"
Write-Host ("Git repo pushed to https://github.com/{0}" -f $Repo)
Write-Host "GitHub Actions workflow present: .github/workflows/deploy.yml"
if($CustomDomain){ Write-Host ("Custom domain requested: set DNS CNAME to {0}.github.io and enable HTTPS" -f $owner) }
Write-Host ("Live URL after Actions finishes: {0}" -f $SiteUrl)
Write-Host "================================================"

