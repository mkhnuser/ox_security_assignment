# Ox Security Assignment

## Overview

Scan code repositories using Trivy Security Vulnerability Scanner concurrently.
Upon scan completion, you get a concise summary of the scan.
Each scan happens in a separate OS process.

Trivy homepage: ```https://trivy.dev/```.

## Usage

Create `repos_urls.txt` in the project root and populate
with the list of links of the repositories you want to scan (a newline separated).
For example, in `repos_urls.txt`:

    https://github.com/OWASP/NodeGoat.git
    https://github.com/OWASP/railsgoat.git

Run with Docker:

    docker image build . -t ox_security_scanner
    docker container run --mount type=bind,src=./src,dst=/security_scanner/src/ ox_security_scanner

Observe the scan results in your terminal.

Alternatively, you might persist `/artifacts` directory from a docker container to your host.
This directory contains the full output of repository scans.

## Considerations

### Architecture

For such a small wrapper application, a function-based approach has been chosen.

### Supported Repo Hosting Platforms

We assume that we scan only GitHub repos.
Further, we assume that we pass a repository URL in a "clone" format:

    https://github.com/OWASP/NodeGoat.git

### Input

We accept an input as a file for the sake of convenience.

### I/O Limit

We don't restrict the amount of I/O we generate when it comes to HTTP requests.

### HTTP retries

We don't do HTTP retries.

### Logging

We might want to use structured logging in the future.
In the future, we might want to use a separate thread for logging so that the event loop is not blocked:

    https://docs.python.org/3/library/logging.handlers.html#queuehandler

### Uniform Async Interface

I prefer to always use `async def` even if a function can be synchronous.
It creates a uniform interface within an application: you don't have to think whether a given function is async or not, you just constantly invoke it with `await` or `asyncio.create_task`.

## Future Improvements

1. Persist statistics to files;
2. Create dependency graph;
3. Run security scans in separate containers;
4. Provide better documentation.
5. Address some considerations: I/O limits, HTTP retries, structured logging.

## Observations so far

### Trivy Seg faults

Sometimes Trivy crashes with an obscure seg fault:

    2026-06-14 13:56:42,937 - root_logger - ERROR - unexpected fault address 0x7f8b42875000
    fatal error: fault
    [signal SIGSEGV: segmentation violation code=0x2 addr=0x7f8b42875000 pc=0x9464aa]

    goroutine 1 gp=0xeea273c01e0 m=9 mp=0xeea27b0c008 [running]:
    runtime.throw({0x5bbe7a9?, 0x5bfd2a1?})

## Example Output

```
(.venv) uladzislau.mikheyenka ox_security_assignment %
(.venv) uladzislau.mikheyenka ox_security_assignment % d image build . -t ox_security_scanner

[+] Building 20.4s (16/16) FINISHED                                                                                     docker:desktop-linux
 => [internal] load build definition from Dockerfile                                                                                    0.0s
 => => transferring dockerfile: 815B                                                                                                    0.0s
 => [internal] load metadata for docker.io/library/python:3.14.6-bookworm                                                               1.0s
 => [internal] load .dockerignore                                                                                                       0.0s
 => => transferring context: 2B                                                                                                         0.0s
 => [ 1/11] FROM docker.io/library/python:3.14.6-bookworm@sha256:601bab1661920dfc3bcd35f4af1ca5df6b0b1385be45adc65baa6c02ab15f110       0.0s
 => => resolve docker.io/library/python:3.14.6-bookworm@sha256:601bab1661920dfc3bcd35f4af1ca5df6b0b1385be45adc65baa6c02ab15f110         0.0s
 => [internal] load build context                                                                                                       0.2s
 => => transferring context: 231.65kB                                                                                                   0.2s
 => CACHED [ 2/11] RUN apt update && apt upgrade -y                                                                                     0.0s
 => CACHED [ 3/11] RUN apt install wget gnupg                                                                                           0.0s
 => CACHED [ 4/11] RUN wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | tee /usr/share/keyrings/t  0.0s
 => CACHED [ 5/11] RUN echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main"  0.0s
 => CACHED [ 6/11] RUN apt update                                                                                                       0.0s
 => CACHED [ 7/11] RUN apt install trivy                                                                                                0.0s
 => CACHED [ 8/11] WORKDIR /security_scanner                                                                                            0.0s
 => [ 9/11] COPY . ./                                                                                                                   0.3s
 => [10/11] RUN pip install --no-cache-dir -r requirements.txt                                                                         16.4s
 => [11/11] RUN chmod a+x ./scripts/run-security-scanner.sh                                                                             0.2s
 => exporting to image                                                                                                                  2.1s
 => => exporting layers                                                                                                                 1.2s
 => => exporting manifest sha256:5f7383012e123917e4ad96194f4d1f308fa34f93c4255100503d11f4207c15b9                                       0.0s
 => => exporting config sha256:4f613767eda1cfd8781af6ee0bd2cebdb4f0f657cdc3f912015efca2c92950bc                                         0.0s
 => => exporting attestation manifest sha256:d37aef9425cb429e9b24a0ae73bc0713d245b84009a0c63baab0041f1ac0023e                           0.0s
 => => exporting manifest list sha256:badb9b530cf517ea4008265f4cf4458d4029d91f478a197de88aaea6c5baff60                                  0.0s
 => => naming to docker.io/library/ox_security_scanner:latest                                                                           0.0s
 => => unpacking to docker.io/library/ox_security_scanner:latest                                                                        0.8s
(.venv) uladzislau.mikheyenka ox_security_assignment %
(.venv) uladzislau.mikheyenka ox_security_assignment %
(.venv) uladzislau.mikheyenka ox_security_assignment %     d container run -it --mount type=bind,src=./src,dst=/security_scanner/src/ ox_security_scanner

2026-06-14 15:06:39,881 - root_logger - INFO - The security scan is about to start.
2026-06-14 15:06:39,882 - root_logger - INFO - The total of 2 repo URLs have been obtained.
2026-06-14 15:06:39,882 - root_logger - INFO - The following repositories will be scanned:
2026-06-14 15:06:39,882 - root_logger - INFO - [
    "https://github.com/OWASP/NodeGoat.git",
    "https://github.com/OWASP/railsgoat.git"
]
2026-06-14 15:06:39,882 - root_logger - DEBUG - Artifacts directory is about to be recreated.
2026-06-14 15:06:39,886 - root_logger - INFO - trivy repository --quiet -f json -o /security_scanner/artifacts/1781449599.8859951-https%3A%2F%2Fgithub.com%2FOWASP%2FNodeGoat.git.json https://github.com/OWASP/NodeGoat.git
2026-06-14 15:06:39,887 - root_logger - INFO - trivy repository --quiet -f json -o /security_scanner/artifacts/1781449599.8860247-https%3A%2F%2Fgithub.com%2FOWASP%2Frailsgoat.git.json https://github.com/OWASP/railsgoat.git
2026-06-14 15:07:39,158 - root_logger - INFO - {
    "repo_url": "https://github.com/OWASP/NodeGoat.git",
    "stars": 2050,
    "severity_statistics": {
        "CRITICAL": 10,
        "HIGH": 39,
        "MEDIUM": 16,
        "LOW": 10,
        "UNKNOWN": 0
    },
    "vulnerability_names": [
        "CVE-2015-8858",
        "CVE-2016-10531",
        "CVE-2017-1000427",
        "CVE-2017-16114",
        "CVE-2017-16137",
        "CVE-2017-20162",
        "CVE-2017-20165",
        "CVE-2018-25110",
        "CVE-2019-10746",
        "CVE-2019-10747",
        "CVE-2019-20149",
        "CVE-2019-2391",
        "CVE-2020-7598",
        "CVE-2020-7610",
        "CVE-2020-7774",
        "CVE-2020-7788",
        "CVE-2021-23358",
        "CVE-2021-23440",
        "CVE-2021-32803",
        "CVE-2021-32804",
        "CVE-2021-37701",
        "CVE-2021-37712",
        "CVE-2021-37713",
        "CVE-2021-3820",
        "CVE-2021-44906",
        "CVE-2022-21680",
        "CVE-2022-21681",
        "CVE-2022-21803",
        "CVE-2022-24999",
        "CVE-2022-25883",
        "CVE-2022-3517",
        "CVE-2022-38900",
        "CVE-2023-25345",
        "CVE-2023-45311",
        "CVE-2024-28863",
        "CVE-2024-29041",
        "CVE-2024-4067",
        "CVE-2024-4068",
        "CVE-2024-43796",
        "CVE-2024-43799",
        "CVE-2024-43800",
        "CVE-2024-45296",
        "CVE-2024-45590",
        "CVE-2024-47764",
        "CVE-2024-52798",
        "CVE-2025-15284",
        "CVE-2025-5889",
        "CVE-2025-7339",
        "CVE-2026-23745",
        "CVE-2026-23950",
        "CVE-2026-24842",
        "CVE-2026-26960",
        "CVE-2026-26996",
        "CVE-2026-27601",
        "CVE-2026-27903",
        "CVE-2026-27904",
        "CVE-2026-29786",
        "CVE-2026-31802",
        "CVE-2026-33750",
        "CVE-2026-4867",
        "GHSA-c3m8-x3cg-qm2c",
        "GHSA-mh5c-679w-hh4r",
        "NSWG-ECO-101",
        "NSWG-ECO-445"
    ]
}
2026-06-14 15:07:39,159 - root_logger - INFO - {
    "repo_url": "https://github.com/OWASP/railsgoat.git",
    "stars": 922,
    "severity_statistics": {
        "CRITICAL": 6,
        "HIGH": 14,
        "MEDIUM": 19,
        "LOW": 4,
        "UNKNOWN": 0
    },
    "vulnerability_names": [
        "CVE-2026-22860",
        "CVE-2026-25500",
        "CVE-2026-26961",
        "CVE-2026-32762",
        "CVE-2026-33168",
        "CVE-2026-33169",
        "CVE-2026-33170",
        "CVE-2026-33173",
        "CVE-2026-33174",
        "CVE-2026-33176",
        "CVE-2026-33195",
        "CVE-2026-33202",
        "CVE-2026-33210",
        "CVE-2026-33306",
        "CVE-2026-33658",
        "CVE-2026-34230",
        "CVE-2026-34763",
        "CVE-2026-34785",
        "CVE-2026-34786",
        "CVE-2026-34826",
        "CVE-2026-34827",
        "CVE-2026-34829",
        "CVE-2026-34830",
        "CVE-2026-34831",
        "CVE-2026-34835",
        "CVE-2026-35611",
        "CVE-2026-39324",
        "CVE-2026-41316",
        "CVE-2026-42245",
        "CVE-2026-42246",
        "CVE-2026-42256",
        "CVE-2026-42257",
        "CVE-2026-42258",
        "CVE-2026-47240",
        "CVE-2026-47241",
        "CVE-2026-47242",
        "CVE-2026-47736",
        "CVE-2026-47737",
        "GHSA-2j22-pr5w-6gq8",
        "GHSA-46fp-8f5p-pf2m",
        "GHSA-c4rq-3m3g-8wgx",
        "GHSA-v2fc-qm4h-8hqv",
        "GHSA-wx95-c6cv-8532"
    ]
}
2026-06-14 15:07:39,159 - root_logger - INFO - The security scanner has finished its execution.
(.venv) uladzislau.mikheyenka ox_security_assignment %
```
