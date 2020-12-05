#!/usr/bin/env python

import argparse
from collections import Counter
from getpass import getuser
from os import getenv

import matplotlib.pyplot as plt
from progress.bar import IncrementalBar
from textblob import TextBlob, exceptions
import vk


TOKEN = getenv('VK_TOKEN',
               open(f"/home/{getuser()}/Documents/access_token.txt").read())
API_V = 5.122


# Argparse handling method
def parse():
    parser = argparse.ArgumentParser()

    parser.add_argument('-id',
                        type=int,
                        default=None,
                        help='VK ID of target. Default = None')
    parser.add_argument('-url',
                        type=str,
                        default=None,
                        help="VK URL of target. Default = None")
    parser.add_argument('-pie',
                        action='store_true',
                        help="Print pie charts of results")

    return parser.parse_args()


def names_translate(word: TextBlob, arr: list):
    """Append to resulting array translated word
       if it was not in Russian. If it was empty, append Not defined
    """
    try:
        if word:
            if word.detect_language() != 'ru':
                arr.append(word.translate(to='ru').string)
            else:
                arr.append(word.title().string)
        else:
            arr.append("Город не указан")
    except exceptions.NotTranslated:
        arr.append(word.string)


# Converting list of cities' names to tuple of frequencies and labels
def get_pie_data(arr: list):
    popular_cities = [c[0] for c in Counter(arr).most_common(5)]

    # Leave only 5 most popular results
    excl_arr = list(map(lambda x: x if x in popular_cities
                        else "Другие города", arr))
    excl_arr_counter = dict(Counter(excl_arr))

    return (excl_arr_counter.values(), excl_arr_counter.keys())


def pie_chart(cities: list, homes: list, print_pie_chart: bool):
    if not print_pie_chart:
        return

    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    fig.canvas.set_window_title("Friends' cities")

    cities_data, homes_data = get_pie_data(cities), get_pie_data(homes)

    for i, data in enumerate([cities_data, homes_data]):
        expl = ([0.1, 0.05] + len(data[0])*[0])[:len(data[0])]
        axes[i].pie(data[0], labels=data[1],
                    startangle=90, explode=expl,
                    autopct="%.1f%%", pctdistance=0.85)
        axes[i].set(title="Текущий город" if not i else "Родной город")

    plt.subplots_adjust(wspace=0.4)
    plt.show()
    return 0


def get_friends_cities(target_id, print_pie_chart: bool):
    cities = []
    homes = []

    session = vk.Session(access_token=TOKEN)
    api = vk.API(session, lang='ru', v=API_V)
    try:
        # convert URL to digit ID
        if type(target_id) == str and target_id.startswith('https://'):
            target_id = api.users.get(user_ids=target_id[15:])[0]['id']
        friends_ids = api.friends.get(user_id=target_id)['items']
    except vk.exceptions.VkAPIError as e:
        print(f'Something went wrong with https://vk.com/id{target_id}\n'
              f'{e.code} - {e.message}')
        return 1

    # User has no friends
    if not friends_ids:
        print(f'https://vk.com/id{target_id} has no friends :(')
        return 1

    with IncrementalBar('Processing', max=len(friends_ids),
                        suffix='%(percent)d%%') as bar:
        for friend_id in friends_ids:
            # Getting user's friend home town and city, else ""
            resp = api.users.get(user_id=friend_id,
                                 fields=['city', 'home_town'])[0]

            city = TextBlob(dict(resp.pop('city', '')).pop('title', ''))
            home_town = TextBlob(resp.get('home_town', ''))

            names_translate(city, cities)
            names_translate(home_town, homes)

            bar.next()

    print('\nCurrent city:')
    for i in Counter(cities).most_common(5):
        print(f'{i[0]:15} - {round(i[1]/len(cities)*100, 2)}%')

    print('\nHome city:')
    for i in Counter(homes).most_common(5):
        print(f'{i[0]:15} - {round(i[1]/len(homes)*100, 2)}%')

    pie_chart(cities, homes, print_pie_chart)

    return 0


def main():
    args = parse()
    print()
    if not args.id and not args.url:
        print("No arguments have been passed! Specify ID or URL.")
        return 1
    get_friends_cities(args.id if args.id else args.url, args.pie)


if __name__ == "__main__":
    main()
