
from pathlib import Path

import utils


def iet2xml(file: Path):
    f = file.open(mode='r', encoding='utf-8-sig')
    w = file.with_suffix(".xml").open(mode='w', encoding='utf-8')
    w.writelines(
        utils.xmlizes(f.readlines(), str(file.absolute()))
    )
    f.close()
    w.close()

def xml2iet(file: Path):
    f = file.open(mode='r', encoding='utf-8-sig')
    w = file.with_suffix(".iet.restored").open(mode='w', encoding='utf-8-sig')
    w.writelines(
        utils.ietlize(f)
    )
    f.close()
    w.close()


if __name__ == '__main__':
    path = Path(".")
    for iet in path.glob("./*.iet"):
        # print('Processing: {}'.format(iet.name), flush=True, file=sys.stderr)
        iet2xml(iet)
    for xml in path.glob("./*.xml"):
        xml2iet(xml)
