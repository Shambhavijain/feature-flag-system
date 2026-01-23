# Feature Flag Management System

A backend **Feature Flag Management System** built using **AWS Serverless architecture**.  
It allows admin to create, manage and audit feature flags across multiple environments (dev, qa, prod, etc.) with strong consistency, auditability, and role-based access.

---

##  Tech Stack

- **Language**: Python 3.12
- **Framework**: AWS Lambda (SAM)
- **Database**: DynamoDB (Single Table Design)
- **Messaging**: SQS (Audit Events)
- **Auth**: JWT
- **Testing**: `unittest` + `pytest`
- **Infrastructure**: AWS SAM

---

##  Architecture Overview

### 🔹 Feature Flags
- Each feature is stored under a single **partition key**
- Each environment is a separate item
- Supports:
  - Enable / Disable
  - Scheduled rollout (`rollout_end_at`)
  - Auto-enable after rollout

### 🔹 Audit Logs
- Every change emits an audit event to **SQS**
- `audit_consumer` Lambda persists audit logs in DynamoDB
- Ensures **at-least-once delivery** (idempotent by design)

---

##  DynamoDB Single Table Design

| PK | SK | Description |
|----|----|------------|
| `FEATURE#{name}` | `META` | Feature metadata |
| `FEATURE#{name}` | `ENV#{env}` | Environment configuration |
| `FEATURE#{name}` | `AUDIT#{timestamp}` | Audit logs |
| `USER#{email}` | `PROFILE` | User profile |

---

##  Authentication & Authorization

- JWT-based authentication
- Roles:
  - `ADMIN`
  - `CLIENT`
- Admin-only endpoints enforced at handler level

---

##  Installation

Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate
