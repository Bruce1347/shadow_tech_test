# Shadow technical test: Library Management API

## Technical choices

This API is based on [FastAPI](https://fastapi.tiangolo.com/) for the routes part and on [SQLAlchemy 2.0](https://docs.sqlalchemy.org/en/20/) for the ORM part.

The logical choice would have been to go with Django and Django Rest Framework as DRF provides most of the boilerplate code for routing and Django already provides a permissions management engine in its ORM.

The choice I made for a FastAPI/SQLA combo is purely based on my will to discover a framework (FastAPI) which I haven't worked with before.

## What has been done

### Books
* Creation
* Read
* Update
* Deletion

### Authors
* Creation
* Read
* Update
* Deletion

### Lending
* Creation (lend a book)
* Read
* Update (manage lendings with some logic to prevent nonsensical updates)

All of the read & updates operations on lending are behind a JWT based authentication.

## What could be better

As of today this code is absolutely **not** production ready:
* There is no proper role management in the API, this means anyone can add, edit or delete books & authors
    * In my opinion this should be done through a RBAC (Role-Based Access Control) based authentication system. Roles could be "Customer", "Librarian", "Administrator", etc.
* There is a serious threat about race conditions when two (or more) users will try to reserve a book at the same time
    * The usage of a `SELECT [...] FROM [...] FOR UPDATE` with Postgres & MariaDB would mitigate the problem by locking the book row
* The lending management is far from complete and needs way more work to be fully usable in production
* The data model could be reworked to be more in touch with already live lending systems
    * The Bibliothèque Nationale de France offers a comprehensive view of their software here: https://www.bnf.fr/fr/modeles-frbr-frad-et-frsad


## Setup

### Prerequisites
This API was written as OS agnostic but beware that it was only written and tested under Ubuntu 23.04 and Ubuntu within a WSL environment on Windows.

For both systems the python version is 3.12.

### Local setup

#### With a manual virtualenv

1. Virtualenv should be available on your system, on debian-based systems (Debian, Ubuntu, etc.) you can run `sudo apt install python3-venv` if it is not the case.
2. Create a virtualenv: `python -m venv library`
3. Enter it: `source library/env/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

#### With poetry

If poetry is available on your machine you can run `poetry install`, it will create a virtualenv and install the dependencies.

#### With docker & docker compose

A `Dockerfile` is provided at the root of this project, with compose you can build the images: `docker compose build`

### Start the API

#### Locally

1. First you need to create a user & database with MariaDB or Postgres
2. Expose the database URI through the environment: `export SQLALCHEMY_DATABASE_URI="[...]"` (replace the dots with the correct connection string)
3. Create the database schema: `PYTHONPATH=. python src/bootstrap_database_schema.py`
4. Start the API: `PYTHONPATH=. uvicorn src.api.main:app`

#### Docker

Just run `docker compose up api`, this command will:
* Start a PostgreSQL container
* Wait until the postgres container is marked as healthy
* Start the API container
* Create the missing database tables
* Start the API
