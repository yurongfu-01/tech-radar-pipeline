[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# 1. 从 Windows Git Credential Manager 中提取认证 Token
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "git"
$psi.Arguments = "credential fill"
$psi.RedirectStandardInput = $true
$psi.RedirectStandardOutput = $true
$psi.UseShellExecute = $false
$p = [System.Diagnostics.Process]::Start($psi)
$p.StandardInput.Write("protocol=https`nhost=github.com`n`n")
$p.StandardInput.Close()
$output = $p.StandardOutput.ReadToEnd()
$p.WaitForExit()

$token = ""
foreach ($line in $output -split "`n") {
    if ($line -match "^password=(.*)") {
        $token = $matches[1].Trim()
    }
}

if (-not $token) {
    Write-Host "❌ 未能在 Git Credential Manager 中找到 GitHub Token" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Authorization" = "token $token"
    "User-Agent" = "PowerShell-Agent"
    "Accept" = "application/vnd.github.v3+json"
}

# 2. 检查或创建远端仓库 tech-radar-pipeline
$repoName = "tech-radar-pipeline"
Write-Host ">>> 正在连接 GitHub API 检查仓库: $repoName ..." -ForegroundColor Cyan

try {
    $existing = Invoke-RestMethod -Uri "https://api.github.com/repos/yurongfu-01/$repoName" -Headers $headers -Method Get
    Write-Host "✅ 仓库已存在: $($existing.html_url)" -ForegroundColor Green
} catch {
    Write-Host ">>> 仓库尚未创建，正在自动调用 GitHub API 创建..." -ForegroundColor Yellow
    $body = @{
        "name" = $repoName
        "description" = "Universal Tech-Radar & Knowledge Synthesis Pipeline for Antigravity, Claude Code, Codex & Hermes."
        "private" = $false
        "has_issues" = $true
        "has_wiki" = $true
    } | ConvertTo-Json

    try {
        $repo = Invoke-RestMethod -Uri "https://api.github.com/user/repos" -Headers $headers -Method Post -Body $body -ContentType "application/json; charset=utf-8"
        Write-Host "🎉 成功在 GitHub 创建仓库: $($repo.html_url)" -ForegroundColor Green
    } catch {
        Write-Host "❌ 创建仓库失败: $($_.Exception.Message)" -ForegroundColor Red
        exit 1
    }
}

# 3. 执行 Git Push
Write-Host ">>> 正在推送代码至 origin main ..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "🚀 推送成功！项目已公开发布至: https://github.com/yurongfu-01/$repoName" -ForegroundColor Green
} else {
    Write-Host "❌ 推送失败，退出码: $LASTEXITCODE" -ForegroundColor Red
}
