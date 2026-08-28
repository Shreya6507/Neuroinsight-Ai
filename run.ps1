$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot "venv\Scripts\python.exe"
& $python (Join-Path $projectRoot "app.py")
