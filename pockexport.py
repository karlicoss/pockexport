#!/usr/bin/env python3
import json

import pocket # type: ignore

class Exporter:
    def __init__(self, *args, **kwargs) -> None:
        self.api = pocket.Pocket(*args, **kwargs)

    def export_json(self):
        # ok, apparently no pagination?
        return self.api.get()[0] # 0 is data, 1 is headers


def get_json(**params):
    return Exporter(**params).export_json()


def main():
    from export_helper import setup_parser
    import argparse
    # TODO literate documentation from help
    parser = argparse.ArgumentParser("Export/takeout for your personal pocker data")
    setup_parser(parser=parser, params=['consumer_key', 'access_token'])
    args = parser.parse_args()

    params = args.params
    dumper = args.dumper

    j = get_json(**params)
    js = json.dumps(j, ensure_ascii=False, indent=1)
    dumper(js)


if __name__ == '__main__':
    main()
