#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator, NamedTuple, Sequence

from .exporthelpers import dal_helper
from .exporthelpers.dal_helper import Json, PathIsh, pathify


# TODO FIXME are times in utc? not mentioned anywhere...

class Highlight(NamedTuple):
    json: Any

    @property
    def text(self) -> str:
        return self.json['quote']

    @property
    def created(self) -> datetime:
        return datetime.strptime(self.json['created_at'], '%Y-%m-%d %H:%M:%S')


class Article(NamedTuple):
    json: Any

    @property
    def url(self) -> str:
        return self.json['given_url']

    @property
    def title(self) -> str:
        gt = self.json['given_title']
        if gt != '':
            return gt
        else:
            return self.json['resolved_title']

    @property
    def pocket_link(self) -> str:
        return 'https://app.getpocket.com/read/' + self.json['item_id']

    @property
    def added(self) -> datetime:
        return datetime.fromtimestamp(int(self.json['time_added']))

    @property
    def highlights(self) -> Sequence[Highlight]:
        raw = self.json.get('annotations', [])
        # TODO warn an link how to get highlights?
        return list(map(Highlight, raw))

    # TODO add tags?


class DAL:
    def __init__(self, sources: Sequence[PathIsh]) -> None:
        self.sources = list(map(pathify, sources))

    def raw(self) -> Json:
        last = max(self.sources)
        # TODO not sure if worth elaborate merging logic?
        # TODO not sure if this should be more defensive against empty sources?
        return json.loads(last.read_text())

    def articles(self) -> Iterator[Article]:
        yield from map(Article, self.raw()['list'].values())


def _get_test_sources() -> Sequence[PathIsh]:
    testdata = Path(__file__).absolute().parent.parent.parent / 'testdata'
    files = list(testdata.rglob('pocket-collect-list.json'))
    assert len(files) > 0
    return files


def test() -> None:
    dal = DAL(_get_test_sources())
    articles = list(dal.articles())
    assert len(articles) == 10
    for a in articles:
        assert a.url         is not None
        assert a.title       is not None
        assert a.pocket_link is not None
        assert a.added       is not None
        for h in a.highlights:
            h.text
            h.created


def demo(dal: DAL) -> None:
    articles = list(dal.articles())
    for a in articles:
        x = f"""
{a.title}
  {len(a.highlights)} highlights
  {a.pocket_link}
""".lstrip()
        print(x)


if __name__ == '__main__':
    dal_helper.main(DAL=DAL, demo=demo)
