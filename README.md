# CloudSecOps – Secure Cloud Native Architecture on AWS

## Project Overview

CloudSecOps is an engineering project focused on designing and implementing a secure Cloud Native architecture on AWS integrating:

- Infrastructure as Code (Terraform)
- DevSecOps practices
- Zero Trust principles
- Secure backend application
- Cloud monitoring & logging
- Incident simulation and forensic analysis

The project follows a structured methodology aligned with cybersecurity best practices and cloud security standards.

---

## Project Objectives

- Design a secure AWS infrastructure (VPC, EC2, RDS, S3, IAM)
- Automate infrastructure provisioning using Terraform
- Implement a secure backend API with RBAC and JWT authentication
- Integrate security controls into CI/CD pipeline
- Enable logging and monitoring (CloudTrail, CloudWatch)
- Simulate a security incident and perform forensic analysis
- Apply GRC methodology (risk analysis, PSSI, PCA/PRA)

---

## Architecture Overview

The infrastructure is deployed within a custom AWS VPC:

- Public Subnet: EC2 instance hosting the backend
- Private Subnet: RDS PostgreSQL database
- S3 Bucket (encrypted)
- IAM Least Privilege policies
- CloudTrail logging
- CloudWatch monitoring

Security principles applied:

- Network segmentation
- Encrypted data at rest and in transit
- Role-based access control
- Infrastructure as Code
- DevSecOps integration

---

## Repository Structure


cloud-secops-b3/
│
├── docs/ # Project documentation
├── terraform/ # Infrastructure as Code
├── app/ # Backend application
├── scripts/ # SQL and automation scripts
└── .github/workflows/ # CI/CD pipelines


---

## Technologies Used

### Cloud & Infrastructure
- AWS
- Terraform

### Backend
- Python (FastAPI)
- PostgreSQL

### DevSecOps
- GitHub Actions
- Trivy (Container scanning)
- SAST tools
- Docker

### Security & Monitoring
- AWS IAM
- CloudTrail
- CloudWatch
- Zero Trust Architecture principles

---

## Getting Started

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/cloud-secops-b3.git
cd cloud-secops-b3
```

### 2️⃣ Configure AWS CLI

```bash
aws configure
```

### 3️⃣ Initialize Terraform

```bash
cd terraform
terraform init
terraform validate
terraform plan
```

### 4️⃣ Deploy infrastructure

```bash
terraform apply
```

### 🔐 Security Practices Implemented

- Least privilege IAM roles
- No public RDS exposure
- Encrypted S3 buckets
- JWT authentication
- Role-Based Access Control
- CI/CD vulnerability scanning
- Incident simulation & forensic reporting

### 📊 Project Management

The project is managed using:

- GitHub Issues (task tracking)
- Milestones (sprint planning)
- Pull Requests (code review)
- Version tags (release tracking)

Agile methodology with 2-week sprints.

### 📘 Documentation

Full documentation is available under the /docs directory:

- Project Charter (Cahier des charges)
- Technological Watch
- Architecture Diagrams
- Risk Analysis
- Incident Report

### 🎓 Academic Context

This project is developed as part of a Cloud Security engineering program, aiming to demonstrate:

- Technical cloud security skills
- DevSecOps implementation
- Infrastructure automation
- Risk management
- Incident response capabilities

⚠️ Disclaimer

This project is for educational purposes only.
All simulated attacks are performed in a controlled environment.

👩‍💻 Author

[Your Name]
Cloud Security Engineering Student
2026