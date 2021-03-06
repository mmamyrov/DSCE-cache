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
    pages_df = pd.DataFrame(columns=['url', 'onContentLoad', 'onLoad', 'cumCacheTransferSize',
        'cumTransferSize', 'cacheTransferSize', '_transferSize', 'cumCacheCount', 'cumPageEntries',
        'cacheCount', 'pageEntries', 'cacheability', 'cacheOverTotal'])
    """url --> str, cumCacheTransferSize --> int, _transferSize --> int,
    cacheCount --> int, pageEntries --> int, cacheability --> float <= 1.0"""

    pages_df = pages_df.astype({ 'url': 'string', 'onContentLoad': 'float64', 'onLoad': 'float64',
        'cumCacheTransferSize': 'int64', 'cumTransferSize': 'int64', 'cacheTransferSize': 'int64', '_transferSize': 'int64',
        'cumCacheCount': 'int64', 'cumPageEntries': 'int64', 'cacheCount': 'int64',
        'pageEntries': 'int64', 'cacheability': 'float64', 'cacheOverTotal': 'float64' })
    pages_df.set_index('url', inplace=True)

    entries_df = pd.DataFrame(columns=['url', '_transferSize', 'cumTransferSize', 'fromCache',
        'statusCode', 'maxAge', 'cacheControl'])
    """url --> str, _transferSize --> int, fromCache --> bool, statusCode --> int,
    maxAge --> int, cacheControl --> object (set)"""

    entries_df = entries_df.astype({ 'url': 'string', '_transferSize': 'int64',
        'cumTransferSize': 'int64', 'fromCache': 'boolean', 'statusCode': 'int64',
        'maxAge': 'int64', 'cacheControl': 'object' })
    entries_df.set_index('url', inplace=True)

    print('dtypes', entries_df.dtypes)

    # Get all of the har_files with the specified interval
    har_files = glob.glob(f'../data/network-metrics-{r_interval}-*.har')
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
        pageTimings = page.pageTimings

        entriesCount = len(page.entries)
        pageTransferSize = 0
        pageCacheTransferSize = 0
        fromCacheCount = 0

        # print(pageTimings)

        # analyze each entry of the page
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

            # Store entry info in dataframe
            if entryUrl in entries_df.index:
                # entry exists in df, override previous record
                if _transferSize > 0:
                    # if transferSize is greater than 0, then it just came over the network
                    # and the record needs to be updated with latest info
                    entries_df.at[entryUrl, '_transferSize'] = _transferSize
                    entries_df.at[entryUrl, 'cumTransferSize'] += _transferSize

                entries_df.at[entryUrl, 'fromCache'] = fromCache
                entries_df.at[entryUrl, 'statusCode'] = entryStatusCode
                entries_df.at[entryUrl, 'maxAge'] = maxAge
                entries_df.at[entryUrl, 'cacheControl'] = ccList
            else:
                # entry doesn't exist in df. Append it
                entry_dict = {
                    'url': [entryUrl],
                    '_transferSize': [_transferSize],
                    'cumTransferSize': [_transferSize],
                    'fromCache': [fromCache],
                    'statusCode': [entryStatusCode],
                    'maxAge': [maxAge],
                    'cacheControl': [ccList]
                }

                # Append the entry to the df
                temp_entrydf = pd.DataFrame(entry_dict)
                temp_entrydf.set_index('url', inplace=True)
                entries_df = pd.concat([entries_df, temp_entrydf], ignore_index=False)

        ### End of entries loop

        ### Store page info in pandas
        if pageUrl in pages_df.index:
            # get the last instance of page information stored in the pages_df
            temp_pagedf = pd.DataFrame(pages_df.loc[[pageUrl]])
            temp_pagedf = temp_pagedf.iloc[[-1]].copy()

            # index row already exists, so just update it
            temp_pagedf.at[pageUrl, 'onContentLoad'] = pageTimings['onContentLoad']
            temp_pagedf.at[pageUrl, 'onLoad'] = pageTimings['onLoad']

            temp_pagedf.at[pageUrl, 'cumCacheTransferSize'] += pageCacheTransferSize
            temp_pagedf.at[pageUrl, 'cumTransferSize'] += pageTransferSize

            temp_pagedf.at[pageUrl, 'cacheTransferSize'] = pageCacheTransferSize
            temp_pagedf.at[pageUrl, '_transferSize'] = pageTransferSize

            temp_pagedf.at[pageUrl, 'cumCacheCount'] += fromCacheCount
            temp_pagedf.at[pageUrl, 'cumPageEntries'] += entriesCount

            temp_pagedf.at[pageUrl, 'cacheCount'] = fromCacheCount
            temp_pagedf.at[pageUrl, 'pageEntries'] = entriesCount

            # cacheTfSize = temp_pagedf.at[pageUrl, 'cacheTransferSize']
            # tfSize = temp_pagedf.at[pageUrl, '_transferSize']

            # in case pageTransferSize == 0, then set it to one to get the ratio
            temp_pagedf.at[pageUrl, 'cacheability'] = pageCacheTransferSize / 1
            temp_pagedf.at[pageUrl, 'cacheOverTotal'] = 0.0

            if pageTransferSize > 0.0:
                temp_pagedf.at[pageUrl, 'cacheability'] = pageCacheTransferSize / pageTransferSize

            if pageCacheTransferSize > 0.0:
                temp_pagedf.at[pageUrl, 'cacheOverTotal'] = pageCacheTransferSize / (pageCacheTransferSize + pageTransferSize)

            pages_df = pd.concat([pages_df, temp_pagedf], ignore_index=False)
            # print(pages_df.loc[[pageUrl]].tail())
        else:
            # create a new index row with the requested url
            page_dict = {
                'url': [pageUrl],
                'onContentLoad': [pageTimings['onContentLoad']],
                'onLoad': [pageTimings['onLoad']],
                'cumCacheTransferSize': [pageCacheTransferSize],
                'cumTransferSize': [pageTransferSize],
                'cacheTransferSize': [pageCacheTransferSize],
                '_transferSize': [pageTransferSize],
                'cumCacheCount': [fromCacheCount],
                'cumPageEntries': [entriesCount],
                'cacheCount': [fromCacheCount],
                'pageEntries': [entriesCount],
                'cacheability': [0.0],
                'cacheOverTotal': [0.0],
            }

            if pageTransferSize > 0.0 and pageCacheTransferSize > 0.0:
                page_dict['cacheability'] = pageCacheTransferSize / pageTransferSize

            if pageCacheTransferSize > 0.0:
                page_dict['cacheOverTotal'] = pageCacheTransferSize / (pageCacheTransferSize + pageTransferSize)

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
