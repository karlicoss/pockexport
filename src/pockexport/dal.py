from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import NamedTuple

from .exporthelpers import dal_helper
from .exporthelpers.dal_helper import (
    Json,
    PathIsh,
    datetime_aware,
    fromisoformat,
    pathify,
)


class Highlight(NamedTuple):
    json: Json

    @property
    def text(self) -> str:
        return self.json['quote']

    @property
    def created(self) -> datetime_aware:
        created_at_s = self.json['created_at']
        if created_at_s.endswith('Z'):
            # FIXME not convinced timestamp is correct here?
            # tested with item highlighted at 2024-09-30 at 00:53 UTC and it appeared as 2024-09-29T19:53:35.000Z in export??
            return fromisoformat(created_at_s)
        else:
            # older format (pre September 2024)
            dt = datetime.strptime(self.json['created_at'], '%Y-%m-%d %H:%M:%S')
            return dt.replace(tzinfo=timezone.utc)


class Article(NamedTuple):
    json: Json

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
    def added(self) -> datetime_aware:
        return datetime.fromtimestamp(int(self.json['time_added']), tz=timezone.utc)

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
        for j in self.raw()['list'].values():
            # means "item should be deleted" according to api?? https://getpocket.com/developer/docs/v3/retrieve
            # started happening around September 2024... in this case there is no data inside except item id
            if j['status'] == '2':
                continue
            yield Article(j)


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
        assert a.url is not None
        assert a.title is not None
        assert a.pocket_link is not None
        assert a.added is not None
        for h in a.highlights:
            h.text  # noqa: B018
            h.created  # noqa: B018


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
