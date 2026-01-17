# setup_claude_zai.ps1
$ErrorActionPreference = "Stop"

Write-Host "🚀 Configuring Claude Code for Windows..."

# 1. Check Node
try {
    $nodeVersion = node -v
    Write-Host "✅ Node.js found: $nodeVersion"
}
catch {
    Write-Error "❌ Node.js is not installed or not in PATH."
    exit 1
}

# 2. Install/Update Claude Code
Write-Host "🔹 Installing/Updating @anthropic-ai/claude-code..."
npm install -g @anthropic-ai/claude-code

# 3. Configure Onboarding (.claude.json)
$claudeConfigPath = "$env:USERPROFILE\.claude.json"
$configContent = @{ hasCompletedOnboarding = $true }
$configContent | ConvertTo-Json | Out-File $claudeConfigPath -Encoding utf8
Write-Host "✅ Onboarding skipped configuration updated."

# 4. Ask for API Key
$apiKeyUrl = "https://z.ai/manage-apikey/apikey-list"
Write-Host "   You can get your API key from: $apiKeyUrl"
$apiKey = Read-Host "🔑 Please enter your Z.AI API key"

if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-Error "❌ API key cannot be empty."
    exit 1
}

# 5. Write settings.json
$settingsDir = "$env:USERPROFILE\.claude"
if (!(Test-Path $settingsDir)) {
    New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
}

$settingsPath = "$settingsDir\settings.json"
$currentSettings = @{}
if (Test-Path $settingsPath) {
    try {
        $content = Get-Content $settingsPath -Raw -ErrorAction SilentlyContinue
        if ($content) {
            $currentSettings = $content | ConvertFrom-Json
        }
    }
    catch {
        Write-Warning "Existing settings.json could not be parsed, starting fresh."
    }
}

# Ensure env object exists
if (-not ($currentSettings | Get-Member -Name "env" -ErrorAction SilentlyContinue)) {
    $currentSettings | Add-Member -MemberType NoteProperty -Name "env" -Value @{}
}

# Update env values
$currentSettings.env.ANTHROPIC_AUTH_TOKEN = $apiKey
$currentSettings.env.ANTHROPIC_BASE_URL = "https://api.z.ai/api/anthropic"
$currentSettings.env.API_TIMEOUT_MS = "3000000"
$currentSettings.env.CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC = 1

$currentSettings | ConvertTo-Json -Depth 5 | Out-File $settingsPath -Encoding utf8

Write-Host "✅ Claude Code configured successfully at $settingsPath"
Write-Host "🚀 You can now start using Claude Code with: claude"
