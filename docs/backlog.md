# Product backlog

Stories are ordered by value. Each one becomes a GitHub issue on the project board.

## Epic: Track issues

**US-1: Report an issue.** As a team member, I want to report an issue with a title and
description, so that the problem is recorded and not forgotten.

- Given I am logged in, when I submit a valid form, then the issue is saved with status open and I am its reporter.
- Given a title shorter than 5 characters, when I submit, then I see an error next to the field and my typing is kept.

**US-2: Find issues.** As a team member, I want to filter and search issues, so that I can find what matters quickly.

- Given issues in several statuses, when I choose status open, then only open issues are listed.
- Given a search word, when I apply it, then I see issues containing it in the title or description, ignoring case.
- Given more than 20 matches, when I open the list, then I see one page and links to move between pages.

**US-3: Track progress.** As an assignee, I want to move an issue through its statuses, so that everyone can see where it stands.

- Given an open issue, when I choose In progress, then its status changes without losing the page.
- Given a resolved issue, when an API client asks for open, then the request is refused with a clear message.

**US-4: Discuss an issue.** As a team member, I want to comment on an issue, so that the discussion stays with the work.

- Given an issue, when I add a comment, then it appears at once with my name and the time.

## Epic: Understand the work

**US-5: See the big picture.** As a team lead, I want a dashboard, so that I can see the state of a project at a glance.

- Given several projects, when I choose one, then the numbers change without a full page reload.

## Epic: Intelligent assistance

**US-6: Get a category suggestion.** As a reporter, I want a suggested category while I type, so that reports are classified consistently.

- Given at least 15 characters of text, when I pause typing, then a suggested category and its confidence appear.
- Given a suggestion with low confidence, then the page says the model is unsure.
- Given any suggestion, then I can still choose a different category.

**US-7: Avoid duplicates.** As a reporter, I want to see similar existing issues, so that I do not report the same problem twice.

- Given an existing similar issue, when I describe the same problem, then it is listed with a similarity score.

**US-8: Clean up duplicates.** As a maintainer, I want to review likely duplicate pairs, so that one problem has one record.

- Given a duplicate pair, when I close one as a duplicate of the other, then it is closed, linked, and a comment records why.

## Epic: Accounts and safety

**US-9: Have my own account.** As a user, I want to log in, so that my actions carry my name.

- Given a wrong password or an unknown e-mail, when I log in, then I see the same message for both.

**US-10: Protect the work.** As an administrator, I want only the right people to change things, so that the data can be trusted.

- Given I am neither the reporter nor the assignee, when I try to edit an issue, then I am refused.
- Given I am not an administrator, when I try to delete an issue, then I am refused.

## Epic: Delivery

**US-11: Trust every change.** As a developer, I want tests to run on every pull request, so that mistakes are caught before they reach users.

**US-12: See it online.** As a stakeholder, I want a public address for the application, so that I can try it without installing anything.
