import sys
import glob
import json
import re
import os
from typing import Tuple
import pandas as pd
from pandas.core.frame import DataFrame
from tqdm import tqdm
from haralyzer import HarParser, HarPage, HarEntry

# TODO: need to keep track of the number of requests made for each entry and page
# TODO: Should keep track of all max-ages returned

def main(args):
    """
    Use the page title as the key/index to attribute analysis to specific pages

    Want to measure:
        - page cacheability
        - transferSize
        - # of requests that have a cache hit
        - max-age policy
        - cache policy in general

    Could do further analysis of each individual request made per page
    """

    # set the cwd to file's directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    r_interval = args[0]


    ### create the two dataframes: (1) pages, (2) entries
    pages_df = pd.DataFrame(columns=['url', 'cacheTransferSize', '_transferSize', 'cacheCount', 'pageEntries', 'cacheability'])
    """url --> str, cacheTransferSize --> int, _transferSize --> int,
    cacheCount --> int, pageEntries --> int, cacheability --> float <= 1.0"""

    pages_df = pages_df.astype({ 'url': 'string', 'cacheTransferSize': 'int64',
        '_transferSize': 'int64', 'cacheCount': 'int64', 'pageEntries': 'int64',
        'cacheability': 'float64' })
    pages_df.set_index('url', inplace=True)

    entries_df = pd.DataFrame(columns=['url', '_transferSize', 'fromCache',
        'statusCode', 'maxAge', 'cacheControl'])
    """url --> str, _transferSize --> int, fromCache --> bool, statusCode --> int,
    maxAge --> int, cacheControl --> object (set)"""

    entries_df = entries_df.astype({ 'url': 'string', '_transferSize': 'int64', 'fromCache': 'boolean',
        'statusCode': 'int64', 'maxAge': 'int64', 'cacheControl': 'object' })
    entries_df.set_index('url', inplace=True)

    print('dtypes', entries_df.dtypes)

    # Get all of the har_files with the specified interval
    har_files = glob.glob(f'../data/50-site-metrics-{r_interval}-*.har')
    har_files.sort()

    print(har_files)

    for har_file in tqdm(har_files):
        pages_df, entries_df = parse_har_file(har_file, pages_df, entries_df)

    # print(pages_df.tail(10))
    # print(pages_df)
    # print(entries_df[entries_df['fromCache'] == True].tail(10))

    # Save the results of pages and entries dataframes as CSV files
    results_dir = 'results'
    pages_result_file = f'../{results_dir}/pages_analysis_{r_interval}.csv'
    entries_result_file = f'../{results_dir}/entries_analysis_{r_interval}.csv'

    pages_df.to_csv(pages_result_file)
    entries_df.to_csv(entries_result_file)



def parse_har_file(har_file: str, pages_df: DataFrame, entries_df: DataFrame) -> Tuple[DataFrame, DataFrame]:
    with open(har_file, 'r') as f:
        har_parser = HarParser(json.loads(f.read()))

    for page in tqdm(har_parser.pages, leave=False):
        # init page variables
        pageUrl = page.url
        entriesCount = len(page.entries)
        pageTransferSize = 0
        pageCacheTransferSize = 0
        fromCacheCount = 0

        for entry in page.entries:
            entryUrl = entry.url
            entryStatusCode = entry.response.status

            # Retrieve the cacheControl
            cacheControl = entry.response.cacheControl
            ccList = set()
            maxAge = -1
            if cacheControl:
                ccList = set([x.strip() for x in cacheControl.split(',')])

                # find the 'max-age' or 's-maxage' parameter of cache-control
                # and extract it if it exists
                for param in ccList:
                    if ('max-age' in param) or ('s-maxage' in param):
                        maxAge = re.findall(r'\b\d+\b', param)[0]
                        break

                # print('=======================')
                # print('cacheControl: ', ccList)
                # print('=======================')

            # handle transfer size
            _transferSize: int = entry.response.get('_transferSize', 0)
            if _transferSize > 0:
                pageTransferSize += _transferSize

            # handle fromCache marker
            fromCache: bool = entry.get('_fromDiskCache', False)
            if fromCache:
                fromCacheCount += 1

                if entryUrl in entries_df.index:
                    entryTfSize = entries_df.at[entryUrl, '_transferSize']
                    pageCacheTransferSize += entryTfSize

            # Store entry info in datafram
            if entryUrl in entries_df.index:
                # entry exists in df, override previous record
                entries_df.at[entryUrl, '_transferSize'] += _transferSize
                entries_df.at[entryUrl, 'fromCache'] = fromCache
                entries_df.at[entryUrl, 'statusCode'] = entryStatusCode
                entries_df.at[entryUrl, 'maxAge'] = maxAge
                entries_df.at[entryUrl, 'cacheControl'] = ccList
            else:
                # entry doesn't exist in df. Append it
                entry_dict = {
                    'url': [entryUrl],
                    '_transferSize': [_transferSize],
                    'fromCache': fromCache,
                    'statusCode': entryStatusCode,
                    'maxAge': maxAge,
                    'cacheControl': [ccList]
                }

                # Append the entry to the df
                temp_entrydf = pd.DataFrame(entry_dict)
                temp_entrydf.set_index('url', inplace=True)
                entries_df = pd.concat([entries_df, temp_entrydf], ignore_index=False)

        ### End of entries loop

        ### Store page info in pandas
        if pageUrl in pages_df.index:
            # index row already exists, so just update it
            pages_df.at[pageUrl, 'cacheTransferSize'] += pageCacheTransferSize
            pages_df.at[pageUrl, '_transferSize'] += pageTransferSize
            pages_df.at[pageUrl, 'cacheCount'] += fromCacheCount
            pages_df.at[pageUrl, 'pageEntries'] += entriesCount

            cacheTfSize = pages_df.at[pageUrl, 'cacheTransferSize']
            tfSize = pages_df.at[pageUrl, '_transferSize']

            if tfSize > 0.0:
                pages_df.at[pageUrl, 'cacheability'] =  cacheTfSize / tfSize
        else:
            # create a new index row with the requested url
            page_dict = {
                'url': [pageUrl],
                'cacheTransferSize': [pageCacheTransferSize],
                '_transferSize': [pageTransferSize],
                'cacheCount': [fromCacheCount],
                'pageEntries': [entriesCount],
                'cacheability': [0.0],
            }

            if pageTransferSize > 0.0 and pageCacheTransferSize > 0.0:
                page_dict['cacheability'] = pageCacheTransferSize / pageTransferSize

            ### Append the page to the df
            temp_pagedf = pd.DataFrame(page_dict)
            temp_pagedf.set_index('url', inplace=True)
            pages_df = pd.concat([pages_df, temp_pagedf], ignore_index=False)

    ### End of page loop
    return pages_df, entries_df


if __name__ == "__main__":
    if len(sys.argv) < 2:
        exit("No interval specified")

    main(sys.argv[1:])
