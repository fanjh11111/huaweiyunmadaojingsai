# Ubuntu ECS deployment

This directory contains the only files that need to differ for the Huawei Cloud ECS deployment. Application source code remains the supplied project version.

## Production topology

- The project is installed at `/opt/huaweiyunmadaojingsai`.
- Uvicorn runs as unprivileged user `appuser` on `127.0.0.1:8000`.
- Nginx serves `dist/` on port 80 and forwards `/api/` to Uvicorn.
- Open only TCP 22 and 80 in the ECS security group. Do not expose port 8000.

## Deployment steps

```bash
sudo useradd --system --create-home --shell /usr/sbin/nologin appuser
sudo chown -R appuser:appuser /opt/huaweiyunmadaojingsai

cd /opt/huaweiyunmadaojingsai
python3 -m venv .venv
sudo -u appuser .venv/bin/pip install -r requirements.txt
sudo -u appuser bash deploy/build-frontend.sh /opt/huaweiyunmadaojingsai

sudo cp deploy/huaweiyunmadaojingsai.env.example /etc/huaweiyunmadaojingsai.env
sudo chmod 600 /etc/huaweiyunmadaojingsai.env
sudo cp deploy/engine-rag.service /etc/systemd/system/engine-rag.service
sudo cp deploy/nginx.conf /etc/nginx/sites-available/engine-rag
sudo ln -sf /etc/nginx/sites-available/engine-rag /etc/nginx/sites-enabled/engine-rag
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl daemon-reload
sudo systemctl enable --now engine-rag
sudo systemctl reload nginx
```

`build-frontend.sh` intentionally rewrites only generated `dist/` JavaScript from `http://localhost:8000/api` to `/api`. This is necessary because a visitor's browser would otherwise call its own localhost instead of this ECS; no source Vue component is changed.

## Verification

```bash
sudo systemctl status engine-rag --no-pager
curl -I http://127.0.0.1/
curl -I http://127.0.0.1/api/docs
```

Before enabling the service, copy the environment template and set an optional DashScope key only on the server. Never commit a populated environment file.
