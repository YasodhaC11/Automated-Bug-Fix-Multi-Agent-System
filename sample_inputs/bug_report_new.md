# Bug Report

## Title
Weather service crashes with connection timeout error

## Description
The /api/weather endpoint crashes when the external weather API
is slow to respond. Started after v2.1.0 deployment.

## Expected Behavior
Should return a friendly error message:
{"error": "Weather service unavailable, please try again later"}

## Actual Behavior
Returns HTTP 500 with ConnectionError crash after hanging for 30+ seconds.

## Environment
- Python 3.11
- Flask 2.3.0
- Requests library 2.31.0
- OS: Ubuntu 22.04

## Reproduction Hints
- Happens when external API is slow or unreachable
- Does NOT happen when external API responds normally
- Seems related to missing timeout in requests.get() call
- All other endpoints work fine