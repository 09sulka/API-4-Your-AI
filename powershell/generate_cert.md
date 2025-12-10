# generate_cert.ps1 walkthrough

Comprehensive explanation of what the PowerShell script does, the artifacts it produces, and how to use it.

## Purpose
- Creates a self-signed TLS certificate for local development with SAN entries for `localhost` and `127.0.0.1`.
- Exports the certificate in multiple formats (CER, PFX, CRT, KEY) so it can be trusted locally and used by services like SQL Server or FastAPI/uvicorn.

## Prerequisites
- Run in PowerShell on Windows.
- Administrative rights recommended because the certificate is written to `Cert:\LocalMachine\My`.
- OpenSSL installed at `C:\Program Files\OpenSSL-Win64\bin\openssl.exe` (path is hard-coded).
- The script writes to `C:\SelfSSL\MyCert` and to the desktop path `C:\Users\admin\Desktop\LocalhostSSL.cer`; adjust paths if your user or locations differ.

## Configurable variables (top of script)
- `$certname`: Friendly name and base filename; default `LocalhostSSL`.
- `$certFolder`: Target directory for generated files; default `C:\SelfSSL\MyCert`.
- `$pfxPath`, `$crtPath`, `$keyPath`: Derived output paths inside `$certFolder`.
- `$openssl`: Location of `openssl.exe`.
- `$password`: Password applied to the PFX and reused when extracting CRT/KEY (stored in plain text; change before use).

## Execution flow
1) **Ensure output directory exists**  
   Creates `$certFolder` if missing (`New-Item -ItemType Directory`).

2) **Create self-signed certificate with SANs**  
   - Uses `New-SelfSignedCertificate` with subject `CN=localhost`.  
   - SANs: `localhost` and `127.0.0.1`.  
   - Stored in `Cert:\LocalMachine\My`.  
   - RSA 2048, SHA256, exportable key, signature key spec, valid for 5 years, friendly name set to `$certname`.  
   - Prints the thumbprint for reference.

3) **Export public certificate (CER)**  
   - Exports to a fixed path on the `admin` desktop: `C:\Users\admin\Desktop\LocalhostSSL.cer`.  
   - Intended for importing into trusted roots.

4) **Export PFX (cert + private key)**  
   - Converts `$password` to a secure string.  
   - Saves `LocalhostSSL.pfx` to `$pfxPath` inside `$certFolder` with the supplied password.

5) **Split PFX into CRT and KEY with OpenSSL**  
   - `openssl pkcs12 -clcerts -nokeys` extracts `cert.crt` (no private key) to `$crtPath`.  
   - `openssl pkcs12 -nocerts -nodes` extracts the unencrypted private key `cert.key` to `$keyPath`.  
   - Both commands use the PFX password for import.

6) **User-facing reminders**  
   - Import the CER into `LocalMachine -> Trusted Root Certification Authorities`.  
   - Restart SQL Server service `MSSQLSERVER` to pick up the new cert.  
   - Example uvicorn command showing how to use `cert.crt` and `cert.key` for HTTPS in FastAPI.

## Outputs and locations
- Certificate store: new entry in `Cert:\LocalMachine\My` with friendly name `LocalhostSSL`.
- Files in `C:\SelfSSL\MyCert`:
  - `LocalhostSSL.pfx` (password protected)
  - `cert.crt` (public cert)
  - `cert.key` (private key, unencrypted)
- File on desktop: `C:\Users\admin\Desktop\LocalhostSSL.cer`.

## Safety and customization tips
- Change `$password` before running to avoid storing credentials in plain text.
- Update `$openssl`, `$certFolder`, and desktop path if your environment differs.
- Running without admin rights may fail when writing to `Cert:\LocalMachine\My`; use an elevated PowerShell.
- The script does not clean old certificates; prune unused certs manually if you regenerate frequently.
