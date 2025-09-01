import argparse




class Argparser:
    Parser: argparse.ArgumentParser
    args: dict


    def __init__(self, conf: dict) -> None:
        self.Parser = argparse.ArgumentParser(**conf['init'])
        for v in conf['args']:
            self.Parser.add_argument(*v['name_or_flags'], **v['setup'])


    def parse(self) -> dict:
        args: argparse.Namespace = self.Parser.parse_args()
        self.args = args.__dict__
        return self.args
