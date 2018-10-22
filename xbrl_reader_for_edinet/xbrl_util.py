"""xbrl_util"""

import re
from traceback import format_exc
from dateutil.parser import parse as dateutil_parser_parse
from lxml.etree import XMLParser as etree_XMLParser
from lxml.etree import fromstring as etree_fromstring
from lxml.etree import XMLSyntaxError

def get_etree_obj_from_file(file, file_data=None):
    """XMLファイルを読み込む"""
    try:
        if file_data is None:
            with open(file, 'rb') as f:
                return etree_fromstring(f.read())
        else:
            return etree_fromstring(file_data)
    except XMLSyntaxError:
        print(format_exc())

    print('■ 不正なXML。recover=Trueで再解析。\n%s' % file)
    parser = etree_XMLParser(recover=True)
    if file_data is None:
        with open(file, 'rb') as f:
            root = etree_fromstring(f.read(), parser=parser)
    else:
        root = etree_fromstring(file_data, parser=parser)
    return root


RE_INT_MATCH = re.compile('^[+-]?[0-9]+[.]?$').match
RE_FLOAT_MATCH = re.compile(r'^[+-]?(?:[0-9]+\.[0-9]*|[0-9]*\.[0-9]+)$').match
def conv_str_to_num(s):
    """文字列を数値型等に変換"""
    # None
    if s is None:
        return s

    # 数値型
    a = s.replace(',', '')
    if RE_INT_MATCH(a):
        return int(a)
    elif RE_FLOAT_MATCH(a):
        return float(a)

    # bool型
    b = s.lower()
    if b == 'true':
        return True
    elif b == 'false':
        return False

    # 日付型
    try:
        t = dateutil_parser_parse(s)
    except ValueError:
        pass
    else:
        return t

    # その他
    return s
