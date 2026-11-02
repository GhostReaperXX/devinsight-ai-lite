# API reference

Generated from the application's OpenAPI description. The interactive version is at `/docs`.
Unless noted, endpoints need a login: send `Authorization: Bearer <token>`,
using a token from `POST /api/auth/login`.

| Method | Path | Purpose | Success |
|---|---|---|---|
| GET | `/health` | Can the service do its work right now? | 200 |
| POST | `/api/auth/register` | Create an account | 201 |
| POST | `/api/auth/login` | Exchange e-mail and password for a token | 200 |
| GET | `/api/auth/me` | Who am I? | 200 |
| GET | `/api/projects` | List projects | 200 |
| POST | `/api/projects` | Create a project (administrators) | 201 |
| GET | `/api/projects/{project_id}` | Read one project | 200 |
| GET | `/api/users` | List users (names only) | 200 |
| GET | `/api/issues` | List issues with filters | 200 |
| POST | `/api/issues` | Create an issue | 201 |
| GET | `/api/issues/{issue_id}` | Read one issue | 200 |
| PATCH | `/api/issues/{issue_id}` | Edit some fields of an issue | 200 |
| DELETE | `/api/issues/{issue_id}` | Delete an issue (administrators) | 204 |
| PATCH | `/api/issues/{issue_id}/status` | Change the status of an issue | 200 |
| POST | `/api/issues/{issue_id}/duplicate` | Close an issue as a duplicate of another | 200 |
| GET | `/api/issues/{issue_id}/comments` | List comments | 200 |
| POST | `/api/issues/{issue_id}/comments` | Add a comment | 201 |
| GET | `/api/stats` | Dashboard numbers | 200 |
| POST | `/api/insights/analyze` | Suggest a category and find related issues | 200 |
| GET | `/api/insights/duplicates` | List likely duplicate pairs | 200 |
| GET | `/api/insights/summary` | AI numbers for the dashboard | 200 |
| GET | `/api/insights/model` | The evaluation results of the deployed model | 200 |

## Error responses

| Code | Meaning |
|---|---|
| 401 | Not logged in, or the token is invalid or expired |
| 403 | Logged in, but not allowed to do this |
| 404 | The issue or project does not exist |
| 409 | Clashes with existing data, such as a repeated e-mail or project key |
| 422 | The data is invalid, or breaks a business rule |
| 500 | An unexpected error. The details are in the server log, not in the response |

Every error body has the form `{"detail": ...}`.
