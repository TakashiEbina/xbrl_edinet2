"""xbrl_proc"""

from os.path import basename as os_basename
import re
from traceback import format_exc
from pandas import DataFrame as pd_DataFrame
from pandas import to_datetime as pd_to_datetime

from xbrl_jpfr import Parser as xbrl_jpfr_Parser
from xbrl_jpcor import Parser as xbrl_jpcor_Parser
from xbrl_util import conv_str_to_num
from xbrl_zip import get_xbrl_files as xbrl_zip_get_xbrl_files

def read_xbrl(xbrl):
    """引数 XBRLファイルパス
戻り値 pandas.DataFrame"""
    # XBRLからデータ取得
    df = _get_xbrl_datas(xbrl, None)
    return df


RE_XBRL_FILE_MATCH = re.compile(r'^.*?(?:jpfr|ifrs|jpcrp).*?\.xbrl$').match
def read_xbrl_from_zip(xbrl):
    """引数 XBRLのzipファイルパス
戻り値 pandas.DataFrame のリスト"""
    # zipからファイルデータ取得
    file_datas = xbrl_zip_get_xbrl_files(
        xbrl,
        RE_XBRL_FILE_MATCH,
        )

    # XBRLファイル辞書取得
    xbrl_files = file_datas['xbrl']

    # XBRLからデータ取得
    # XBRLファイルは複数存在する場合があるのでリストを使用
    # (「jpfrとifrs」、「jpcrpとifrs」など)
    dfs = []
    for (xbrl_filename, xbrl_file_data) in xbrl_files.items():
        df = _get_xbrl_datas(xbrl_filename, xbrl_file_data)
        if df is not None:
            dfs.append(df)
    return dfs


# XBRLバージョン判定の正規表現
RE_XBRL_P_V1_MATCH = re.compile(r'^(?:jpfr|ifrs).*?\.xbrl$').match
RE_XBRL_P_V2_MATCH = re.compile(r'^jpcrp.*?\.xbrl$').match
def _get_xbrl_datas(xbrl_file, xbrl_file_data):
    """データ取得"""

    # xbrlファイル読み込み
    if RE_XBRL_P_V1_MATCH(os_basename(xbrl_file)):
        # 旧 EDINET XBRL
        # print(xbrl_file)
        xbrl = xbrl_jpfr_Parser(xbrl_file, xbrl_file_data)
        xbrl_ver = 1
    elif RE_XBRL_P_V2_MATCH(os_basename(xbrl_file)):
        # print(xbrl_file)
        xbrl = xbrl_jpcor_Parser(xbrl_file, xbrl_file_data)
        xbrl_ver = 2
    else:
        # 監査報告書のXBRLが該当(jpaud-***.xbrl)
        # print('未対応のファイル名 %s' % xbrl_file)
        return None

    # データをリストに変換
    data_labels = [
        'version', '提出日', '提出回数', '報告対象期間期末日', '追番', '第N期',
        '名前空間接頭辞', 'tag', 'id',
        'context', '開始日', '終了日', '期末日', '連結', '値',
        ]

    context_tags = xbrl.context_tags

    xbrl_infos = [
        xbrl_ver, xbrl.info['提出日'], xbrl.info['提出回数'],
        xbrl.info['報告対象期間期末日'], xbrl.info['追番'], xbrl.info['第N期'],
        ]

    datas = []
    datas_append = datas.append

    xbrl_standard = xbrl.info['会計基準'] if '会計基準' in xbrl.info else None

    # xbrl.xbrl_datasの種類(namespaceに対応する接頭辞)
    # 管理情報(jpfr-di, ifrs, jpdei_cor)
    # 表紙・サマリ・本文など(jpcrp_cor)
    # 財務諸表(jpfr-t-***, ifrs, jppfs_cor)
    # 提出者別タクソノミ(*E00000*)
    for (namespace, xbrl_data) in xbrl.xbrl_datas:

        # キーのタプル(タグ名・コンテキスト・ID)
        # 値の辞書(属性・テキスト)
        for ((t_tag, t_context_ref, t_id), v) in xbrl_data.items():

            # タグ名から名前空間を分離 & 接頭辞に変換
            (t_ns, t_tag_name) = t_tag.rsplit('}', maxsplit=1)
            try:
                datas_append(
                    # XBRLバージョンと文書情報
                    xbrl_infos +
                    
                    # 名前空間接頭辞 タグ名 id属性 コンテキスト
                    [
                        xbrl.ns_prefixes[t_ns.lstrip('{')],
                        t_tag_name,
                        t_id,
                        t_context_ref,
                    ] +

                    # 開始日 終了日 期末日
                    _get_dates(context_tags[t_context_ref]['period']) +

                    # 連結区分 型変換した値
                    [
                        _get_consolidated_or_nonconsolidated(context_tags[t_context_ref], xbrl_ver, xbrl_standard),
                        conv_str_to_num(v['text']),
                    ]
                )
            except:
                print(format_exc())
    del (xbrl, xbrl_infos, context_tags)

    # データフレームに変換
    df = pd_DataFrame(datas, columns=data_labels)
    del (datas, data_labels)

    def df_conv_str_to_datetime(t_colulmn_name):
        """文字列 -> 日付変換"""
        try:
            df[t_colulmn_name] = pd_to_datetime(df[t_colulmn_name])
        except (TypeError, ValueError):
            print('変換エラー %s conv_str_to_num で再試行' % t_colulmn_name)
            df[t_colulmn_name] = df[t_colulmn_name].apply(conv_str_to_num)
        return
    for colulmn_name in ('提出日', '開始日', '終了日', '期末日'):
        df_conv_str_to_datetime(colulmn_name)

    return df


def _get_dates(x):
    """日付取得"""
    if 'start_date' in x:
        return [x['start_date']['text'], x['end_date']['text'], None]
    else:
        return [None, None, x['instant']['text']]


CONSOLIDATED_OR_NONCONSOLIDATED_AXIS = 'jppfs_cor:ConsolidatedOrNonConsolidatedAxis'
NON_CONSOLIDATED_MEMBER = 'jppfs_cor:NonConsolidatedMember'
def _get_consolidated_or_nonconsolidated(x, xbrl_ver, xbrl_standard):
    """連結の真偽値を取得"""
    if xbrl_ver == 1:
        if xbrl_standard == 'jpfr':
            if 'scenario' in x:
                if x['scenario']['tag'] == 'NonConsolidated':
                    return False
                else:
                    print('想定外のscenario %s' % x['scenario']['tag'])
                    return True
            return True
        else:
            return None
    elif xbrl_ver == 2:
        if 'scenario' in x:
            if CONSOLIDATED_OR_NONCONSOLIDATED_AXIS in x['scenario']:
                if x['scenario'][CONSOLIDATED_OR_NONCONSOLIDATED_AXIS]['text'] == NON_CONSOLIDATED_MEMBER:
                    return False
            for dimension in x['scenario'].keys():
                if 'NonConsolidatedMember' in dimension:
                    print('想定外のscenario %s' % str(x['scenario']))
                    return False
        return True
    return None

