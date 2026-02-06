
# Feature Flag Management System

A backend **Feature Flag Management System** built using **AWS Serverless architecture**.  
It allows admin to create, manage and audit feature flags across multiple environments (dev, qa, prod, etc.) with strong consistency, auditability, and role-based access.

---

## Tech Stack

- **Language**: Python 3.12
- **Framework**: AWS Lambda (SAM)
- **Database**: DynamoDB
- **Messaging**: SQS (Audit Events)
- **Auth**: JWT
- **Infrastructure**: AWS SAM

---

## Architecture Overview

### 🔹 Feature Flags

- Enable/Disable features dynamically without redeployemnet.
- Supports environment-based flags (dev, qa, prod)
- Allow Clients to evaluate flags.
- Maintain audit logs

### 🔹 Audit Logs

- Every change emits an audit event to **SQS**
- `audit_consumer` Lambda persists audit logs in DynamoDB
- Ensures **at-least-once delivery** (idempotent by design)

---

## System Architecture

- The Feature Flag System follows a serverless, event-driven architecture using AWS services.

<img width="988" height="568" alt="Screenshot 2026-02-06 141256" src="https://github.com/user-attachments/assets/69af5cae-57a6-4048-85e7-f668289bf5ef" />

## DynamoDB Single Table Design

| PK                           | SK                       | Description                             |
| ---------------------------- | ------------------------ | --------------------------------------- |
| `FEATURES`                   | `FEATURE#{feature_name}` | Feature metadata                        |
| `ENVIRONMENT#{feature_name}` | `ENV#{env}`              | Environment configuration for a feature |
| `AUDIT#{name}`               | `LOGS#{timestamp}`       | Audit logs                              |
| `USER#{email}`               | `PROFILE`                | User profile                            |

---

## Authentication & Authorization

- JWT-based authentication
- Roles:
  - `ADMIN`
  - `CLIENT`
- Admin-only endpoints enforced at handler level

---
