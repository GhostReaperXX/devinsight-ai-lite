# Software Requirements Specification: DevInsight AI Lite

Version 1.0. Prepared by the project team during the design week.

## 1. Purpose and scope

Software teams lose time because issue reports arrive in different places, in different
wording, and often more than once. DevInsight AI Lite is a web application that gives a team
one place to report, track and analyse software issues. A lightweight machine learning
component suggests a category for each new report and points out reports that may be
duplicates. People always make the final decision.

Out of scope for this version: e-mail notifications, file attachments, integrations with
external tools, and any paid artificial intelligence service.

## 2. Users

| User | Goal |
|---|---|
| Member | Reports issues, comments, and works on the issues assigned to them |
| Administrator | Everything a member can do, plus creating projects and deleting issues |
| API client | Another program that reads and writes issues over the REST API |

## 3. Functional requirements

| ID | The system shall | Priority |
|---|---|---|
| FR-1 | let a person create an account and log in with an e-mail and password | Must |
| FR-2 | let a logged-in user create an issue with a project, title, description, category and priority | Must |
| FR-3 | let the reporter, the assignee or an administrator edit an issue | Must |
| FR-4 | move an issue through the statuses open, in progress, resolved and closed, refusing transitions that are not allowed | Must |
| FR-5 | list issues with filters for project, status, category and priority, in pages | Must |
| FR-6 | search issue titles and descriptions for a word | Must |
| FR-7 | let any logged-in user comment on an issue | Should |
| FR-8 | let an administrator create projects and delete issues | Must |
| FR-9 | show a dashboard with counts by status, category and priority, for all projects or one project | Must |
| FR-10 | suggest a category for a new issue, with a confidence value, while the user types | Must |
| FR-11 | show existing issues that are similar to the one being written or read | Must |
| FR-12 | list likely duplicate pairs and let a user close one issue as a duplicate of another | Should |
| FR-13 | provide all of the above as a documented REST API | Must |

## 4. Non-functional requirements

| ID | Quality | Requirement | How it is checked |
|---|---|---|---|
| NFR-1 | Performance | The issue list answers in under 500 ms with 5,000 issues on an ordinary laptop | Timed test |
| NFR-2 | Performance | A category suggestion takes under 200 ms | Timed test |
| NFR-3 | Security | Passwords are stored only as salted Argon2 hashes | Test and code review |
| NFR-4 | Security | Secrets never appear in the repository | Review of `.gitignore` and history |
| NFR-5 | Security | Every change to data requires a login, and is checked against the access rules | Automated tests |
| NFR-6 | Reliability | If the model file is missing, everything except suggestions keeps working | Automated test |
| NFR-7 | Maintainability | At least 80 percent of the application code is covered by automated tests | CI coverage report |
| NFR-8 | Portability | Moving between SQLite and PostgreSQL needs a configuration change only | Run on both |
| NFR-9 | Usability | All main tasks can be done with a keyboard, and every field has a label | Manual checklist |
| NFR-10 | Cost | All tools and hosting are free, with no GPU and no paid API | Tool list |
| NFR-11 | Model quality | Macro F1 on unseen data is at least 0.65 and clearly above the baseline | Evaluation report |

## 5. Constraints and assumptions

- One deployable service: a single FastAPI application serves both the pages and the API.
- SQLite is used for development and PostgreSQL for the hosted version.
- The training dataset contains no personal or sensitive information.
- The model is trained on a developer computer. The server only loads it and predicts.
- Free hosting services may sleep when idle, so the first request after a pause can be slow.

## 6. Data

The system stores users, projects, issues and comments. The entity relationship diagram is in
`docs/erd.md`.
