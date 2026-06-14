import asyncio
import logging
from pprint import pprint
from typing import MutableMapping

import aiohttp


logger = logging.getLogger("root_logger")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


GITHUB_REPO_STATISTICS_URL = "https://api.github.com/repos/{owner}/{repo_name}"


async def read_repos_urls() -> list[str]:
    """Read repositories to be scanned from STDIN."""
    repos_urls = []

    while True:
        try:
            repo_url = input()
        except EOFError:
            break

        repos_urls.append(repo_url)

    return repos_urls


async def get_repo_stars(
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


async def parse_repo_info(repo_url: str) -> tuple[str, str]:
    """Given a repository URL, return its owner and a repository name.
    For example, given `https://github.com/OWASP/NodeGoat.git`, return ('OWASP', 'NodeGoat').
    """
    parts = tuple(part for part in repo_url.split("/") if part)
    owner = parts[-2]
    repo_name = parts[-1]
    repo_name = repo_name[:-4]
    return owner, repo_name


async def main() -> None:
    repos_urls = await read_repos_urls()
    logger.info("The following repositories will be scanned:")
    pprint(repos_urls)

    repo_url_to_the_number_of_stars_mapping: MutableMapping[str, int | None] = {}

    async with aiohttp.ClientSession() as session:
        get_repo_stars_tasks: list[asyncio.Task] = []

        for repo_url in repos_urls:
            owner, repo_name = await parse_repo_info(repo_url)
            get_repo_stars_tasks.append(
                asyncio.create_task(
                    get_repo_stars(
                        session,
                        owner,
                        repo_name,
                    )
                )
            )

        repos_stars = await asyncio.gather(*get_repo_stars_tasks)
        # NOTE: `asyncio.gather` preserves the ordering.
        # So, we rely on this ordering and use `zip`.
        for repo_url, stars in zip(repos_urls, repos_stars):
            repo_url_to_the_number_of_stars_mapping[repo_url] = stars

    pprint(repo_url_to_the_number_of_stars_mapping)


if __name__ == "__main__":
    logger.info("A security scan is about to start.")
    asyncio.run(main())
