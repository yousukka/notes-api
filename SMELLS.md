# Code Smell List

## 1. Hardcoded Configuration
Some configuration values may be directly written in the source code instead of being managed through environment variables.

## 2. Large Main File
Several API routes and application logic are kept together, which can make the project harder to maintain as it grows.

## 3. Repeated Authentication Logic
Authentication and authorization checks may be repeated across multiple endpoints instead of being centralized.

## 4. Limited Error Handling
Some operations could use more specific exception handling and clearer error messages.

## 5. Missing Automated Tests
The API has been manually tested through Swagger UI, but automated tests should be added for important endpoints.

## 6. Development Configuration
Some settings are intended for local development and should be reviewed before production deployment.

## Suggested Improvements

- Move configuration to environment variables.
- Separate routes, models, authentication, and database logic into modules.
- Centralize authentication dependencies.
- Add automated API tests.
- Improve exception handling.
- Review security settings before production deployment.