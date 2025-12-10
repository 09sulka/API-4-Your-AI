# ===============================
# CONFIG
# ===============================
$certname = "LocalhostSSL"
$certFolder = "C:\SelfSSL\MyCert"
$pfxPath = "$certFolder\$certname.pfx"
$crtPath = "$certFolder\cert.crt"
$keyPath = "$certFolder\cert.key"
$openssl = "C:\Program Files\OpenSSL-Win64\bin\openssl.exe"
$password = "MySuperSecretPassword2025!"

# Tworzymy folder jeśli nie istnieje
if (!(Test-Path $certFolder)) {
    New-Item -ItemType Directory -Path $certFolder | Out-Null
}

Write-Host "=== Generating SELF-SIGNED CERTIFICATE with SAN ===" -ForegroundColor Cyan

# ===============================
# 1) GENERATE CERT WITH SAN (localhost + 127.0.0.1)
# ===============================
$cert = New-SelfSignedCertificate `
    -Subject "CN=localhost" `
    -DnsName "localhost", "127.0.0.1" `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -KeyExportPolicy Exportable `
    -KeySpec Signature `
    -KeyLength 2048 `
    -KeyAlgorithm RSA `
    -HashAlgorithm SHA256 `
    -FriendlyName $certname `
    -NotAfter (Get-Date).AddYears(5)

Write-Host "✔ Certificate created in LocalMachine\My" -ForegroundColor Green
Write-Host "Thumbprint: $($cert.Thumbprint)"


# ===============================
# 2) EXPORT CER (public cert)
# ===============================
$cerOutPath = "C:\Users\admin\Desktop\$certname.cer"
Export-Certificate -Cert $cert -FilePath $cerOutPath | Out-Null
Write-Host "✔ Exported CER to: $cerOutPath" -ForegroundColor Green


# ===============================
# 3) EXPORT PFX (private key + cert)
# ===============================
$mypwd = ConvertTo-SecureString -String $password -Force -AsPlainText

Export-PfxCertificate `
    -Cert $cert `
    -FilePath $pfxPath `
    -Password $mypwd `
    | Out-Null

Write-Host "✔ Exported PFX to: $pfxPath" -ForegroundColor Green


# ===============================
# 4) CONVERT PFX → cert.crt + cert.key (OpenSSL)
# ===============================
Write-Host "=== Extracting CRT and KEY using OpenSSL ===" -ForegroundColor Cyan

# CRT
& "$openssl" pkcs12 `
    -in $pfxPath `
    -clcerts -nokeys `
    -out $crtPath `
    -passin pass:"$password"

Write-Host "✔ Created CRT: $crtPath" -ForegroundColor Green

# KEY
& "$openssl" pkcs12 `
    -in $pfxPath `
    -nocerts -nodes `
    -out $keyPath `
    -passin pass:"$password"

Write-Host "✔ Created KEY: $keyPath" -ForegroundColor Green


# ===============================
# 5) FINAL INFO
# ===============================
Write-Host ""
Write-Host "===== DONE =====" -ForegroundColor Yellow
Write-Host "Now import $cerOutPath into:" -ForegroundColor White
Write-Host "  LocalMachine → Trusted Root Certification Authorities" -ForegroundColor Cyan
Write-Host ""
Write-Host "Then restart SQL Server:" -ForegroundColor White
Write-Host "  Restart-Service MSSQLSERVER" -ForegroundColor Cyan
Write-Host ""
Write-Host "Use cert.crt + cert.key in FastAPI:" -ForegroundColor White
Write-Host "  uvicorn app.main:app --host 127.0.0.1 --port 5001 --ssl-certfile $crtPath --ssl-keyfile $keyPath" -ForegroundColor Cyan
