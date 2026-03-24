#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# RHEL Debug Report

## Issue: Flask app can't bind to port 8080

### Systemd Check
```bash
systemctl status flask-app
```

### Journal Logs
```bash
journalctl -u flask-app -n 100
```

### SELinux Check
```bash
getenforce
ausearch -m AVC -ts recent
# Found: denied bind to port 8080
```

### Fix: Add port to SELinux
```bash
sudo semanage port -a -t http_port_t -p tcp 8080
sudo restorecon -Rv /opt/flask-app
```

### Firewall Check
```bash
sudo firewall-cmd --list-all
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```
REPORT_EOF
