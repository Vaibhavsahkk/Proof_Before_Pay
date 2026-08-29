$ErrorActionPreference = 'Continue'
$evidenceDir = "D:\MICRO.1\evidence\phase_0"
$outProof = "$evidenceDir\FINAL_PHASE0_PROOF.txt"
$candidateSha = git rev-parse HEAD 2>&1 | Out-String
$candidateSha = $candidateSha.Trim()
$timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:sszzz")

Set-Content -Path $outProof -Value "================================================================"
Add-Content -Path $outProof -Value "PHASE 0 FINAL AUDIT PROOF"
Add-Content -Path $outProof -Value "================================================================"
Add-Content -Path $outProof -Value "STATUS: READY FOR EXTERNAL CHATGPT REVIEW"
Add-Content -Path $outProof -Value "TIMESTAMP: $timestamp"
Add-Content -Path $outProof -Value "REPOSITORY: https://github.com/Vaibhavsahkk/Proof_Before_Pay.git"
Add-Content -Path $outProof -Value "CANDIDATE SHA: $candidateSha"
Add-Content -Path $outProof -Value "`n================================================================"
Add-Content -Path $outProof -Value "1. CLEAN CLONE REPRODUCTION EVIDENCE"
Add-Content -Path $outProof -Value "================================================================"
Get-Content -Path "$evidenceDir\clean_clone_execution.txt" | Add-Content -Path $outProof
Add-Content -Path $outProof -Value "`n================================================================"
Add-Content -Path $outProof -Value "2. CLEAN CLONE ADVERSARIAL EXECUTION EVIDENCE"
Add-Content -Path $outProof -Value "================================================================"
Get-Content -Path "$evidenceDir\clean_clone_adversarial_execution.txt" | Add-Content -Path $outProof
Add-Content -Path $outProof -Value "`n================================================================"
Add-Content -Path $outProof -Value "3. POST-TEST AUDIT (CLEANLINESS VERIFICATION)"
Add-Content -Path $outProof -Value "================================================================"
Get-Content -Path "$evidenceDir\clean_clone_post_test_audit.txt" | Add-Content -Path $outProof
Add-Content -Path $outProof -Value "`n================================================================"
Add-Content -Path $outProof -Value "4. CONTAINER SECURITY VERIFICATION"
Add-Content -Path $outProof -Value "================================================================"
$securityOutput = & 'C:\Program Files\Git\bin\bash.exe' .\scripts\verify_container_security.sh 2>&1 | Out-String
Add-Content -Path $outProof -Value $securityOutput

Write-Output "Final proof generated at $outProof"
