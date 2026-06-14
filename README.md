# Ox Security Assignment

## Overview

## Usage

Create `repos_urls.txt` and populate
with the list of links of the repositories you want to scan (a newline separated):

    https://github.com/OWASP/NodeGoat.git
    https://github.com/OWASP/railsgoat.git

Run with Docker:

    d image build . -t ox_security_scanner
    d container run ox_security_scanner

## Considerations

### Supported Repo Hosting Platforms

We assume that we scan only GitHub repos.
Further, we assume that we pass a repository URL in a "clone" format:

    https://github.com/OWASP/NodeGoat.git

### Input

We accept an input as a file for the sake of convenience.

### I/O Limit

For the sake of simplicity, we don't restrict the amount of I/O we generate when it comes to HTTP requests.

### HTTP retries

For the sake of simplicity, we don't do HTTP retries.

### Logging

We might want to use structured logging in the future.
In the future, we might want to use a separate thread for logging so that the event loop is not blocked:

    https://docs.python.org/3/library/logging.handlers.html#queuehandler

### Uniform Async Interface

I prefer to always use `async def` even if a function can be synchronous.
It creates a uniform interface within an application: you don't have to think whether a given function is async or not, you just constantly invoke it with `await` or `asyncio.create_task`.

## Observations so far

For each passed repo,
1. Scan it.
2. Output a short summary.
3. Create a more complete .csv file.

So, we create a process pool.
Submit a task to this pool.
Wait till it completes.
Each task will produce an output file in /artifacts directory.
This file will be in a JSON format.
We then analyze this file and aggregate the statistics.
We output a short summary.
We create .csv file for a long summary.


# This command: trivy repository --quiet -f table -o scan_result.json --table-mode summary https://github.com/OWASP/NodeGoat.git
# Produces this:
#
# Report Summary
#
# ┌───────────────────────────┬──────┬─────────────────┬─────────┐
# │          Target           │ Type │ Vulnerabilities │ Secrets │
# ├───────────────────────────┼──────┼─────────────────┼─────────┤
# │ package-lock.json         │ npm  │       75        │    -    │
# ├───────────────────────────┼──────┼─────────────────┼─────────┤
# │ artifacts/cert/server.key │ text │        -        │    1    │
# └───────────────────────────┴──────┴─────────────────┴─────────┘
# Legend:
# - '-': Not scanned
# - '0': Clean (no security findings detected)
#
#
# This command: trivy repository --quiet -f json -o scan_result.json https://github.com/OWASP/NodeGoat.git
# Produces a more detailed output.
