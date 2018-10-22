# xbrl から読み込む
from xbrl_proc import read_xbrl

xbrl_file = r"C:\Users\taku\Documents\My Documents\蝦名事務所\EDINET 変換\0105010_honbun_jpcrp030000-asr-001_E02367-000_2018-03-31_01_2018-06-29_ixbrl"
df = read_xbrl(xbrl_file)
df.head(3)

