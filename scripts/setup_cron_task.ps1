# ==============================================================================
# Windows 计划任务一键配置脚本 (Setup Daily Scheduled Task)
# 每日自动运行 TechRadar 扫描最新行业讲座并研读归档至 Obsidian
# ==============================================================================

$TaskName = "TechRadar-Daily-Job"
$ScriptDir = Split-Path -Parent $PSScriptRoot
$PythonPath = (Get-Command python).Source

Write-Host ">>> 正在注册 Windows 定时任务: $TaskName ..." -ForegroundColor Cyan
Write-Host ">>> 工作目录: $ScriptDir" -ForegroundColor Gray
Write-Host ">>> Python 解释器: $PythonPath" -ForegroundColor Gray

$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "cli.py run --max-items 2" -WorkingDirectory $ScriptDir
$Trigger = New-ScheduledTaskTrigger -Daily -At "08:00AM"
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Daily TechRadar Automated Pipeline" -Force

Write-Host "✅ 成功注册计划任务！每天早晨 08:00 将自动扫描并提炼最新权威讲座与博客。" -ForegroundColor Green
