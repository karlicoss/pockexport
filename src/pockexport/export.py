from __future__ import annotations

import argparse
import json
import logging

import hpikit.cli.export as cli
import pocket  # type: ignore[import-untyped]
from hpikit.json import Json
from kloggy import get_logger
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

## useful for debugging
# from http.client import HTTPConnection
# HTTPConnection.debuglevel = 1
###

logger = get_logger(__name__)


def _retry_if(_e: BaseException) -> bool:
    # NOTE: since pocket is shutting down soon, no point figuring out a nice/careful retry strategy -- just retry on all errors
    return True
    # seems to randomly occur at times?
    # return 'Internal server error' in str(e)


class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.api = pocket.Pocket(*args, **kwargs)

    def export_json(self) -> Json:
        # When pocket web app queries api it's got some undocumented parameters, so this small hack allows us to use them too
        # e.g. {"images":1,"videos":1,"tags":1,"rediscovery":1,"annotations":1,"authors":1,"itemTopics":1,"meta":1,"posts":1,"total":1,"state":"unread","offset":0,"sort":"newest","count":24,"forceaccount":1,"locale_lang":"en-US"}
        @pocket.method_wrapper
        def get(self, **kwargs):
            pass

        @retry(
            retry=retry_if_exception(predicate=_retry_if),
            wait=wait_exponential(max=60 * 10),  # 10 mins
            stop=stop_after_attempt(10),
            before_sleep=before_sleep_log(logger, logging.WARNING),
        )
        def get_with_retry(*args, **kwargs) -> Json:
            res, _headers = get(*args, **kwargs)
            error = res.get('error')
            if error is None:
                return res
            raise RuntimeError(error)

        all_items: dict[str, Json] = {}

        first_res: Json | None = None
        total: int | None = None

        while True:
            offset = len(all_items)
            logger.info(f'retrieving from {offset=} (expected {total=})')
            res = get_with_retry(
                self.api,
                images=1,
                videos=1,
                tags=1,
                rediscovery=1,
                annotations=1,
                authors=1,
                itemOptics=1,
                meta=1,
                posts=1,
                total=1,
                forceaccount=1,
                offset=offset,
                count=30,  # max count per request according to api docs
                state='all',
                sort='newest',
                detailType='complete',
            )
            if first_res is None:
                first_res = res

            total = int(res['total'])

            new_items: dict[str, Json] = res['list']
            if len(new_items) == 0:
                break

            all_items.update(new_items)

        first_res['list'] = all_items  # eh, hacky, but not sure what's a better way
        return first_res


def get_json(**params) -> Json:
    return Exporter(**params).export_json()


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    params = cli.get_params(parser, args)

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    cli.dump(js, path=args.path)


def make_parser() -> argparse.ArgumentParser:
    parser = cli.make_parser(
        description='Export your personal Pocket data, **including highlights** as JSON.',
        params=['consumer_key', 'access_token'],
        extra_usage='''
You can also import `pockexport.export` as a module and call `get_json` function directly to get raw JSON.
''',
    )
    return parser


if __name__ == '__main__':
    main()
