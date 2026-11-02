# Entity relationship diagram

```mermaid
erDiagram
    USERS ||--o{ ISSUES : reports
    USERS |o--o{ ISSUES : "is assigned"
    USERS ||--o{ COMMENTS : writes
    PROJECTS ||--o{ ISSUES : contains
    ISSUES ||--o{ COMMENTS : has
    ISSUES |o--o{ ISSUES : "is duplicate of"

    USERS {
        int id PK
        string full_name
        string email UK
        string password_hash
        string role
        datetime created_at
    }
    PROJECTS {
        int id PK
        string key UK
        string name
        text description
        datetime created_at
    }
    ISSUES {
        int id PK
        int project_id FK
        int reporter_id FK
        int assignee_id FK
        int duplicate_of_id FK
        string title
        text description
        string category
        string priority
        string status
        string predicted_category
        float prediction_confidence
        datetime created_at
        datetime updated_at
    }
    COMMENTS {
        int id PK
        int issue_id FK
        int author_id FK
        text body
        datetime created_at
    }
```

## Decisions

- **Category, priority and status are text columns with CHECK constraints**, not separate
  tables. The values rarely change and have no attributes of their own.
- **`assignee_id` may be empty**, because a new issue often has no owner yet.
- **`predicted_category` is stored beside `category`**, so the team can measure how often
  people agree with the model.
- **Deleting an issue deletes its comments**, because a comment has no meaning alone.
- **A project with issues cannot be deleted**, because that would silently destroy history.
