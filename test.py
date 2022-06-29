import io
import unittest
from pathlib import Path

import utils


class MyTestCase(unittest.TestCase):
    def test_xml_equals_iet(self):
        self.maxDiff = None
        files = Path('.').glob('./scripts/*/*.iet')
        for file in files:
            filepath = str(file.absolute())
            with self.subTest(file=filepath):
                r = file.open(mode='r', encoding='utf-8-sig')
                xml = io.StringIO()
                xml.writelines(
                    utils.xmlize(r, filepath=filepath)
                )
                xml.seek(0)

                r_iet = io.StringIO()

                r_iet.writelines(
                    utils.ietlize(xml)
                )
                r_iet.seek(0)
                r.seek(0)

                self.assertEqual(r.read(), r_iet.read())
                r.close()
                xml.close()
                r_iet.close()

    def test_xml_string_equals_iet_string(self):
        self.maxDiff = None
        files = Path('.').glob('./scripts/*/*.iet')
        for file in files:
            filepath = str(file.absolute())
            with self.subTest(file=filepath):
                r = file.open(mode='r', encoding='utf-8-sig')
                restored = ''.join(
                    utils.ietlizes(
                        utils.xmlizes(r.readlines())
                    )
                )
                r.seek(0)
                orig = r.read()

                self.assertEqual(orig, restored)
                r.close()


if __name__ == '__main__':
    unittest.main()
