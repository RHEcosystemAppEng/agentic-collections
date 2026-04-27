#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# RHEL Deployment Plan

## Rootless Podman Setup
```bash
sudo useradd -m appuser
sudo loginctl enable-linger appuser
```

## Container Run
```bash
podman run -d --name flask-app -p 8080:5000 -v /opt/app-data:/data:z flask-app:latest
```

## Systemd Service
Path: `~/.config/systemd/user/flask-app.service`
```ini
[Unit]
Description=Flask App Container
[Service]
ExecStart=/usr/bin/podman run --rm --name flask-app -p 8080:5000 -v /opt/app-data:/data:Z flask-app:latest
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
PrivateTmp=true
[Install]
WantedBy=default.target
```

## Firewall
```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

## SELinux
```bash
sudo semanage port -a -t http_port_t -p tcp 8080
sudo semanage fcontext -a -t container_file_t '/opt/app-data(/.*)?'
sudo restorecon -Rv /opt/app-data
```
REPORT_EOF
