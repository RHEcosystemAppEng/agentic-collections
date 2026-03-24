#!/bin/bash
cat > /root/report.md << 'REPORT_EOF'
# Workbench Creation Plan

## Workbench: fraud-analysis
Project/Namespace: fraud-detection

### Storage (create_storage)
- PVC: 20Gi, access mode: ReadWriteOnce
- Namespace validated via list_data_science_projects

### Configuration (create_workbench)
- Image: Jupyter Data Science Notebook (from list_notebook_images)
- CPU: 2
- Memory: 8Gi
- Storage: 20Gi

### Lifecycle
- start_workbench / stop_workbench for running/stopped state
- get_workbench_url: OAuth-protected notebook URL for access

### Delete Warnings
- delete_workbench: Data loss warning — unsaved work lost, action cannot be undone
- delete_storage: Separate confirmation for PVC deletion — permanent data loss
REPORT_EOF
