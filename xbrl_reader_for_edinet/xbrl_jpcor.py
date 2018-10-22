"""xbrl_jpcor"""

from os.path import join as os_join
from os.path import basename as os_basename
from os.path import dirname as os_dirname
from re import match as re_match
from collections import OrderedDict
from traceback import format_exc
from dateutil.parser import parse as dateutil_parser_parse
import xbrl_namespace
from xbrl_util import get_etree_obj_from_file

class Parser:
    """xbrlファイル解析クラス"""
    def __init__(self, file, file_data):
        self.file = file

        # ファイル名解析
        self.info = self.parse_filename(os_basename(self.file))

        # XBRLファイル読み込み
        self.root = get_etree_obj_from_file(self.file, file_data)
        self.nsmap = self.root.nsmap
        self.ns_prefixes = {v: k for (k, v) in self.nsmap.items()}

        # 名前空間(NameSpace)の定義を取得
        ns_def = xbrl_namespace.NS_INSTANCE_20180228

        # 名前空間 DEI語彙スキーマ (管理情報)
        self.ns_dei = None

        # 名前空間 企業内容等の開示に関する内閣府令 (表紙・サマリ・本文など)
        self.ns_crp = None

        # 名前空間 日本基準財務諸表のうち本表に係る部分 (財務諸表)
        self.ns_pfs = None

        # 名前空間 提出者別タクソノミ
        self.ns_self = None

        # 勘定科目などを定義している名前空間を取得
        ns_list = []
        for (ns_prefix, ns) in self.nsmap.items():
            if ns_def['jpdei_cor'](ns):
                ns_list.append((0, ns))
                self.ns_dei = ns
            elif ns_def['jpcrp_cor'](ns):
                ns_list.append((1, ns))
                self.ns_crp = ns
            elif ns_def['jppfs_cor'](ns):
                ns_list.append((2, ns))
                self.ns_pfs = ns
            elif ns_def['self'](ns_prefix):
                ns_list.append((3, ns))
                self.ns_self = ns

        # 管理情報(dei)が上に来るとデバッグし易かったのでソート
        ns_list.sort(key=lambda x: x[0], reverse=False)

        # タグ名/属性名定義
        self.link_schema_ref = '{%s}schemaRef' % ns_def['link']
        self.xlink_href = '{%s}href' % ns_def['xlink']
        self.xbrli_context = '{%s}context' % ns_def['xbrli']
        self.xbrli_entity = '{%s}entity' % ns_def['xbrli']
        self.xbrli_identifier = '{%s}identifier' % ns_def['xbrli']
        self.xbrli_period = '{%s}period' % ns_def['xbrli']
        self.xbrli_start_date = '{%s}startDate' % ns_def['xbrli']
        self.xbrli_end_date = '{%s}endDate' % ns_def['xbrli']
        self.xbrli_instant = '{%s}instant' % ns_def['xbrli']
        self.xbrli_scenario = '{%s}scenario' % ns_def['xbrli']
        self.xbrldi_explicit_member = '{%s}explicitMember' % ns_def['xbrldi']
        self.xsi_nil = '{%s}nil' % ns_def['xsi']

        # xsdファイルパス取得
        self.xsd = self.get_xsd_filepath(file_data)

        # コンテキストタグ(日付情報)取得
        self.context_tags = self.get_context_tags()

        # 管理情報・財務諸表データ取得
        self.xbrl_datas = []
        for (number, ns) in ns_list:
            self.xbrl_datas.append((ns, self.get_xbrl_datas(ns)))

        # 変数削除
        del self.root
        return

    @staticmethod
    def parse_filename(s):
        """ファイル名解析"""
        # 0         1         2         3         4         5         6
        # 0123456789012345678901234567890123456789012345678901234567890
        # jpcrp030000-asr-001_E00000-000_2017-03-31_01_2017-06-29.xbrl
        od = OrderedDict()

        try:
            od.update({'府令略号': s[2:5]})
            od.update({'様式番号': s[5:11]})

            # 第N期の数字を判定
            t = s[12:15]
            od.update({'報告書': t})

            if t == 'asr':
                # 有価証券報告書
                od.update({'第N期': 0})
            elif re_match('^q[1-5]r$', t):
                # 四半期報告書
                od.update({'第N期': int(t[1])})
            elif t == 'ssr':
                # 半期報告書
                od.update({'第N期': 2})
            else:
                # 有価証券届出書
                # みなし有価証券届出書
                od.update({'第N期': None})

            od.update({'報告書連番': s[16:19]})
            od.update({'EDINETコード_ファンドコード':s[20:26]})
            od.update({'追番': int(s[27:30])})
            od.update({'報告対象期間期末日': dateutil_parser_parse(s[31:41])})
            od.update({'提出回数': int(s[42:44])})
            od.update({'提出日': dateutil_parser_parse(s[45:55])})

        except ValueError:
            print('不正なファイル名\n%s' % format_exc())
            od.update({
                '府令略号': None, '様式番号': None, '報告書': None,
                '第N期': None, '報告書連番': None, 'EDINETコード_ファンドコード': None,
                '追番': None, '報告対象期間期末日': None, '提出回数': None, '提出日': None,
                })
        return od

    def get_xsd_filepath(self, file_data):
        """提出者別タクソノミのxsdファイルパス取得"""
        # xsdファイル名取得
        element = self.root.find('.//%s' % self.link_schema_ref)

        if file_data is None:
            # 絶対パス生成
            return os_join(os_dirname(self.file), element.get(self.xlink_href))
        else:
            return os_basename(element.get(self.xlink_href))

    def get_context_tags(self):
        """contextタグ取得"""
        od = OrderedDict()

        # contextタグ取得
        for element in self.root.findall('.//%s' % self.xbrli_context):
            # id属性の値を取得
            key_id = element.get('id')

            # idは重複しないはず
            assert key_id not in od

            # id属性をキーにして辞書を作成
            od.update({key_id: OrderedDict()})

            # entityタグ取得
            entity = OrderedDict()
            for (n, et_entity) in enumerate(element.findall('.//%s' % self.xbrli_entity), start=1):
                # entityは通常1つ
                assert n == 1

                # identifierタグ取得
                entity.update(self.get_identifier_tags(et_entity))
                od[key_id].update({'entity': entity})

            # periodタグ取得
            period = OrderedDict()
            for (n, et_period) in enumerate(element.findall('.//%s' % self.xbrli_period), start=1):
                # periodは通常1つ
                assert n == 1

                # startDate, endDate, instantタグ取得
                period.update(self.get_date_tags(et_period))
                od[key_id].update({'period': period})

            # scenarioタグ取得
            scenario = OrderedDict()
            for (n, et_scenario) in enumerate(element.findall('.//%s' % self.xbrli_scenario), start=1):
                # scenarioは通常1つ
                assert n == 1

                # explicitMemberタグ取得
                scenario.update(self.get_explicit_member_tags(et_scenario))
                od[key_id].update({'scenario': scenario})
        return od

    def get_identifier_tags(self, element):
        """identifierタグ取得"""
        od = OrderedDict()
        for (n, et_identifier) in enumerate(element.findall('.//%s' % self.xbrli_identifier), start=1):
            # identifierは通常1つ
            assert n == 1

            for (name, value) in et_identifier.items():
                od.update({name: value})
            od.update({'text': et_identifier.text})
        return od

    def get_date_tags(self, element):
        """日付タグ取得"""
        datas = OrderedDict()

        et_start_date = element.find('.//%s' % self.xbrli_start_date)
        if et_start_date is not None:
            # 開始日を追加
            od = OrderedDict()
            for (name, value) in et_start_date.items():
                od.update({name: value})
            od.update({'text': et_start_date.text})
            datas.update({'start_date': od})

            # 終了日を追加
            et_end_date = element.find('.//%s' % self.xbrli_end_date)

            od = OrderedDict()
            for (name, value) in et_end_date.items():
                od.update({name: value})
            od.update({'text': et_end_date.text})
            datas.update({'end_date': od})
        else:
            # 期末日を追加
            et_instant = element.find('.//%s' % self.xbrli_instant)

            od = OrderedDict()
            for (name, value) in et_instant.items():
                od.update({name: value})
            od.update({'text': et_instant.text})
            datas.update({'instant': od})
        return datas

    def get_explicit_member_tags(self, element):
        """explicitMemberタグ取得"""
        od = OrderedDict()
        for et_explicit_member in element.findall('.//%s' % self.xbrldi_explicit_member):
            key = et_explicit_member.get('dimension')

            assert key not in od

            od.update({key: et_explicit_member.attrib})
            od[key].update({'text': et_explicit_member.text})
        return od

    def get_xbrl_datas(self, namespace):
        """データ取得"""
        datas = OrderedDict()
        for element in self.root.findall('.//{%s}*' % namespace):
            # # 本文のテキストブロックは不要なのでスキップ
            # if self.ns_crp:
            #     if self.ns_crp in element.tag:
            #         if 'CoverPage' in element.tag:
            #             # print('skipped %s %s' % (element.tag.split('}')[1], element.text[:20]))
            #             continue
            #         elif 'TextBlock' in element.tag:
            #             # print('skipped %s %s' % (element.tag.split('}')[1], element.text[:20]))
            #             continue

            # # 提出者別タクソノミのテキストブロックは不要なのでスキップ
            # if self.ns_self:
            #     if self.ns_self in element.tag:
            #         if 'CoverPage' in element.tag:
            #             # print('skipped %s %s' % (element.tag.split('}')[1], element.text[:20]))
            #             continue
            #         elif 'TextBlock' in element.tag:
            #             # print('skipped %s %s' % (element.tag.split('}')[1], element.text[:20]))
            #             continue

            # tag名、contextRef、idのタプルをキーにして辞書を作成
            key = (element.tag, element.get('contextRef'), element.get('id'))
            data = OrderedDict()

            # 属性の内容を追加
            data.update(element.attrib)

            # テキストも追加
            data.update({'text': element.text})

            if key in datas:
                if data == datas[key]:
                    # キーも値も同じなのでスキップ
                    continue
                else:
                    print('キー重複 %s' % str(key))

            # リストに追加
            datas.update({key: data})
        return datas
