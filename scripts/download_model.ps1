<#
Download a HuggingFace model snapshot to a local folder using `huggingface_hub.snapshot_download`.

Usage (PowerShell):
  # public model
  .\scripts\download_model.ps1 -RepoId "Qwen/Qwen2.5-7b-instruct" -TargetDir "models/qwen2.5-7b-instruct"

  # private model (set HF_TOKEN first)
  $env:HF_TOKEN = "hf_xxx"
  .\scripts\download_model.ps1 -RepoId "owner/private-model" -TargetDir "models/private-model" -UseAuth

Notes:
- Requires Python and `huggingface_hub` installed in the active Python environment.
- This script runs a small Python helper that calls `snapshot_download`.
#>

param(
    [Parameter(Mandatory=$true)] [string]$RepoId,
    [Parameter(Mandatory=$true)] [string]$TargetDir,
    [switch]$UseAuth
)

Write-Host "Downloading repo:`t$RepoId`nTarget dir:`t$TargetDir`nUseAuth:`t$UseAuth"

# Ensure target directory exists
New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

# Ensure Python is available
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Error "Python not found in PATH. Install Python 3.8+ and retry."
    exit 1
}

# Ensure huggingface_hub is available
try {
    python -c "import huggingface_hub" 2>$null
} catch {
    Write-Host "Installing huggingface_hub into current Python environment..."
    python -m pip install --upgrade pip
    python -m pip install huggingface_hub
}

$pyScript = @'
import os, sys
from huggingface_hub import snapshot_download
repo = sys.argv[1]
out = sys.argv[2]
token = os.environ.get('HF_TOKEN')
if token:
    snapshot_download(repo_id=repo, local_dir=out, use_auth_token=token)
else:
    snapshot_download(repo_id=repo, local_dir=out)
print('Downloaded', repo, '->', out)
'@

$tmp = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), ([System.Guid]::NewGuid().ToString() + '.py'))
Set-Content -Path $tmp -Value $pyScript -Encoding UTF8

if ($UseAuth) {
    if (-not $env:HF_TOKEN) {
        Write-Error "UseAuth specified but HF_TOKEN environment variable is not set. Set it and retry."
        Remove-Item $tmp -Force
        exit 1
    }
}

python $tmp $RepoId $TargetDir
$rc = $LASTEXITCODE
Remove-Item $tmp -Force
if ($rc -ne 0) { exit $rc }

Write-Host "Model download completed. Files are in $TargetDir"
