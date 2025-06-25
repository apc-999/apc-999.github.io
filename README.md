# QAHE DA DTS L5 - Software engineering and agile
# Issue Tracking System

This is an Issue Tracking System built with Flask and SQLite, allowing users to manage issues and user accounts effectively. 

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [User Accounts](#user-accounts)
- [Unit Testing](#unit-testing)
- [CI/CD Pipeline](#ci-cd-pipeline)
- [Access](#access)

## Features

- User account creation and management.
- Admin user with elevated permissions.
- Ability to add, update, delete, and resolve issues.
- Search functionality for issues.
- Simple, user-friendly interface.

## Installation
1. Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

2. Run the script:

   ```bash
   python main.py
   ```
   (this can be run in IDLE)

## Usage

- After starting the application, you can access it through your web browser at `http://127.0.0.1:5000`.
- Use the provided admin account to create user accounts or manage existing ones.

## User Accounts

- **Admin User**:
  - **Username**: `admin`
  - **Password**: `IRNBRU`
  - Admin users can manage user accounts, including resetting passwords and updating user roles. They can add, modify or resolve issues as well as being able to do everything that a regular user can do.

- **Regular Users**:
  - Users can create accounts, see all issues, search for specific issues and resolve or create their own issues but cannot modify/delete issues or perform administrative tasks.

- **Anonymous Users**:
  - Users that are not signed in can login or create an account and see the issues in the system but cannot modify or add issues or perform administrative tasks.

### Creating a User Account

1. Go to the signup page (link in the top right of the page or go to `/signup`)
2. Enter a username and password.
3. Click the submit button to create your account.

## Unit Testing

Unit tests are included in `test.py`. You can run the tests to ensure the system functions as expected.

```bash
python test.py
```

## CI/CD Pipeline

This project uses GitHub Actions for continuous integration and deployment:

- **Testing**: Automatically runs unit tests on Python 3.8, 3.9, and 3.10 with code coverage reporting.
- **Linting**: Checks code quality using flake8, black, and isort.
- **Security Scanning**: Performs security analysis using Bandit and Safety.
- **Deployment**: Builds and deploys the application when changes are pushed to the main branch.

GitHub Actions workflows are located in the `.github/workflows` directory:
- `python-tests.yml`: Runs unit tests and generates coverage reports
- `python-lint.yml`: Performs code quality checks
- `security-scan.yml`: Scans for security vulnerabilities
- `deploy.yml`: Handles the build and deployment process

## Access

The application is also available online at: [apc999.eu.pythonanywhere.com](http://apc999.eu.pythonanywhere.com)

---