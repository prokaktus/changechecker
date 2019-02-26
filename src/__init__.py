import json
import sqlite3

import requests
from pyquery import PyQuery as pq


TIMEOUT = 60


conn = sqlite3.connect('history.db')


class EmptySelectorError(Exception):
    pass


def create_db():
    with conn:
        conn.execute('''
        Create table if not exists provider
        (slug text primary key, content text)
        ''')

def insert_content(provider, content):
    with conn:
        conn.execute('''
        insert or replace into provider (slug, content) values (?, ?)
        ''', (provider, content, ))


def read_config(name=None):
    name = name or '.config.json'
    with open(name, 'r') as f:
        return json.load(f)


def has_changes(provider, content):
    with conn:
        cur = conn.execute('select content from provider where slug = ?',
                           (provider, ))
        old_content = cur.fetchone()
        old_content = old_content and old_content[0]
        return content != old_content


if __name__ == '__main__':
    create_db()
    config = read_config()
    for provider, checks in config.items():
        changed = False
        for check in checks:
            try:
                url, selector = check['url'], check['selector']
                
                if not url or not selector:
                    continue

                resp = requests.get(url, timeout=TIMEOUT)
                resp.raise_for_status()

                text = resp.text
                query = pq(text)

                items = query(selector)
                if not items:
                    raise EmptySelectorError
                item = items[0]

                content = item.text_content().strip()
                if has_changes(provider, content):
                    print('Content has changed')
                    changed = True

                insert_content(provider, content)

            except Exception as e:
                # TODO: logger config
                print(e)

