from __future__ import annotations

import json
from collections.abc import Iterator, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple
from zoneinfo import ZoneInfo

from .exporthelpers import dal_helper
from .exporthelpers.dal_helper import (
    Json,
    datetime_aware,
    pathify,
)

# Pocket configures the annotations database session as US/Central.
# Its /v3 transformer documents Central timestamps and emits ISO strings.
# The observed API timestamps therefore contain Central wall time with a misleading UTC "Z".
# Use America/Chicago so daylight-saving transitions are preserved.
# This is also validated against zip data export from Pocket.
# https://github.com/Pocket/pocket-monorepo/blob/542fd269a750a446f2ae0367acf270fd517a3416/servers/annotations-api/src/config/index.ts#L62-L78
# https://github.com/Pocket/pocket-monorepo/blob/542fd269a750a446f2ae0367acf270fd517a3416/servers/annotations-api/src/database/client.ts#L50-L80
# https://github.com/Pocket/pocket-monorepo/blob/542fd269a750a446f2ae0367acf270fd517a3416/servers/v3-proxy-api/src/graph/get/toRest.ts#L230-L253
_CENTRAL = ZoneInfo('America/Chicago')


class Highlight(NamedTuple):
    json: Json

    @property
    def text(self) -> str:
        return self.json['quote']

    @property
    def created(self) -> datetime_aware:
        created_at_s = self.json['created_at']
        if created_at_s.endswith('Z'):
            # Pocket's API labels US/Central wall time as UTC.
            dt = datetime.fromisoformat(created_at_s.removesuffix('Z'))
        else:
            # older format (pre September 2024)
            # This is also US/Central wall time.
            dt = datetime.strptime(self.json['created_at'], '%Y-%m-%d %H:%M:%S')
        return dt.replace(tzinfo=_CENTRAL).astimezone(UTC)


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
        return datetime.fromtimestamp(int(self.json['time_added']), tz=UTC)

    @property
    def highlights(self) -> Sequence[Highlight]:
        raw = self.json.get('annotations', [])
        # TODO warn an link how to get highlights?
        return list(map(Highlight, raw))

    # TODO add tags?


class DAL:
    def __init__(self, sources: Sequence[Path | str]) -> None:
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


def _get_test_sources() -> Sequence[Path | str]:
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


def test_highlight_timezone() -> None:
    def created(created_at: str) -> datetime:
        return Highlight({'created_at': created_at}).created

    assert created('2019-09-25 18:20:00') == datetime(2019, 9, 25, 23, 20, tzinfo=UTC)
    assert created('2024-09-29T19:53:35.000Z') == datetime(2024, 9, 30, 0, 53, 35, tzinfo=UTC)
    assert created('2024-01-15T12:00:00.000Z') == datetime(2024, 1, 15, 18, tzinfo=UTC)


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
