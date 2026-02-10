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

- Enable/Disable features dynamically without redeployment.
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

## DynamoDB Access Patterns by Lambda

| Lambda Function      | Endpoint                     | HTTP Method | DynamoDB Operations            | Keys Used                                                                                  | Access Pattern                                            |
| -------------------- | ---------------------------- | ----------- | ------------------------------ | ------------------------------------------------------------------------------------------ | --------------------------------------------------------- |
| **Signup**           | `/auth/signup`               | POST        | `PutItem` (conditional)        | `PK: USER#{email}`<br>`SK: PROFILE`                                                        | Point Write - Creates user with uniqueness check          |
| **Login**            | `/auth/login`                | POST        | `GetItem`                      | `PK: USER#{email}`<br>`SK: PROFILE`                                                        | Point Read - O(1) user lookup by email                    |
| **CreateFeature**    | `/features`                  | POST        | `TransactWriteItems`           | `PK: FEATURES`<br>`SK: FEATURE#{name}`<br>`PK: ENVIRONMENT#{name}`<br>`SK: ENV#{env}` (×N) | Atomic Transaction - Creates feature + environments       |
| **GetFeature**       | `/features/{flag}`           | GET         | `GetItem` + `Query`            | `PK: FEATURES`<br>`SK: FEATURE#{name}`<br>`PK: ENVIRONMENT#{name}`                         | Point Read + Range Query - Gets metadata + environments   |
| **ListFeatures**     | `/features`                  | GET         | `Query`                        | `PK: FEATURES`                                                                             | Range Query - Lists all features                          |
| **UpdateFeatureEnv** | `/features/{flag}/env/{env}` | PUT         | `UpdateItem` (conditional)     | `PK: ENVIRONMENT#{name}`<br>`SK: ENV#{env}`                                                | Point Write - Updates environment config                  |
| **DeleteFeatureEnv** | `/features/{flag}/env/{env}` | DELETE      | `DeleteItem` (conditional)     | `PK: ENVIRONMENT#{name}`<br>`SK: ENV#{env}`                                                | Point Write - Deletes environment                         |
| **DeleteFeature**    | `/features/{flag}`           | DELETE      | `Query` + `TransactWriteItems` | `PK: FEATURES`<br>`SK: FEATURE#{name}`<br>`PK: ENVIRONMENT#{name}`                         | Range Query + Atomic Transaction - Deletes feature + envs |
| **EvaluateFeature**  | `/features/evaluate`         | POST        | `GetItem`                      | `PK: ENVIRONMENT#{name}`<br>`SK: ENV#{env}`                                                | Point Read - O(1) feature evaluation (hot path)           |
| **GetAuditLogs**     | `/features/{flag}/audit`     | GET         | `Query`                        | `PK: AUDIT#{name}`<br>`SK: LOGS#{timestamp}`                                               | Range Query - Lists audit logs chronologically            |
| **AuditConsumer**    | N/A (SQS trigger)            | N/A         | `PutItem` (batch)              | `PK: AUDIT#{name}`<br>`SK: LOGS#{timestamp}`                                               | Point Write - Appends audit logs from SQS                 |

---

## Authentication & Authorization

- JWT-based authentication
- Roles:
  - `ADMIN`
  - `CLIENT`
- Admin-only endpoints enforced at handler level

---
