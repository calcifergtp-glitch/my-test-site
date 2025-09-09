# SiteSmith — Static Site + CI/CD (GitHub Pages)

**One-run setup:** Open Windows PowerShell in this folder and run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
.ix-all.ps1 -Repo "calcifergtp-glitch/my-test-site" -SiteUrl "https://calcifergtp-glitch.github.io/my-test-site" -Brand "My Test Blog"
```

Optional flags:
- `-Ga4 "G-XXXXXXX"` (Google Analytics 4 ID)
- `-Plausible "example.com"` (Plausible domain)
- `-CustomDomain "www.example.com"` (also writes CNAME and attempts Pages cname config if `gh` is available)
- `-Token "<YOUR_GITHUB_PAT>"` (PAT with `repo` + `pages:write` scope; otherwise uses `gh` CLI if available)

The script will:
- Verify/generate required structure
- Install Python deps in a `.venv`
- Build site into `site/` with timestamp
- Initialize git, commit, create/attach remote, push
- Install/refresh a **GitHub Actions** workflow that deploys `site/` to **GitHub Pages**
- (If given) set Pages to use Actions and enforce HTTPS (via `gh` CLI), set CNAME
- Print an audit/status summary
