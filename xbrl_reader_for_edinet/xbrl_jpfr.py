"""xbrl_jpfr"""

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
        if self.info['報告書'] is None:
            # 再解析
            if 'E25850-' in self.file:
                self.info = self.parse_filename_e25850(os_basename(self.file))

        # XBRLファイル読み込み
        self.root = get_etree_obj_from_file(self.file, file_data)
        self.nsmap = self.root.nsmap
        self.ns_prefixes = {v: k for (k, v) in self.nsmap.items()}

        # 名前空間 文書情報タクソノミ
        self.ns_di = None

        # 名前空間 企業別タクソノミ
        self.ns_self = None

        # 名前空間 IFRS
        self.ns_ifrs = None

        # 名前空間 その他スキーマ
        self.ns_jpfr_oe = None

        # 名前空間 xbrldi
        self.ns_xbrldi = None

        # 勘定科目などを定義している名前空間を取得
        ns_list = []
        if self.info['会計基準'] == 'jpfr':
            # 名前空間(NameSpace)の定義を取得
            ns_def = xbrl_namespace.NS_INSTANCE_20130301

            for (ns_prefix, namespace) in self.nsmap.items():
                if ns_def['jpfr-di'](namespace):
                    ns_list.append((0, namespace))
                    self.ns_di = namespace
                elif re_match('^jpfr-t-[a-z]*$', ns_prefix):
                    ns_list.append((1, namespace))
                elif ns_def['self'](ns_prefix):
                    ns_list.append((2, namespace))
                    self.ns_self = namespace
                elif ns_def['jpfr-oe'](namespace):
                    self.ns_jpfr_oe = namespace

            ns_list.sort(key=lambda x: (x[0], x[1]), reverse=False)

        elif self.info['会計基準'] == 'ifrs':
            # 名前空間(NameSpace)の定義を取得
            ns_def = xbrl_namespace.NS_INSTANCE_IFRS_20130301

            for (ns_prefix, namespace) in self.nsmap.items():
                if ns_def['ifrs'](namespace):
                    ns_list.append((0, namespace))
                    self.ns_ifrs = namespace
                elif ns_def['self'](ns_prefix):
                    ns_list.append((1, namespace))
                    self.ns_self = namespace
                elif ns_def['xbrldi'] == namespace:
                    self.ns_xbrldi = namespace

            ns_list.sort(key=lambda x: (x[0], x[1]), reverse=False)

        else:
            print('会計基準の判定失敗')
            raise

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
        self.jpfr_oe_non_consolidated = '{%s}NonConsolidated' % self.ns_jpfr_oe if self.ns_jpfr_oe else None
        self.xbrldi_explicit_member = '{%s}explicitMember' % self.ns_xbrldi if self.ns_xbrldi else None
        self.xsi_nil = '{%s}nil' % ns_def['xsi']

        # xsdのファイルパスと名前空間を取得
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
        # 0         1         2         3         4
        # 01234567890123456789012345678901234567890123456789
        # jpfr-asr-E00000-000-2012-03-31-01-2012-06-22.xbrl
        od = OrderedDict()
        od.update({'会計基準': s[0:4]})

        try:
            # 第N期の数字を判定
            t = s[5:8]
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

            od.update({'EDINETコード_ファンドコード': s[9:15]})
            od.update({'追番': int(s[16:19])})
            od.update({'報告対象期間期末日': dateutil_parser_parse(s[20:30])})
            od.update({'提出回数': int(s[31:33])})
            od.update({'提出日': dateutil_parser_parse(s[34:44])})
        except ValueError:
            print('不正なファイル名\n%s' % format_exc())
            od.update({
                '報告書': None, '第N期': None, 'EDINETコード_ファンドコード': None,
                '追番': None, '報告対象期間期末日': None, '提出回数': None, '提出日': None,
                })
        return od

    @staticmethod
    def parse_filename_e25850(s):
        """ファイル名解析(E25850)"""
        #        0         1         2         3         4
        #        01234567890123456789012345678901234567890123456789
        #   通常 ifrs-asr-E00000-000-2012-03-31-01-2012-06-22.xbrl
        #        0         1         2         3         4         5
        #        012345678901234567890123456789012345678901234567890123
        # E25850 ifrs-asr-001_E00000-000_2014-12-31_01_2015-03-30.xbrl

        od = OrderedDict()
        od.update({'会計基準': s[0:4]})

        try:
            # 第N期の数字を判定
            t = s[5:8]
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
                od.update({'第N期': t})

            # s[9:12] <- 無視 (不正な文字列)

            od.update({'EDINETコード_ファンドコード': s[13:19]})
            od.update({'追番': s[20:23]})
            od.update({'報告対象期間期末日': dateutil_parser_parse(s[24:34])})
            od.update({'提出回数': s[35:37]})
            od.update({'提出日': dateutil_parser_parse(s[38:48])})
        except ValueError:
            print('不正なファイル名\n%s' % format_exc())
            od.update({
                '報告書': None, '第N期': None, 'EDINETコード_ファンドコード': None,
                '追番': None, '報告対象期間期末日': None, '提出回数': None, '提出日': None,
                })
        else:
            print('ファイル名 再解析 OK')
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

                if self.info['会計基準'] == 'jpfr':
                    # NonConsolidatedタグ取得
                    scenario.update(self.get_non_consolidated_tag(et_scenario))
                    od[key_id].update({'scenario': scenario})
                elif self.info['会計基準'] == 'ifrs':
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

    def get_non_consolidated_tag(self, element):
        """NonConsolidatedタグ取得"""
        od = OrderedDict()
        for (n, et_non_consolidated) in enumerate(element.findall('.//%s' % self.jpfr_oe_non_consolidated), start=1):
            # NonConsolidatedは通常1つ
            assert n == 1

            # <jpfr-oe:NonColsolidated/>
            # タグ名のみ取り出す
            od.update({'tag': et_non_consolidated.tag.rsplit('}', maxsplit=1)[1]})
        return od

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
