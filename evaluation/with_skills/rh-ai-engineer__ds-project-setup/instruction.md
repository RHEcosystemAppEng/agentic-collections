# Data Science Project Setup Task

You are an AI engineer on Red Hat OpenShift AI. Your team needs a new project to host a fraud detection model, with access to an S3 model store and model serving enabled.

## Requirements
- Create a new data science project named `fraud-detection` with a descriptive display name and appropriate labels
- Configure an S3-compatible data connection for model artifact storage using these details:
  - Connection name: `model-store`
  - Bucket: `fraud-models`
  - Endpoint: `https://s3.us-east-1.amazonaws.com`
  - Access key: `AKIA1234EXAMPLE`
  - Secret key: `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY`
  - Region: `us-east-1`
- Enable model serving on the project and confirm which serving runtimes become available
- Configure the pipeline server using the data connection you created
- Verify the project is fully configured and ready for model deployment

Document your setup steps, the final project configuration, and any issues encountered in `/root/report.md`. Redact any credentials in the report.

Use MCP tools to interact with the platform. If reference documentation or skills are available in this environment, consult them before beginning work.
