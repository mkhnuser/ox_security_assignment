import json
import time
import asyncio
import logging
import pathlib
import shutil
from urllib.parse import quote

from typing import Mapping, MutableMapping

import aiohttp


logger = logging.getLogger("root_logger")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


GITHUB_REPO_STATISTICS_URL = "https://api.github.com/repos/{owner}/{repo_name}"
TRIVY_SECURITY_SCAN_COMMAND = (
    "trivy repository --quiet -f json -o {prefix_path}/{scan_name}.json {repo_url}"
)


async def obtain_repos_urls() -> list[str]:
    """Obtain repositories to be scanned from STDIN."""
    repos_urls = []

    while True:
        try:
            repo_url = input()
        except EOFError:
            break

        repos_urls.append(repo_url)

    logger.info("The total of %d repo URLs has been obtained.", len(repos_urls))
    return repos_urls


async def obtain_repo_stars(
    session: aiohttp.ClientSession,
    owner: str,
    repo_name: str,
) -> int | None:
    """Obtain the number of stars a given repository has. If there is an error, return the default value."""

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
    """Obtain a mapping between a repo URL and the number of stars it has."""

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
    """Run a security scan on all repo urls."""
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
    """Run a trivy security scan on a given repo url."""

    # NOTE: A path can't contain slashes, so let's quote it.
    safe_repo_url = quote(repo_url, safe="")
    scan_name = f"{timestamp}-{safe_repo_url}"

    command = TRIVY_SECURITY_SCAN_COMMAND.format(
        prefix_path=str(prefix_path).rstrip("/"),
        scan_name=scan_name,
        repo_url=repo_url,
    )
    logger.info(command)

    # NOTE:
    # So,
    # given the input repo url = https://github.com/OWASP/NodeGoat.git,
    # the following command will be run:
    # trivy repository --quiet -f json -o \
    # /security_scanner/artifacts/1781440863.1922567-https%3A%2F%2Fgithub.com%2FOWASP%2FNodeGoat.git.json \
    # https://github.com/OWASP/NodeGoat.git

    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    _, stderr = await process.communicate()

    if stderr:
        logger.error("%r exited with %s.", command, process.returncode)
        logger.error("%s", stderr.decode())


async def prepare_artifacts_dir() -> pathlib.Path:
    logger.debug("Artifacts directory is about to be recreated.")

    cwd = pathlib.Path.cwd()
    artifacts_dir_path = cwd / "artifacts"

    try:
        shutil.rmtree(artifacts_dir_path)
    except FileNotFoundError:
        pass

    artifacts_dir_path.mkdir(mode=0o777)
    return artifacts_dir_path


async def main() -> None:
    repos_urls = await obtain_repos_urls()
    logger.info("The following repositories will be scanned:")
    logger.info(json.dumps(repos_urls, indent=4))

    repo_url_to_stars_mapping = await obtain_repo_url_to_stars_mapping(repos_urls)

    artifacts_dir_path = await prepare_artifacts_dir()
    await run_security_scans(artifacts_dir_path, repos_urls)


if __name__ == "__main__":
    logger.info("A security scan is about to start.")
    asyncio.run(main())
