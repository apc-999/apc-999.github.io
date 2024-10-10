# User Manual

Welcome to the Issue Tracking System! This manual provides an overview of the key features available to users and administrators, along with instructions on how to utilize the system effectively.

---

## Table of Contents

1. [Overview](#overview)
2. [User Accounts](#user-accounts)
3. [Key Features for Users](#key-features-for-users)
   - [Login](#login)
   - [Sign Up](#sign-up)
   - [View Issues](#view-issues)
   - [Add Issues](#add-issues)
   - [Find Issues](#find-issues)
   - [Resolve Issues](#resolve-issues)
4. [Key Features for Administrators](#key-features-for-administrators)
   - [Admin Login](#admin-login)
   - [User Management](#user-management)
   - [Delete Issues](#delete-issues)
   - [Update Issues](#update-issues)
5. [Unit Testing](#unit-testing)
6. [Accessing the System](#accessing-the-system)

---

## Overview

The Issue Tracking System is designed to help users manage and track issues efficiently. Users can create, view, and resolve issues, while administrators can manage user accounts and oversee the system.

## User Accounts

- **User Roles**:
  - **User**: Regular account with access to view and manage their own issues.
  - **Admin**: Elevated account with access to manage users and issues.

- **Default Admin Account**:
  - **Username**: `admin`
  - **Password**: `IRNBRU`

## Key Features for Users

### Login

1. Navigate to the **Login** page.
2. Enter your **Username** and **Password**.
3. Click on **Login** to access the system.

### Sign Up

1. Go to the **Sign Up** page.
2. Fill in the **Username** and **Password** fields.
3. Click on **Sign Up** to create your account.

### View Issues

- Navigate to the **Show Issues** page to view all currently logged issues.
- If no issues are available, a message will be displayed prompting you to add new issues.

### Add Issues

1. Go to the **Add Issue** page.
2. Fill in the required fields (Title, Severity, etc.).
3. Click **Submit** to add the issue to the system.

### Find Issues

1. Navigate to the **Find Issue** page.
2. Enter a search term in the provided field.
3. Click **Search** to find matching issues.

### Resolve Issues

1. Go to the **Resolve Issue** page.
2. Select an unresolved issue from the list.
3. Enter the **Root Cause** and click **Resolve** to mark the issue as resolved.

## Key Features for Administrators

### Admin Login

- Admins can log in using the **admin** account mentioned above.

### User Management

1. Access the **Admin** page.
2. Here, you can:
   - Update user details (username, role, profile image). Profile image may not work on pythonanywhere due to a limitation of the free hosting site, it does however work locally.
   - Reset user passwords.
   - View all registered users.

### Delete Issues

1. Navigate to the **Delete Issue** page.
2. Select an issue to delete and confirm your action.

### Update Issues

1. Go to the **Update Issue** page.
2. Select an issue to update its details.
3. Make the necessary changes and click **Submit**.

## Unit Testing

Unit testing for the application is conducted in the `test.py` file. This ensures that the core functionality of the system operates as expected.

## Accessing the System

The Issue Tracking System is available online at: [apc999.eu.pythonanywhere.com](http://apc999.eu.pythonanywhere.com).

---