import json
import time
import asyncio
import logging
import pathlib
import shutil
from urllib.parse import quote, unquote
from collections import Counter
from typing import Any, Mapping, MutableMapping

import aiohttp
from pydantic import BaseModel, Field


logger = logging.getLogger("root_logger")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)

if not logger.handlers:
    # NOTE: Don't add a handler if a module is imported multiple times.
    logger.addHandler(stream_handler)


GITHUB_REPO_STATISTICS_URL = "https://api.github.com/repos/{owner}/{repo_name}"
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")


class ScanStatistics(BaseModel):
    repo_url: str
    stars: int | None = 0
    severity_statistics: Mapping[str, int] = Field(default_factory=dict)
    vulnerability_names: list[str] = Field(default_factory=list)


async def obtain_repos_urls() -> list[str]:
    repos_urls = []

    while True:
        try:
            repo_url = input()
        except EOFError:
            break

        repos_urls.append(repo_url)

    logger.info("The total of %d repo URLs have been obtained.", len(repos_urls))
    return repos_urls


async def obtain_repo_stars(
    session: aiohttp.ClientSession,
    owner: str,
    repo_name: str,
) -> int | None:
    url = GITHUB_REPO_STATISTICS_URL.format(owner=owner, repo_name=repo_name)

    try:
        async with session.get(url) as response:
            response.raise_for_status()
            return int((await response.json())["stargazers_count"])
    except Exception:
        logger.error(
            "There was an error while obtaining the number of stars a repository has.",
            exc_info=True,
        )
        logger.info("The script will continue its execution normally.")
        return None


async def obtain_repo_url_to_stars_mapping(
    repos_urls: list[str],
) -> Mapping[str, int | None]:
    repo_url_to_stars_mapping: MutableMapping[str, int | None] = {}
    tasks: list[asyncio.Task] = []

    async with aiohttp.ClientSession() as session:
        for repo_url in repos_urls:
            owner, repo_name = await parse_repo_info(repo_url)
            tasks.append(
                asyncio.create_task(
                    obtain_repo_stars(
                        session,
                        owner,
                        repo_name,
                    )
                )
            )

        repos_stars = await asyncio.gather(*tasks)
        for repo_url, stars in zip(repos_urls, repos_stars):
            repo_url_to_stars_mapping[repo_url] = stars

    return repo_url_to_stars_mapping


async def parse_repo_info(repo_url: str) -> tuple[str, str]:
    """Given a repository URL, return its owner and a repository name.

    For example, given `https://github.com/OWASP/NodeGoat.git`, return ('OWASP', 'NodeGoat').
    """
    parts = tuple(part for part in repo_url.split("/") if part)
    owner = parts[-2]
    repo_name = parts[-1]
    repo_name = repo_name[:-4]
    return owner, repo_name


async def run_security_scans(
    artifacts_dir_path: pathlib.Path,
    repos_urls: list[str],
) -> None:
    tasks: tuple[asyncio.Task, ...] = tuple(
        asyncio.create_task(
            run_security_scan(
                artifacts_dir_path,
                str(time.time()),
                repo_url,
            )
        )
        for repo_url in repos_urls
    )
    await asyncio.gather(*tasks)


async def run_security_scan(
    prefix_path: pathlib.Path,
    timestamp: str,
    repo_url: str,
) -> None:
    # NOTE: A path can't contain slashes, so let's quote it.
    safe_repo_url = quote(repo_url, safe="")
    scan_name = f"{timestamp}-{safe_repo_url}.json"
    output_path = prefix_path / pathlib.Path(scan_name)

    command = [
        "trivy",
        "repository",
        "--quiet",
        "-f",
        "json",
        "-o",
        str(output_path),
        repo_url,
    ]
    logger.info(" ".join(command))
    process = await asyncio.create_subprocess_exec(
        *command,
        stderr=asyncio.subprocess.PIPE,
    )

    # NOTE:
    # So,
    # given the input repo url = https://github.com/OWASP/NodeGoat.git,
    # the following command will be run:
    # trivy repository --quiet -f json -o \
    # /security_scanner/artifacts/1781440863.1922567-https%3A%2F%2Fgithub.com%2FOWASP%2FNodeGoat.git.json \
    # https://github.com/OWASP/NodeGoat.git

    _, stderr = await process.communicate()

    if process.returncode != 0:
        logger.error("Trivy exited with %s status code.", process.returncode)
        if stderr:
            logger.error("%s", stderr.decode())


async def recreate_artifacts_dir() -> pathlib.Path:
    logger.debug("Artifacts directory is about to be recreated.")

    cwd = pathlib.Path.cwd()
    artifacts_dir_path = cwd / "artifacts"

    try:
        shutil.rmtree(artifacts_dir_path)
    except FileNotFoundError:
        pass

    artifacts_dir_path.mkdir(mode=0o777)
    return artifacts_dir_path


async def aggregate_the_statistics(
    repo_url: str,
    statistics_dict: dict[Any, Any],
) -> ScanStatistics:
    scan_statistics = ScanStatistics(repo_url=repo_url)
    severity_counts = Counter({severity: 0 for severity in SEVERITIES})
    vulnerability_names = set()

    for result in statistics_dict.get("Results", []):
        for vulnerability in result.get("Vulnerabilities", []):
            severity = vulnerability.get("Severity", "UNKNOWN")
            if severity not in severity_counts:
                severity = "UNKNOWN"

            severity_counts[severity] += 1
            name = vulnerability.get("VulnerabilityID") or "UNKNOWN"
            vulnerability_names.add(name)

    scan_statistics.severity_statistics = dict(severity_counts)
    scan_statistics.vulnerability_names = sorted(vulnerability_names)
    return scan_statistics


async def obtain_repo_url_to_statistics_mapping(
    artifacts_dir_path: pathlib.Path,
) -> MutableMapping[str, ScanStatistics]:
    repo_url_to_scan_statistics: MutableMapping[str, ScanStatistics] = {}

    for artifact_path in artifacts_dir_path.iterdir():
        try:
            with open(str(artifact_path), "rt") as file:
                statistics_dict = json.load(file)
        except (OSError, ValueError):
            logger.error(
                "There was an error while reading an artifact file.",
                exc_info=True,
            )
            logger.info("The script will continue its execution normally.")
            continue

        repo_url = artifact_path.stem
        repo_url = repo_url.split("/")[-1]
        repo_url = repo_url.split("-", 1)[-1]
        repo_url = unquote(repo_url)
        repo_url_to_scan_statistics[repo_url] = await aggregate_the_statistics(
            repo_url,
            statistics_dict,
        )

    return repo_url_to_scan_statistics


async def main() -> None:
    repos_urls = await obtain_repos_urls()
    logger.info("The following repositories will be scanned:")
    logger.info(json.dumps(repos_urls, indent=4))

    artifacts_dir_path = await recreate_artifacts_dir()
    await run_security_scans(artifacts_dir_path, repos_urls)
    repo_url_to_scan_statistics_mapping = await obtain_repo_url_to_statistics_mapping(
        artifacts_dir_path,
    )
    repo_url_to_stars_mapping = await obtain_repo_url_to_stars_mapping(repos_urls)
    for repo_url, stars in repo_url_to_stars_mapping.items():
        # NOTE: At this point, scan_statistics might be not present if a Trivy process has previously failed.
        scan_statistics = repo_url_to_scan_statistics_mapping.get(repo_url)
        if scan_statistics is not None:
            scan_statistics.stars = stars

    for scan_statistics in repo_url_to_scan_statistics_mapping.values():
        logger.info(scan_statistics.model_dump_json(indent=4))

    logger.info("The security scanner has finished its execution.")


if __name__ == "__main__":
    logger.info("The security scan is about to start.")
    asyncio.run(main())
