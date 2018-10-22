"""xbrl_zip"""

from os.path import basename as os_basename
from os.path import isfile as os_isfile
from zipfile import ZipFile
from collections import OrderedDict

def get_xbrl_files(file, re_xbrl_file_match):
    """XBRLファイルデータ取得"""
    xbrl_files = OrderedDict()

    if not os_isfile(file):
        print('not found %s' % file)
        return xbrl_files

    # zipオブジェクト作成
    with ZipFile(file, 'r') as zip_obj:
        # ファイルリスト取得
        infos = zip_obj.infolist()

        # zipアーカイブから対象ファイルを読み込む
        od_xbrl = OrderedDict()
        for info in infos:
            filename = os_basename(info.filename)

            # zipからデータを読み込んで辞書に入れる
            if re_xbrl_file_match(info.filename):
                od_xbrl.update({filename: zip_obj.read(info.filename)})

    xbrl_files.update({'xbrl': od_xbrl})
    return xbrl_files
