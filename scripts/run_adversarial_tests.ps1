$ErrorActionPreference = "Continue"
$overallPass = $true
$lines = [System.Collections.Generic.List[string]]::new()
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

function L {
    param([string]$Message = "")
    $normalizedMessage = $Message -replace "`0", "" -replace "`r", ""
    foreach ($messageLine in ($normalizedMessage -split "`n", 0, "SimpleMatch")) {
        $cleanLine = $messageLine -replace "[ `t]+$", ""
        $lines.Add($cleanLine)
        Write-Host $cleanLine
    }
}

function S {
    param([string]$Title)
    L
    L "================================================================"
    L $Title
    L "================================================================"
}

function Invoke-ChildPowerShell {
    param(
        [string]$WorkingDirectory,
        [string]$ScriptName
    )

    $powerShellPath = (Get-Command powershell.exe -ErrorAction Stop).Source
    $processInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $processInfo.FileName = $powerShellPath
    $processInfo.Arguments = "-NonInteractive -NoProfile -ExecutionPolicy Bypass -File `"$ScriptName`""
    $processInfo.WorkingDirectory = $WorkingDirectory
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $processInfo
    [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()

    [pscustomobject]@{
        Command = "powershell.exe -NonInteractive -NoProfile -ExecutionPolicy Bypass -File `"$ScriptName`""
        ExitCode = $process.ExitCode
        Output = (($stdoutTask.Result, $stderrTask.Result) -join "`n").TrimEnd()
    }
}

function Invoke-ChildBash {
    param(
        [string]$WorkingDirectory,
        [string]$BashPath,
        [string]$Arguments
    )

    $processInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $processInfo.FileName = $BashPath
    $processInfo.Arguments = $Arguments
    $processInfo.WorkingDirectory = $WorkingDirectory
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true

    $process = [System.Diagnostics.Process]::new()
    $process.StartInfo = $processInfo
    [void]$process.Start()
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $process.WaitForExit()

    [pscustomobject]@{
        ExitCode = $process.ExitCode
        Output = (($stdoutTask.Result, $stderrTask.Result) -join "`n").TrimEnd()
    }
}

function Test-TrackedPathRejection {
    param(
        [string]$Label,
        [string]$RelativePath,
        [string]$ExpectedText
    )

    S $Label
    $tempRoot = [IO.Path]::Combine([IO.Path]::GetTempPath(), "micro1_trace_gate_" + [guid]::NewGuid().ToString("N"))
    try {
        New-Item -ItemType Directory -Path $tempRoot -ErrorAction Stop | Out-Null
        Copy-Item -LiteralPath (Join-Path $repoRoot "verify.ps1") -Destination (Join-Path $tempRoot "verify.ps1") -ErrorAction Stop
        $targetPath = Join-Path $tempRoot ($RelativePath -replace '/', [IO.Path]::DirectorySeparatorChar)
        New-Item -ItemType Directory -Path (Split-Path $targetPath) -Force -ErrorAction Stop | Out-Null
        Set-Content -LiteralPath $targetPath -Value "synthetic test marker" -Encoding ASCII

        Push-Location $tempRoot
        try {
            $initOutput = git init -q 2>&1
            $initExit = $LASTEXITCODE
            $addOutput = git add -- $RelativePath 2>&1
            $addExit = $LASTEXITCODE
        } finally {
            Pop-Location
        }

        L "Setup command: git init -q"
        L ("Setup exit   : " + $initExit)
        $initOutput | ForEach-Object { L "$_" }
        L ("Setup command: git add -- " + $RelativePath)
        L ("Setup exit   : " + $addExit)
        $addOutput | ForEach-Object { L "$_" }

        if ($initExit -ne 0 -or $addExit -ne 0) {
            L "TEST WRAPPER: FAIL (temporary repository setup failed)"
            return $false
        }

        $result = Invoke-ChildPowerShell -WorkingDirectory $tempRoot -ScriptName "verify.ps1"
        L ("Command      : " + $result.Command)
        L ("Process exit : " + $result.ExitCode)
        L "--- stdout/stderr ---"
        $result.Output -split "`r?`n" | ForEach-Object { L "$_" }
        L "--- end ---"

        $expectedFound = ($result.Output | Select-String ([regex]::Escape($ExpectedText))).Count -gt 0
        $composeSeen = ($result.Output | Select-String "Compose Config Isolation").Count -gt 0
        $passed = $result.ExitCode -ne 0 -and $expectedFound -and -not $composeSeen
        L ("  non-zero exit       : " + $(if ($result.ExitCode -ne 0) { "PASS" } else { "FAIL" }))
        L ("  rejected path shown : " + $(if ($expectedFound) { "PASS" } else { "FAIL" }))
        L ("  Compose not started : " + $(if (-not $composeSeen) { "PASS" } else { "FAIL" }))
        L ("TEST WRAPPER: " + $(if ($passed) { "PASS" } else { "FAIL" }))
        return $passed
    } finally {
        if (Test-Path -LiteralPath $tempRoot) {
            Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction Stop
        }
    }
}

S "ADVERSARIAL EVIDENCE FILE"
L ("Timestamp : " + (Get-Date -Format "yyyy-MM-ddTHH:mm:sszzz"))
L ("Workdir   : " + $repoRoot)

$commitRaw = git rev-parse HEAD 2>&1
$commitExit = $LASTEXITCODE
L "Command    : git rev-parse HEAD"
L ("Exit       : " + $commitExit)
$commitRaw | ForEach-Object { L "$_" }
if ($commitExit -ne 0) { $overallPass = $false }

$statusRaw = git status --short 2>&1
$statusExit = $LASTEXITCODE
L "Command    : git status --short"
L ("Exit       : " + $statusExit)
$statusRaw | ForEach-Object { L "$_" }
if ($statusExit -ne 0) { $overallPass = $false }

L
L "--- SHA-256 Hashes ---"
$filesToHash = @(
    ".dockerignore",
    ".env.example",
    ".gitattributes",
    ".gitignore",
    "verify.ps1",
    "verify.sh",
    "docker-compose.yml",
    "Dockerfile",
    "requirements.lock",
    "requirements-dev.txt",
    "scripts\verify_container_security.sh",
    "scripts\run_adversarial_tests.ps1",
    "src\main.py",
    "src\utils\human_checkpoint.py",
    "src\utils\logger.py",
    "tests\test_environment.py",
    "tests\test_human_checkpoint.py",
    "tests\test_logger.py"
)
foreach ($fileToHash in $filesToHash) {
    try {
        $hashObject = Get-FileHash -LiteralPath $fileToHash -Algorithm SHA256 -ErrorAction Stop
        L ("HASH EXIT 0: $($hashObject.Hash)  $fileToHash")
    } catch {
        L ("HASH EXIT 1: $fileToHash")
        L $_.Exception.Message
        $overallPass = $false
    }
}
L "--- end hashes ---"

S "TEST A: PowerShell Git negative-path test"
$tempDir = [IO.Path]::Combine([IO.Path]::GetTempPath(), "micro1_nogit_" + [guid]::NewGuid().ToString("N"))
try {
    New-Item -ItemType Directory -Path $tempDir -ErrorAction Stop | Out-Null
    Copy-Item -LiteralPath (Join-Path $repoRoot "verify.ps1") -Destination (Join-Path $tempDir "verify.ps1") -ErrorAction Stop
    $negativeResult = Invoke-ChildPowerShell -WorkingDirectory $tempDir -ScriptName "verify.ps1"
} finally {
    if (Test-Path -LiteralPath $tempDir) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction Stop
    }
}
L ("Command      : " + $negativeResult.Command)
L ("Working dir  : " + $tempDir)
L ("Process exit : " + $negativeResult.ExitCode)
L "--- stdout/stderr ---"
$negativeResult.Output -split "`r?`n" | ForEach-Object { L "$_" }
L "--- end ---"
$gitFailureFound = ($negativeResult.Output | Select-String "\[FAIL\] Git command failed").Count -gt 0
$composeSeen = ($negativeResult.Output | Select-String "Compose Config Isolation").Count -gt 0
$testAPass = $negativeResult.ExitCode -ne 0 -and $gitFailureFound -and -not $composeSeen
L ("  non-zero exit       : " + $(if ($negativeResult.ExitCode -ne 0) { "PASS" } else { "FAIL" }))
L ("  Git failure marker  : " + $(if ($gitFailureFound) { "PASS" } else { "FAIL" }))
L ("  Compose not started : " + $(if (-not $composeSeen) { "PASS" } else { "FAIL" }))
L ("TEST A WRAPPER: " + $(if ($testAPass) { "PASS" } else { "FAIL" }))
if (-not $testAPass) { $overallPass = $false }

$traceBypassPass = Test-TrackedPathRejection `
    -Label "TEST B: Reject tracked traces/raw/README.md" `
    -RelativePath "traces/raw/README.md" `
    -ExpectedText "traces/raw/README.md"
if (-not $traceBypassPass) { $overallPass = $false }

$trajectoryBypassPass = Test-TrackedPathRejection `
    -Label "TEST C: Reject tracked trajectories/raw/README.md" `
    -RelativePath "trajectories/raw/README.md" `
    -ExpectedText "trajectories/raw/README.md"
if (-not $trajectoryBypassPass) { $overallPass = $false }

S "TEST D: Three-provider Compose sentinel test"
$hadOpenAI = Test-Path Env:\OPENAI_API_KEY
$hadAnthropic = Test-Path Env:\ANTHROPIC_API_KEY
$hadGemini = Test-Path Env:\GEMINI_API_KEY
$originalOpenAI = $env:OPENAI_API_KEY
$originalAnthropic = $env:ANTHROPIC_API_KEY
$originalGemini = $env:GEMINI_API_KEY
try {
    $env:OPENAI_API_KEY = "SENTINEL_OPENAI"
    $env:ANTHROPIC_API_KEY = "SENTINEL_ANTHROPIC"
    $env:GEMINI_API_KEY = "SENTINEL_GEMINI"
    $configOutput = docker compose -f docker-compose.yml config 2>&1
    $configExit = $LASTEXITCODE
} finally {
    if ($hadOpenAI) { $env:OPENAI_API_KEY = $originalOpenAI } else { Remove-Item Env:\OPENAI_API_KEY -ErrorAction SilentlyContinue }
    if ($hadAnthropic) { $env:ANTHROPIC_API_KEY = $originalAnthropic } else { Remove-Item Env:\ANTHROPIC_API_KEY -ErrorAction SilentlyContinue }
    if ($hadGemini) { $env:GEMINI_API_KEY = $originalGemini } else { Remove-Item Env:\GEMINI_API_KEY -ErrorAction SilentlyContinue }
}
$openAIRestored = (Test-Path Env:\OPENAI_API_KEY) -eq $hadOpenAI -and (-not $hadOpenAI -or $env:OPENAI_API_KEY -ceq $originalOpenAI)
$anthropicRestored = (Test-Path Env:\ANTHROPIC_API_KEY) -eq $hadAnthropic -and (-not $hadAnthropic -or $env:ANTHROPIC_API_KEY -ceq $originalAnthropic)
$geminiRestored = (Test-Path Env:\GEMINI_API_KEY) -eq $hadGemini -and (-not $hadGemini -or $env:GEMINI_API_KEY -ceq $originalGemini)
$openAIAbsent = ($configOutput | Select-String "OPENAI").Count -eq 0
$anthropicAbsent = ($configOutput | Select-String "ANTHROPIC").Count -eq 0
$geminiAbsent = ($configOutput | Select-String "GEMINI").Count -eq 0
L "Command      : docker compose -f docker-compose.yml config (with three harmless sentinel variables)"
L ("Process exit : " + $configExit)
$configOutput | ForEach-Object { L "$_" }
L ("  OPENAI absent          : " + $(if ($openAIAbsent) { "PASS" } else { "FAIL" }))
L ("  ANTHROPIC absent       : " + $(if ($anthropicAbsent) { "PASS" } else { "FAIL" }))
L ("  GEMINI absent          : " + $(if ($geminiAbsent) { "PASS" } else { "FAIL" }))
L ("  OPENAI env restored    : " + $(if ($openAIRestored) { "PASS" } else { "FAIL" }))
L ("  ANTHROPIC env restored : " + $(if ($anthropicRestored) { "PASS" } else { "FAIL" }))
L ("  GEMINI env restored    : " + $(if ($geminiRestored) { "PASS" } else { "FAIL" }))
$testDPass = $configExit -eq 0 -and $openAIAbsent -and $anthropicAbsent -and $geminiAbsent -and $openAIRestored -and $anthropicRestored -and $geminiRestored
L ("TEST D WRAPPER: " + $(if ($testDPass) { "PASS" } else { "FAIL" }))
if (-not $testDPass) { $overallPass = $false }

$volumeArgument = "$repoRoot\scripts\verify_container_security.sh:/app/verify_container_security.sh:ro"

S "DOCKER PRECONDITION: Build current image"
$buildOutput = docker compose -f docker-compose.yml build --no-cache 2>&1
$buildExit = $LASTEXITCODE
L "Command      : docker compose -f docker-compose.yml build --no-cache"
L ("Process exit : " + $buildExit)
$buildOutput | ForEach-Object { L "$_" }
$dockerBuildPass = $buildExit -eq 0
L ("BUILD PRECONDITION: " + $(if ($dockerBuildPass) { "PASS" } else { "FAIL" }))
if (-not $dockerBuildPass) { $overallPass = $false }

if ($dockerBuildPass) {
S "TEST E: Security prohibited-path matrix"
$prohibitedCommand = "mkdir -p '/app/folder with space' '/app/.git' '/app/__pycache__' '/app/.pytest_cache' '/app/traces/raw/t1' '/app/trajectories/raw/t1' && touch '/app/folder with space/.env' '/app/.env.staging' '/app/test.pyc' && sh /app/verify_container_security.sh"
$prohibitedOutput = docker run --rm -v $volumeArgument micro1-challenge-phase0:latest sh -c $prohibitedCommand 2>&1
$prohibitedExit = $LASTEXITCODE
L ("Command      : docker run --rm -v `"$volumeArgument`" micro1-challenge-phase0:latest sh -c `"$prohibitedCommand`"")
L ("Scanner exit : " + $prohibitedExit)
$prohibitedOutput | ForEach-Object { L "$_" }
$requiredPatterns = @("folder with space.*\.env", "\.env\.staging", "\.git", "__pycache__", "test\.pyc", "\.pytest_cache", "traces/raw", "trajectories/raw")
$allProhibitedFound = $true
foreach ($requiredPattern in $requiredPatterns) {
    if (($prohibitedOutput | Select-String $requiredPattern).Count -eq 0) { $allProhibitedFound = $false }
}
$testEPass = $prohibitedExit -ne 0 -and $allProhibitedFound
L ("  all prohibited categories reported : " + $(if ($allProhibitedFound) { "PASS" } else { "FAIL" }))
L ("TEST E WRAPPER: " + $(if ($testEPass) { "PASS" } else { "FAIL" }))
if (-not $testEPass) { $overallPass = $false }

S "TEST F: Security allowed lookalikes"
$allowedCommand = "mkdir -p '/app/traces/raw_backup' '/app/trajectories/raw_notes' && sh /app/verify_container_security.sh"
$allowedOutput = docker run --rm -v $volumeArgument micro1-challenge-phase0:latest sh -c $allowedCommand 2>&1
$allowedExit = $LASTEXITCODE
L ("Command      : docker run --rm -v `"$volumeArgument`" micro1-challenge-phase0:latest sh -c `"$allowedCommand`"")
L ("Scanner exit : " + $allowedExit)
$allowedOutput | ForEach-Object { L "$_" }
$testFPass = $allowedExit -eq 0 -and ($allowedOutput | Select-String "\[PASS\] Container security assertion passed").Count -gt 0
L ("TEST F WRAPPER: " + $(if ($testFPass) { "PASS" } else { "FAIL" }))
if (-not $testFPass) { $overallPass = $false }

S "TEST G: Security find failure"
$findFailureCommand = "SCAN_ROOT=/app/does-not-exist sh /app/verify_container_security.sh"
$findFailureOutput = docker run --rm -v $volumeArgument micro1-challenge-phase0:latest sh -c $findFailureCommand 2>&1
$findFailureExit = $LASTEXITCODE
L ("Command      : docker run --rm -v `"$volumeArgument`" micro1-challenge-phase0:latest sh -c `"$findFailureCommand`"")
L ("Scanner exit : " + $findFailureExit)
$findFailureOutput | ForEach-Object { L "$_" }
$findFailureMarker = ($findFailureOutput | Select-String "\[FAIL\] Container filesystem scan failed").Count -gt 0
$testGPass = $findFailureExit -ne 0 -and $findFailureMarker
L ("TEST G WRAPPER: " + $(if ($testGPass) { "PASS" } else { "FAIL" }))
if (-not $testGPass) { $overallPass = $false }

S "TEST H: Security root execution"
$rootOutput = docker run --rm -u 0 -v $volumeArgument micro1-challenge-phase0:latest sh /app/verify_container_security.sh 2>&1
$rootExit = $LASTEXITCODE
L ("Command      : docker run --rm -u 0 -v `"$volumeArgument`" micro1-challenge-phase0:latest sh /app/verify_container_security.sh")
L ("Scanner exit : " + $rootExit)
$rootOutput | ForEach-Object { L "$_" }
$rootMarker = ($rootOutput | Select-String "Container is running as root").Count -gt 0
$testHPass = $rootExit -ne 0 -and $rootMarker
L ("TEST H WRAPPER: " + $(if ($testHPass) { "PASS" } else { "FAIL" }))
if (-not $testHPass) { $overallPass = $false }

S "TEST I: Normal security scan"
$normalOutput = docker run --rm -v $volumeArgument micro1-challenge-phase0:latest sh /app/verify_container_security.sh 2>&1
$normalExit = $LASTEXITCODE
L ("Command      : docker run --rm -v `"$volumeArgument`" micro1-challenge-phase0:latest sh /app/verify_container_security.sh")
L ("Scanner exit : " + $normalExit)
$normalOutput | ForEach-Object { L "$_" }
$normalMarker = ($normalOutput | Select-String "\[PASS\] Container security assertion passed").Count -gt 0
$testIPass = $normalExit -eq 0 -and $normalMarker
L ("TEST I WRAPPER: " + $(if ($testIPass) { "PASS" } else { "FAIL" }))
if (-not $testIPass) { $overallPass = $false }
} else {
    L "TESTS E-I STATUS: NOT RUN - current image build precondition failed."
}

S "TEST J: Git mode and EOL checks"
$stageOutput = git ls-files --stage -- verify.sh scripts/verify_container_security.sh scripts/PHASE_GATE.sh 2>&1
$stageExit = $LASTEXITCODE
$eolOutput = git ls-files --eol -- verify.sh scripts/verify_container_security.sh scripts/PHASE_GATE.sh .gitattributes 2>&1
$eolExit = $LASTEXITCODE
L "Command      : git ls-files --stage -- verify.sh scripts/verify_container_security.sh scripts/PHASE_GATE.sh"
L ("Process exit : " + $stageExit)
$stageOutput | ForEach-Object { L "$_" }
L "Command      : git ls-files --eol -- verify.sh scripts/verify_container_security.sh scripts/PHASE_GATE.sh .gitattributes"
L ("Process exit : " + $eolExit)
$eolOutput | ForEach-Object { L "$_" }
$expectedExecutableFiles = @(
    "verify.sh",
    "scripts/verify_container_security.sh",
    "scripts/PHASE_GATE.sh"
)
$expectedLfFiles = @(
    ".gitattributes",
    "verify.sh",
    "scripts/verify_container_security.sh",
    "scripts/PHASE_GATE.sh"
)

$allExecutable = $true
foreach ($expectedFile in $expectedExecutableFiles) {
    $escapedFile = [regex]::Escape($expectedFile)
    $matchingStageLines = @($stageOutput | Where-Object { $_ -match "^100755\s+[0-9a-f]{40}\s+0\s+$escapedFile$" })
    if ($matchingStageLines.Count -ne 1) {
        $allExecutable = $false
        L ("  executable mode missing: " + $expectedFile)
    }
}

$allLf = $true
foreach ($expectedFile in $expectedLfFiles) {
    $escapedFile = [regex]::Escape($expectedFile)
    $matchingEolLines = @($eolOutput | Where-Object {
        $_ -match "^i/lf\s+w/lf\s+attr/text(?:=auto)? eol=lf\s+$escapedFile$"
    })
    if ($matchingEolLines.Count -ne 1) {
        $allLf = $false
        L ("  exact LF state missing: " + $expectedFile)
    }
}
$testJPass = $stageExit -eq 0 -and $eolExit -eq 0 -and $allExecutable -and $allLf
L ("TEST J WRAPPER: " + $(if ($testJPass) { "PASS" } else { "FAIL" }))
if (-not $testJPass) { $overallPass = $false }

S "TEST K: POSIX syntax and Git negative-path test"
$bashCandidates = [System.Collections.Generic.List[string]]::new()
if ($env:ProgramFiles) {
    $bashCandidates.Add((Join-Path $env:ProgramFiles "Git\bin\bash.exe"))
}
if (${env:ProgramFiles(x86)}) {
    $bashCandidates.Add((Join-Path ${env:ProgramFiles(x86)} "Git\bin\bash.exe"))
}
$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue
if ($gitCommand) {
    $gitRoot = Split-Path (Split-Path $gitCommand.Source -Parent) -Parent
    $bashCandidates.Add((Join-Path $gitRoot "bin\bash.exe"))
}
$gitBashPath = $bashCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1

if (-not $gitBashPath) {
    L "Git Bash path: NOT FOUND"
    L "TEST K WRAPPER: FAIL"
    $overallPass = $false
} else {
    L ("Git Bash path: " + $gitBashPath)
    $verifySyntax = Invoke-ChildBash -WorkingDirectory $repoRoot -BashPath $gitBashPath -Arguments "-n ./verify.sh"
    $securitySyntax = Invoke-ChildBash -WorkingDirectory $repoRoot -BashPath $gitBashPath -Arguments "-n ./scripts/verify_container_security.sh"
    L "Command      : bash -n ./verify.sh"
    L ("Process exit : " + $verifySyntax.ExitCode)
    $verifySyntax.Output -split "`r?`n" | ForEach-Object { L "$_" }
    L "Command      : bash -n ./scripts/verify_container_security.sh"
    L ("Process exit : " + $securitySyntax.ExitCode)
    $securitySyntax.Output -split "`r?`n" | ForEach-Object { L "$_" }

    $posixTempDir = [IO.Path]::Combine([IO.Path]::GetTempPath(), "micro1_posix_nogit_" + [guid]::NewGuid().ToString("N"))
    try {
        New-Item -ItemType Directory -Path $posixTempDir -ErrorAction Stop | Out-Null
        Copy-Item -LiteralPath (Join-Path $repoRoot "verify.sh") -Destination (Join-Path $posixTempDir "verify.sh") -ErrorAction Stop
        $posixNegative = Invoke-ChildBash -WorkingDirectory $posixTempDir -BashPath $gitBashPath -Arguments "./verify.sh"
    } finally {
        if (Test-Path -LiteralPath $posixTempDir) {
            Remove-Item -LiteralPath $posixTempDir -Recurse -Force -ErrorAction Stop
        }
    }
    L "Command      : bash ./verify.sh (outside a Git repository)"
    L ("Process exit : " + $posixNegative.ExitCode)
    $posixNegative.Output -split "`r?`n" | ForEach-Object { L "$_" }
    $posixGitFailure = ($posixNegative.Output | Select-String "Git command failed while listing traces").Count -gt 0
    $posixComposeSeen = ($posixNegative.Output | Select-String "Compose Config Isolation").Count -gt 0
    $testKPass = $verifySyntax.ExitCode -eq 0 -and $securitySyntax.ExitCode -eq 0 -and $posixNegative.ExitCode -ne 0 -and $posixGitFailure -and -not $posixComposeSeen
    L ("  verify.sh syntax              : " + $(if ($verifySyntax.ExitCode -eq 0) { "PASS" } else { "FAIL" }))
    L ("  security script syntax        : " + $(if ($securitySyntax.ExitCode -eq 0) { "PASS" } else { "FAIL" }))
    L ("  Git failure rejected          : " + $(if ($posixNegative.ExitCode -ne 0 -and $posixGitFailure) { "PASS" } else { "FAIL" }))
    L ("  Compose not started           : " + $(if (-not $posixComposeSeen) { "PASS" } else { "FAIL" }))
    L ("TEST K WRAPPER: " + $(if ($testKPass) { "PASS" } else { "FAIL" }))
    if (-not $testKPass) { $overallPass = $false }

    S "TEST L: POSIX end-to-end pipeline"
    if ($dockerBuildPass) {
        $posixPipeline = Invoke-ChildBash -WorkingDirectory $repoRoot -BashPath $gitBashPath -Arguments "./verify.sh"
        L "Command      : bash ./verify.sh"
        L ("Process exit : " + $posixPipeline.ExitCode)
        $posixPipeline.Output -split "`r?`n" | ForEach-Object { L "$_" }
        $posixCompletionMarker = ($posixPipeline.Output | Select-String "ALL VERIFICATION STEPS PASSED").Count -gt 0
        $posixTestMarker = ($posixPipeline.Output | Select-String "17 passed").Count -gt 0
        $testLPass = $posixPipeline.ExitCode -eq 0 -and $posixCompletionMarker -and $posixTestMarker
        L ("  process exit 0       : " + $(if ($posixPipeline.ExitCode -eq 0) { "PASS" } else { "FAIL" }))
        L ("  completion marker    : " + $(if ($posixCompletionMarker) { "PASS" } else { "FAIL" }))
        L ("  current 17 tests     : " + $(if ($posixTestMarker) { "PASS" } else { "FAIL" }))
        L ("TEST L WRAPPER: " + $(if ($testLPass) { "PASS" } else { "FAIL" }))
        if (-not $testLPass) { $overallPass = $false }
    } else {
        L "TEST L STATUS: NOT RUN - current image build precondition failed."
    }
}

S "OVERALL HARNESS RESULT"
$outputPath = Join-Path $repoRoot "evidence\phase_0\adversarial_execution.txt"
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
if ($overallPass) {
    L "ALL EXECUTABLE ASSERTIONS PASSED"
    L "HARNESS EXIT: 0"
    [IO.File]::WriteAllText($outputPath, (($lines -join "`n") + "`n"), $utf8NoBom)
    exit 0
}

L "ONE OR MORE EXECUTABLE ASSERTIONS FAILED"
L "HARNESS EXIT: 1"
[IO.File]::WriteAllText($outputPath, (($lines -join "`n") + "`n"), $utf8NoBom)
exit 1
