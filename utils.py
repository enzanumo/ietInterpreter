import io
import re
import warnings
import xml.sax
from typing import Iterable, TextIO, Optional
from xml.sax.handler import ContentHandler
from xml.sax.saxutils import escape, unescape

__all__ = ['xmlize', 'xmlizes', 'ietlize', 'ietlizes']

ALL_TAGS = ('ul', 'tag', 'comment', 'star')

QUOTE_PATT = r"<q>\1</q>"  # formatted by re.sub
EMSP_PATT = "<emsp/>"

TAG_MAPPING = {'emsp': '　', 'sl': '[sl]', 'pg': '[pg]', }


class XmlizedIETContentHandler(ContentHandler):
    def __init__(self, use_western_quote=False):
        super(XmlizedIETContentHandler, self).__init__()
        # if set to False, read and clear self.this_row from outside.
        # if set to True(default), read self.io object.
        self.__use_io = True
        self.io = io.StringIO()
        self.this_row = ''

        if use_western_quote:
            self.quotes = '“”'
        else:
            self.quotes = '「」'

    def write(self, value, end='\n'):
        if self.__use_io:
            print(value, end=end, file=self.io)
        else:
            self.this_row = self.this_row + value + end

    def startElement(self, name, attrs):
        if name == 'q':
            self.this_row += self.quotes[0]
        elif name in TAG_MAPPING:
            self.this_row += TAG_MAPPING[name]
        elif name == 'save-label':
            text = attrs.getValue("text")
            self.write('[SAVELABLE TEXT="{}"]'.format(text))

    def characters(self, content):
        if content != '\n':
            self.this_row += (unescape(content))

    def endElement(self, name):
        if name == 'br':
            self.write('')
        elif name == 'q':
            self.this_row += self.quotes[1]
        elif name in ALL_TAGS:
            row = self.this_row
            if not row.endswith('\n'):
                row += '\n'
            if self.__use_io:
                self.this_row = ''
                self.write(row, end='')

    def endDocument(self):
        if self.__use_io:
            self.io.seek(0)


# class IgnoreErrorHandler(ErrorHandler):
#     def error(self, exception):
#         print('err', end='')
#         print(exception)
#
#     def fatalError(self, exception):
#         print('fatal', end='')
#         print(exception)


class IETWarning(Warning):
    pass


def _warn(msg: str, linenum: Optional[int] = None, filepath: Optional[str] = None):
    if linenum:
        if filepath:
            warnings.warn_explicit(msg, IETWarning, filename=filepath, lineno=linenum)
            return
        else:
            msg += " at line {}".format(linenum)
    warnings.warn(msg, IETWarning)
    return


def make_serif(serif: str) -> str:
    '''
    generates <emsp/> and <q></q>.
    :param serif: str like '「あれ？」'
    :return: str like '<q>あれ？</q>'
    '''
    if serif.startswith("　"):
        serif = serif.replace("　", EMSP_PATT, 1)
    return re.sub(r"^「(.*)」$", QUOTE_PATT, serif)


def make_ul(row: str, on_scr: dict) -> str:
    '''
    :param row: str like '「あれ？」[pg]', without \n
    :param on_scr: str like {'c': 'mizu'}
    :return: str like '<ul char="l: mizu"><q>あれ？</q><pg/></ul>\n'
    '''
    if on_scr:
        char_str = ' char="{}"'.format(", ".join(["{0}: {1}".format(k, v) for k, v in on_scr.items()]))
    else:
        char_str = ''
    if row.endswith('[sl]'):
        sl_str = '<sl/>'
        row = row[:-4]
    elif row.endswith('[pg]'):
        sl_str = '<pg/>'
        row = row[:-4]
    else:
        sl_str = ''
    return '<ul{c}>{s}{sl}</ul>\n'.format(c=char_str, s=make_serif(row), sl=sl_str)


def xmlizes(rows: Iterable[str], filepath=None) -> Iterable[str]:
    yield '<?xml version="1.0" encoding="utf-8"?>\n'
    yield '<iet converted-by="pyiet 1.0">\n'
    on_scr = {}
    pg_flag = 0
    linenum = 0
    for row in rows:
        linenum += 1
        # Remove \n
        if row.endswith('\n'):
            row = row[:-1]
        # escape
        row = escape(row)
        # Replace empty row
        if not row:
            yield '<br/>\n'
            continue

        # region startswith
        if row.startswith('//'):
            yield f"<comment>{row}</comment>\n"
            continue
        elif row.startswith('*'):
            yield f"<star>{row}</star>\n"
            continue
        elif row.startswith('['):
            if not row.endswith(']'):
                _warn('Row starts with "[" but not ended by "]": "{}"'.format(row), linenum, filepath)

            save_label_match = re.search(r'\[SAVELABLE TEXT="(.+)"]', row)
            if save_label_match:
                yield '<save-label text="{}"/>\n'.format(save_label_match.group(1))
                continue

            char_match = re.search(r'\[char_([clr]).*?st_([a-z]+?)\d.*]', row)
            if char_match:
                char_locat, char_name = char_match.groups()
                on_scr[char_locat] = char_name

            if 'char_all_clear' in row:
                on_scr.clear()

            yield f"<tag>{row}</tag>\n"
            continue
        # endregion

        # if row[0] not in ("「", '　'):
        #     warn(
        #         'Exceptional starting character:"{}" around "{}"'.format(row[0], row),
        #         linenum, filepath
        #     )

        if pg_flag == 0:
            yield "<p>\n"
            pg_flag = 1

        if row.endswith('[sl]'):
            yield make_ul(row, on_scr)
            continue
        elif row.endswith('[pg]'):
            yield make_ul(row, on_scr)
            yield "</p>\n"
            pg_flag = 0
            continue
        else:
            end_match = re.search(r'^.+\[([a-z]+)]$', row)
            if end_match and end_match.group(1) in ('l', 'r'):
                pass
            else:
                _warn('Row ends with no known tag: "{}"'.format(row), linenum, filepath)
            yield make_ul(row, on_scr)
            continue

    yield "</iet>\n"


def xmlize(iet_file: TextIO, /, filepath=None) -> Iterable[str]:
    filepath = filepath or iet_file.name or None
    return xmlizes(iet_file.readlines(), filepath)


def ietlize(xml_file: TextIO, /, use_western_quote=False) -> Iterable[str]:
    w = XmlizedIETContentHandler(use_western_quote)
    xml.sax.parse(xml_file, w)
    return w.io.readlines()


def ietlizes(rows: Iterable[str], use_western_quote=False) -> Iterable[str]:
    all_str = ''.join(rows)
    w = XmlizedIETContentHandler(use_western_quote)
    xml.sax.parseString(all_str, w)
    return w.io.readlines()
