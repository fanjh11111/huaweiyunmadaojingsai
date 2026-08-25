# ECS deployment

This directory contains the production Nginx and systemd templates for one Ubuntu ECS.

The application is installed under `/opt/huaweiyunmadaojingsai` and runs as the unprivileged `appuser` account. Nginx serves `dist/` and forwards only `/api/` to Uvicorn on `127.0.0.1:8000`; port 8000 must not be opened in the security group.

Use the deployment commands provided during the ECS setup. Before enabling the service, copy `huaweiyunmadaojingsai.env.example` to `/etc/huaweiyunmadaojingsai.env` and set any optional DashScope key only on the server.
