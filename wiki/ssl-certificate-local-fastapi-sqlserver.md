## SSL Certificate for Local FastAPI + SQL Server 2025

### Why We Need It, What Fails Without It, and How to Configure It Correctly

---

### 1. Purpose of This Document
This document explains:
- Why we need an SSL certificate for the local integration between SQL Server 2025, FastAPI, and Python.
- What errors appear when no valid certificate is configured.
- Exactly what configuration the SSL certificate must have (CN, SAN, stores, key properties).
- How to manually create and configure the certificate step by step.
- That there is already a PowerShell script in the project’s `powershell` folder which automates the whole process.
- That all of this requires Windows administrator privileges.

Assumed setup:
- SQL Server 2025 running locally.
- A local FastAPI application exposed via Uvicorn.
- A Python script that calls the FastAPI endpoint over HTTPS to get embeddings and writes them back into SQL Server.

---

### 2. Why We Need an SSL Certificate
#### 2.1 SQL Server 2025 Requires HTTPS for External AI Endpoints
SQL Server 2025 introduces native AI and vector integration. When SQL Server calls an external REST endpoint (for example, an embeddings or LLM endpoint), it behaves like an enterprise client calling a cloud service:
- HTTP is not allowed; only HTTPS is supported.
- SQL Server performs a full TLS handshake.
- The server’s certificate must be trusted by the machine.
- The certificate’s Subject Alternative Name (SAN) must match the hostname used in the URL.

This is true even if the endpoint is running on localhost. Therefore, if we want SQL Server to talk to a local FastAPI service such as `https://localhost:5001/openai/deployments/local/embeddings`, we must provide a valid SSL certificate that the operating system and SQL Server trust.

#### 2.2 FastAPI / Uvicorn Needs a Certificate to Serve HTTPS
FastAPI itself does not handle TLS termination. TLS is implemented by the ASGI server, in this case Uvicorn. Uvicorn requires:
- A certificate file (`cert.crt`).
- A private key file (`cert.key`).

Without these, Uvicorn cannot expose an `https://` endpoint. It will only serve `http://`, which is not acceptable for SQL Server.

#### 2.3 Python Also Validates TLS
The Python client (using `aiohttp`) performs certificate validation when calling `https://localhost:5001`. If the certificate is not trusted or does not match the hostname, Python rejects the connection with an SSL validation error.

---

### 3. What Errors Occur Without a Proper SSL Certificate
When the certificate is missing or misconfigured, you will see different errors depending on the component.

#### 3.1 Errors from SQL Server 2025
Typical error when the certificate is missing, not trusted, or does not match the hostname:
- `HRESULT: 0x80070018`
- `Failed to communicate with external REST endpoint`

In practice, this means the TLS handshake failed, SQL Server could not validate the certificate chain, or the hostname did not match the certificate’s SAN.

#### 3.2 Errors from Python (`aiohttp`)
When Python does not trust the certificate, you will typically see:
- `ssl.SSLCertVerificationError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed`
- `Cannot connect to host localhost:5001 ssl:True [SSLCertVerificationError]`

This happens when `cafile` is not provided in the SSL context, the SAN does not match the host (`localhost` vs `127.0.0.1`), or the certificate is invalid or corrupted.

#### 3.3 Browser / API Client Warnings
Browsers and tools like Bruno/Postman will show:
- “Your connection is not private”
- “Certificate is not trusted”
- “Self-signed certificate”

if the certificate is not installed as a trusted root.

---

### 4. Required Certificate Configuration
To satisfy Windows, SQL Server, FastAPI/Uvicorn, and Python, the SSL certificate must have all of the following properties.

#### 4.1 Subject and SAN
- Subject (CN): `localhost`
- Subject Alternative Name (SAN):
  - DNS Name = `localhost`
  - IP Address = `127.0.0.1` (so you can safely use either `localhost` or `127.0.0.1` in URLs)

#### 4.2 Location in Windows Certificate Stores
The certificate must be created in and/or imported into the LocalMachine stores, not just CurrentUser.
- Personal / My (`Cert:\LocalMachine\My`): where the certificate with private key lives; Uvicorn uses this when exporting to `.pfx`.
- Trusted Root Certification Authorities (`Cert:\LocalMachine\Root`): the public part (or self-signed issuer) must be imported here; SQL Server and the OS only trust certificates that chain up to a root in this store.

#### 4.3 Key and Algorithm
- Key Export Policy: Exportable (needed to export `.pfx`, then `cert.crt` and `cert.key`).
- Key Algorithm: RSA.
- Key Length: at least 2048 bits.
- Hash Algorithm: SHA256.
- Validity: e.g., 5 years for local development and internal use.

#### 4.4 Trust
- The certificate’s public part (or self-signed root) must be imported into Local Computer → Trusted Root Certification Authorities.
- After import, the system and SQL Server will treat the HTTPS endpoint as trusted.

---

### 5. Manual Step-by-Step: Creating and Configuring the SSL Certificate
Important: All steps must be performed with Windows administrator privileges. Run PowerShell as Administrator and MMC (`mmc.exe`) as Administrator when managing certificates.

#### 5.1 Generate the Self-Signed Certificate (PowerShell, as Administrator)
```powershell
$certName = "LocalhostSSL"

$cert = New-SelfSignedCertificate `
    -Subject "CN=localhost" `
    -DnsName "localhost","127.0.0.1" `
    -CertStoreLocation "Cert:\LocalMachine\My" `
    -KeyExportPolicy Exportable `
    -KeySpec Signature `
    -KeyLength 2048 `
    -KeyAlgorithm RSA `
    -HashAlgorithm SHA256 `
    -FriendlyName $certName `
    -NotAfter (Get-Date).AddYears(5)
```
This creates a certificate in `LocalMachine\My`, includes SAN entries for `localhost` and `127.0.0.1`, and makes the private key exportable.

#### 5.2 Export the Certificate as `.cer`
```powershell
Export-Certificate -Cert $cert -FilePath "C:\SelfSSL\MyCert\LocalhostSSL.cer"
```
This file contains the public part of the certificate for import into the Trusted Root store.

#### 5.3 Export the Certificate as `.pfx`
```powershell
$mypwd = ConvertTo-SecureString -String "YourStrongPasswordHere!" -Force -AsPlainText

Export-PfxCertificate `
    -Cert $cert `
    -FilePath "C:\SelfSSL\MyCert\LocalhostSSL.pfx" `
    -Password $mypwd
```
The `.pfx` file is needed to extract `cert.crt` and `cert.key` with OpenSSL.

#### 5.4 Import the Certificate into Trusted Root (MMC, as Administrator)
1. Run `mmc.exe` as Administrator.  
2. File → Add/Remove Snap-in… → Certificates → Add.  
3. Select Computer account → Local computer → OK.  
4. In the tree: Certificates (Local Computer) → Trusted Root Certification Authorities → Certificates.  
5. Right-click Certificates → All Tasks → Import….  
6. Select `C:\SelfSSL\MyCert\LocalhostSSL.cer`.  
7. Complete the wizard.

Now the machine, including SQL Server, will trust this certificate as a root CA.

#### 5.5 Extract `cert.crt` and `cert.key` for Uvicorn (OpenSSL)
```powershell
# Public certificate
& "C:\Program Files\OpenSSL-Win64\bin\openssl.exe" pkcs12 `
    -in C:\SelfSSL\MyCert\LocalhostSSL.pfx `
    -clcerts -nokeys `
    -out C:\SelfSSL\MyCert\cert.crt `
    -passin pass:"YourStrongPasswordHere!"

# Private key
& "C:\Program Files\OpenSSL-Win64\bin\openssl.exe" pkcs12 `
    -in C:\SelfSSL\MyCert\LocalhostSSL.pfx `
    -nocerts -nodes `
    -out C:\SelfSSL\MyCert\cert.key `
    -passin pass:"YourStrongPasswordHere!"
```
You should now have:
- `C:\SelfSSL\MyCert\cert.crt`
- `C:\SelfSSL\MyCert\cert.key`

#### 5.6 Configure FastAPI / Uvicorn to Use HTTPS
```bash
uvicorn app.main:app `
  --host localhost `
  --port 5001 `
  --ssl-certfile "C:\SelfSSL\MyCert\cert.crt" `
  --ssl-keyfile "C:\SelfSSL\MyCert\cert.key"
```
FastAPI is now available at `https://localhost:5001` and uses the trusted local certificate.

#### 5.7 Configure Python (`aiohttp`) to Trust the Certificate
```python
import ssl
import aiohttp

ssl_context = ssl.create_default_context(
    cafile="C:/SelfSSL/MyCert/cert.crt"
)

connector = aiohttp.TCPConnector(
    limit=10,
    ssl=ssl_context,
)

async with aiohttp.ClientSession(connector=connector) as session:
    async with session.post(
        "https://localhost:5001/openai/deployments/local/embeddings",
        json={"input": ["example text"]}
    ) as resp:
        data = await resp.json()
```
This ensures Python trusts the same certificate and can connect securely.

#### 5.8 Verify Everything Works
1. Open `https://localhost:5001/docs` in a browser: no certificate warning should appear.  
2. Run a small Python test script using the SSL context: you should not see `SSLCertVerificationError`.  
3. Trigger a call from SQL Server 2025 to the external endpoint: you should no longer see `HRESULT 0x80070018`.

---

### 6. PowerShell Automation Script
To simplify and avoid mistakes, use the PowerShell script in `powershell/generate_cert.ps1`. It:
- Generates the self-signed certificate with the correct CN and SANs.
- Stores it in the correct LocalMachine store.
- Exports `.cer` and `.pfx`.
- Uses OpenSSL to create `cert.crt` and `cert.key`.
- Prints example commands for starting Uvicorn.

Run it in an elevated PowerShell and ensure OpenSSL is installed at `C:\Program Files\OpenSSL-Win64\bin\openssl.exe`.

---

### 7. Administrator Privileges – Important Note
All SSL certificate operations here require Windows administrator privileges because they interact with LocalMachine certificate stores and system-wide settings. You must:
- Run PowerShell as Administrator when generating and exporting the certificate.
- Run MMC as Administrator when importing the certificate into Trusted Root Certification Authorities.
- Restart services (like SQL Server) after certificate changes, which also often requires admin-level permissions.

If you attempt these steps without administrator rights, you may encounter access denied errors, certificates being created under the wrong store (CurrentUser instead of LocalMachine), or SQL Server being unable to see or trust the certificate.

---

### Summary
- SQL Server 2025 requires HTTPS for external AI calls.
- A self-signed SSL certificate is needed for local FastAPI endpoints.
- The certificate must have correct SANs, be created in `LocalMachine\My`, and be imported into Trusted Root Certification Authorities.
- Uvicorn needs `cert.crt` and `cert.key` to serve HTTPS.
- Python needs an explicit `ssl_context` pointing to the same `cert.crt`.
- The PowerShell script `powershell/generate_cert.ps1` automates the entire process, but all operations must be performed with administrator privileges.
