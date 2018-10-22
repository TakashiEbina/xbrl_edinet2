"""xbrl_namespace"""

import re

# 名前空間
NS_INSTANCE_20130301 = {
    'xbrli': 'http://www.xbrl.org/2003/instance',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xlink': 'http://www.w3.org/1999/xlink',
    'link': 'http://www.xbrl.org/2003/linkbase',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'self': re.compile('^jp[a-z]*-[a-z0-9]{3}-[A-Z][0-9]{5}-[0-9]{3}$').match,
    'jpfr-di': re.compile('^http://info.edinet-fsa.go.jp/jp/fr/gaap/o/di/[1-9][0-9]{3}-[01][0-9]-[0-3][0-9]$').match,
    'jpfr-oe': re.compile('^http://info.edinet-fsa.go.jp/jp/fr/gaap/o/oe/[1-9][0-9]{3}-[01][0-9]-[0-3][0-9]$').match,
    }

NS_INSTANCE_IFRS_20130301 = {
    'xbrli': 'http://www.xbrl.org/2003/instance',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xlink': 'http://www.w3.org/1999/xlink',
    'link': 'http://www.xbrl.org/2003/linkbase',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'self': re.compile('^ifrs-[a-z0-9]{3}[-_][A-Z][0-9]{5}-[0-9]{3}$').match,
    'xbrldt': 'http://www.xbrl.org/2005/xbrldt',
    'ifrs': re.compile('^http://xbrl.ifrs.org/taxonomy/[1-9][0-9]{3}-[01][0-9]-[0-3][0-9]/ifrs$').match,
    'xbrldi': 'http://xbrl.org/2006/xbrldi',
}

NS_INSTANCE_20180228 = {
    'ix': 'http://www.xbrl.org/2008/inlineXBRL',
    'ixt': 'http://www.xbrl.org/inlieXBRL/transformation/2011-07-31',
    'xbrli': 'http://www.xbrl.org/2003/instance',
    'xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xlink': 'http://www.w3.org/1999/xlink',
    'link': 'http://www.xbrl.org/2003/linkbase',
    'iso4217': 'http://www.xbrl.org/2003/iso4217',
    'self': re.compile('^jp[a-z]{3}[0-9]{6}-[a-z0-9]{3}_[A-Z][0-9]{5}-[0-9]{3}$').match,
    'jpdei_cor': re.compile('^http://disclosure.edinet-fsa.go.jp/taxonomy/jpdei/[1-9][0-9]{3}-[01][0-9]-[0-3][0-9]/jpdei_cor$').match,
    'jpcrp_cor': re.compile('^http://disclosure.edinet-fsa.go.jp/taxonomy/jpcrp/[1-9][0-9]{3}-[01][0-9]-[0-3][0-9]/jpcrp_cor$').match,
    'jppfs_cor': re.compile('^http://disclosure.edinet-fsa.go.jp/taxonomy/jppfs/[1-9][0-9]{3}-[01][0-9]-[0-3][0-9]/jppfs_cor$').match,
    'num': 'http://www.xbrl.org/dtr/type/numericXBRL',
    'nonnum': 'http://www.xbrl.org/dtr/type/non-numericXBRL',
    'xbrldt': 'http://xbrl.org/2005/xbrldt',
    'xbrldi': 'http://xbrl.org/2006/xbrldi',
    }
