import asyncio
import logging
from pprint import pprint


logger = logging.getLogger("ox_security_scanner")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


async def read_repos_urls() -> list[str]:
    repos_urls = []

    while True:
        try:
            repo_url = input()
        except EOFError:
            break

        repos_urls.append(repo_url)

    return repos_urls


async def main() -> None:
    repos_urls = await read_repos_urls()
    logger.info("The following repositories will be scanned:")
    pprint(repos_urls)


if __name__ == "__main__":
    logger.info("A security scan is about to start.")
    asyncio.run(main())
