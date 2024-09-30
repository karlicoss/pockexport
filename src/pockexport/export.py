#!/usr/bin/env python3
import json

import pocket  # type: ignore


class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.api = pocket.Pocket(*args, **kwargs)

    def export_json(self):
        # When pocket web app queries api it's got some undocumented parameters, so this small hack allows us to use them too
        # e.g. {"images":1,"videos":1,"tags":1,"rediscovery":1,"annotations":1,"authors":1,"itemTopics":1,"meta":1,"posts":1,"total":1,"state":"unread","offset":0,"sort":"newest","count":24,"forceaccount":1,"locale_lang":"en-US"}
        @pocket.method_wrapper
        def get(self, **kwargs):
            pass

        # apparently no pagination?
        res = get(
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
            state='all',
            sort='newest',
            detailType='complete',
        )
        return res[0]


def get_json(**params):
    return Exporter(**params).export_json()


def main() -> None:
    parser = make_parser()
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


def make_parser():
    from .exporthelpers.export_helper import Parser, setup_parser
    parser = Parser('Export your personal Pocket data, *including highlights* as JSON.')
    setup_parser(
        parser=parser,
        params=['consumer_key', 'access_token'],
        extra_usage='''
You can also import ~pockexport.export~ as a module and call ~get_json~ function directly to get raw JSON.
''')
    return parser


if __name__ == '__main__':
    main()
