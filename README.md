# RogueORM

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/MaxDude132/RogueORM/python-package.yml?branch=main)
[![codecov](https://codecov.io/gh/MaxDude132/RogueORM/branch/main/graph/badge.svg?token=U7DKE4S8SV)](https://codecov.io/gh/MaxDude132/RogueORM)
![GitHub](https://img.shields.io/github/license/MaxDude132/RogueORM)

 A high level ORM that strives to get rid of all N+1 issues.

_Note_: This package is currently in development and is not production ready yet.

## Development Roadmap
 1. Define a clear syntax taking advantage of Python 3.10 and later's typing syntax. Status: Done
 2. Define models, managers and fields. Status: Done
 3. Add support for basic SQLite operation: SELECT, INSERT, UPDATE, DELETE. Status: Done
 4. Add support for Foreign Keys. Status: Done
 5. Add support for ManyToMany relationships using a joining table. Status: Not started
 6. Add support for relation lookup using a similar method to Django's, with __ being put between field names. Status: Not started
 7. Add support for JOIN, UNION and GROUP BY, with an interface to build them. Status: Not started
 8. Add logic for batch fetching in loops. Status: Not started
 9. Add logic for select_related. By design, prefetch_related will never be part of this ORM, preferring a 'fetch in batch when needed' approach. Status: Not started
 10. Look into supporting up to Python 3.7 by taking into account the possible usage of *Union* and *Optional* Maybe import from future? Status: Not started
 11. Improve testing by adding a way to catch queries made to the database, to make sure we lower them as much as possible. Status: Not started
 12. Add support for postgresql

If the project interests you, don't hesitate to reach out!
