# Offline Deployment (Air-gapped)

## 1) Build bundle on connected machine
```bash
cd secure-xl2hwp-local
bash scripts/build_offline_bundle.sh
```

Output:
- `dist/secure-xl2hwp-offline-bundle.tar.gz`

## 2) Move tarball to air-gapped machine
USB, internal mirror, or approved transfer channel.

## 3) Install offline on air-gapped machine
```bash
mkdir -p /opt/secure-xl2hwp
cd /opt/secure-xl2hwp
tar -xzf secure-xl2hwp-offline-bundle.tar.gz
bash install_offline.sh /opt/secure-xl2hwp/runtime
```

## 4) Configure
```bash
cd /opt/secure-xl2hwp/runtime
cp .env.example .env
# Set JWT_SECRET_KEY and AUTH_PASSWORD_PEPPER to organization values
```

## 5) Run
```bash
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8080
```
