[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$TargetRoot = (Join-Path $HOME ".agents\skills")
)

$ErrorActionPreference = "Stop"
$skillsRoot = Join-Path $RepoRoot "skills"

if (-not (Test-Path -LiteralPath $skillsRoot -PathType Container)) {
    throw "Skills directory not found: $skillsRoot"
}

if (-not (Test-Path -LiteralPath $TargetRoot -PathType Container)) {
    New-Item -ItemType Directory -Path $TargetRoot | Out-Null
}

Get-ChildItem -LiteralPath $skillsRoot -Directory | ForEach-Object {
    $skill = $_
    $target = Join-Path $TargetRoot $skill.Name

    if (Test-Path -LiteralPath $target) {
        $existing = Get-Item -LiteralPath $target -Force
        if ($existing.LinkType -eq "Junction") {
            $existingTarget = @($existing.Target) | Select-Object -First 1
            Write-Host "SKIP  $($skill.Name) -> $existingTarget"
            return
        }
        throw "Target exists and is not a Junction: $target. Back it up and remove it manually first."
    }

    if ($PSCmdlet.ShouldProcess($target, "Create Junction to $($skill.FullName)")) {
        New-Item -ItemType Junction -Path $target -Target $skill.FullName | Out-Null
        Write-Host "LINK  $($skill.Name) -> $($skill.FullName)"
    }
}
