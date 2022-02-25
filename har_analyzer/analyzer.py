import json
import pandas as pd
from haralyzer import HarParser, HarPage, HarEntry


def main():
    with open('../50-site-2-accesses.har', 'r') as f:
        har_parser = HarParser(json.loads(f.read()))

    """
    Use the page title as the key to attribute analysis to specific pages

    Want to measure:
        - page cacheability
        - transferSize
        - # of requests that have a cache hit
        - max-age policy
        - cache policy in general

    Could do further analysis of each individual request made per page
    """

    for page in har_parser.pages:
        print(page.title)
        print(page.url)
        print('page size', page.page_size)
        print('page size trans', page.page_size_trans)
        for entry in page.entries:
            print(entry.url)
            for header in entry.response.headers:

        break

if __name__ == "__main__":
    main()
