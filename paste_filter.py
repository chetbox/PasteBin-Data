#!/usr/bin/python

import re

def identify(content):
    if re.search('(' +
                    '(\.|/)\w*(tradebit|notlong|media|upload|share|file|porn|xxx|sex)\w*\.|' +
                    '(\.|/)(7z|torrent|cbz|iso|rar|mkv|mp[0-9]|zip)(\W|$)|' +
                    '\\b(xvid|dvdrip)\\b'
                ')', content, flags=re.IGNORECASE):
        return 'pirate'

    if re.search('footballcoverage', content, flags=re.IGNORECASE):
        return 'stream'

    if re.search('</?html[^>]*>', content, flags=re.IGNORECASE):
        return 'html'

    if re.search('^(CREATE|SELECT|DELETE|\\-{3}|\\+{3}|@@|\\-|\\+|Exception in thread)\\s', content, flags=re.IGNORECASE):
        return 'code'

    if re.search('^\\s*[EWIDV]/', content, flags=re.IGNORECASE):
        return 'code'

    if      re.search('(^\\s*(Dim|class|def|#include|#define)\\s)', content, flags=re.IGNORECASE) \
        or    re.search('[{\(]\\s*($|\n)', content, flags=re.IGNORECASE):

        if len(content) < 600:
            if max(map(len, content.split('\n'))) > 160:
                return 'wide'
            else:
                return 'short-code'
        else:
            return 'code'



def keep(identity):
    return (identity is None) or (identity == 'short-code')



import unittest

class PasteFilterTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_keep(self):
        self.assertTrue ( keep(None) )
        self.assertTrue ( keep('short-code') )
        self.assertFalse( keep('code') )
        self.assertFalse( keep('html') )
        self.assertFalse( keep('pirate') )

    def test_identify(self):
        test_cases = [
            (None, """Things http://www.google.com/sjbdsf drg sdb sgbsd"""),
            (None, """A torrent of things"""),
            (None, """I am talking about a class of function where I select a thing."""),
            ('pirate', """http://www.mediafire.com"""),
            ('pirate', """http://www.megaupload.com"""),
            ('pirate', """http://something.torrent"""),
            ('pirate', """http://things.iso"""),
            ('pirate', """get http://things.rar"""),
            ('pirate', """http://rapidshare.com"""),
            ('pirate', """http://2shared.com"""),
            ('pirate', """http://filepost.com"""),
            ('pirate', """http://wupload.com"""),
            ('pirate', """http://deppositfiles.com"""),
            ('pirate', """http://4shared.com"""),
            ('pirate', """something something Xvid something"""),
            ('pirate', """http://filepost.com"""),
            ('pirate', """File name:     Xxx DVD5 The Essential Lovers Guide.part1.rar\n"""),
            ('pirate', """http://www.filesonic.com/file/1560757611/Hoodwinked.Too.Hood.VS.Evil.2011.DVDRip.Xvid-MAX.part1.rar"""),
            ('html', '<html>' + 'lots of things. ' * 30 + '</html>'),
            ('html', '<!DOCTYPE HTML PUBLIC>\n<html>' + 'lots of things. ' * 30 + '</html>'),
            ('html', """<!doctype html>
<html>
<head>
    <title>Artbox7</title>
    <link rel="stylesheet" href="css/normalize.css">"""),
            ('code', '.thing { \n' +
                '   color: #fff;\n' * 100 + 
                '}\n'),
            ('short-code', '.thing { \n' +
                '   color: #fff;\n' * 2 + 
                '}\n'),
            ('short-code', 'class Thing(): \n' +
                ( ' def __init__(self):\n' + 
                  '      pass\n\n') * 2),
            ('code', 'class Thing(): \n' +
                ( ' def __init__(self):\n' + 
                  '      pass\n\n') * 100),
            ('code', ('  def t():\n' +
                '    pass\n\n') * 50),
            ('code', """SELECT * FROM 'blah'"""),
            ('code', """DELETE * FROM 'blah'"""),
            ('code', '#include\n' * 100),
            ('short-code', '#include\n' * 3),
            ('code', '#define\n' * 100),
            ('code', 'D/debug log\n' * 100),
            ('short-code', '#define\n' * 3),
            ('short-code', '    public void  dfgfg() { '),
            ('wide', 'void thing() {\n' + 'too long ' * 40),
            (None, 'good length ' * 4),
            ('stream', 'http://footballcoverage-2012.blogspot.com'),
        ]
        for (expected, doc) in test_cases:
            try:
                self.assertEquals(expected, identify(doc))
            except AssertionError as e:
                print((expected, doc))
                raise e


if __name__ == '__main__':
    unittest.main()

