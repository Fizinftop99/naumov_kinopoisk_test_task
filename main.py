import copy
import json
import requests

import numpy as np
import pandas as pd
from scrapy.http import TextResponse


def parse_page(data) -> pd.DataFrame:
    df = pd.DataFrame()  # columns = ['russian', 'original', 'genre'])
    jsn = json.loads(data)["props"]["apolloState"]['data']
    keys = jsn.keys()

    def get_genre(key: str) -> str:
        assert '__typename' in jsn[key].keys(), 'no typename'
        return jsn[key].get('name', 'no')

    for i in keys:
        item: dict = copy.deepcopy(jsn[i])  # to avoid changing JSON data
        if '__typename' not in item.keys():
            continue

        if item['__typename'] in ('Film', 'TvSeries'):
            row: dict = item['title']
            row['rating'] = item['rating']['kinopoisk']['value']

            genre_keys = [j['__ref'] for j in item['genres']]
            row['genre'] = ', '.join([get_genre(k) for k in genre_keys])

            # getting release year:
            if item['__typename'] == 'Film':
                row['release_year'] = str(item['productionYear'])
            else:
                years: dict = item['releaseYears'][0]
                start = str(years['start'])
                end = str(years['end'] or '...')  # '...' if end == None
                row['release_year'] = start if start == end else start + '-' + end

            row.pop('__typename')  # removing useless column
            df = df.append(row, ignore_index=True)

    return df


def main():
    df = pd.DataFrame()

    page = 1
    while page <= 4:  # due to captcha
        curr_url = f'https://www.kinopoisk.ru/lists/movies/popular/?page={page}'
        res = requests.get(curr_url)
        print(res.status_code)
        selector = TextResponse(res.url, body=res.text, encoding='utf-8').selector.xpath('//*[@id="__NEXT_DATA__"]')

        data = selector.css('[id="__NEXT_DATA__"]::text').get()

        df = df.append(parse_page(data))
        page += 1

    df.insert(0, 'ranking_position', range(1, 1 + len(df)))
    df.to_csv('films_info.csv', index=False)


if __name__ == '__main__':
    main()
