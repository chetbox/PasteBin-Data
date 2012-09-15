#!/usr/bin/python

import re

def identify(content):
	if re.search('(' +
					'(\.|/)\w*(notlong|media|upload|share|file|porn|xxx|sex)\w*\.|' +
					'(\.|/)(7z|torrent|iso|rar|mkv|mp[0-9]|zip)(\W|$)|' +
					'\\b(xvid|dvdrip)\\b'
				')', content, flags=re.IGNORECASE):
		return 'pirate'

	if re.search('</?html[^>]*>', content, flags=re.IGNORECASE):
		return 'html'

def keep(content):
	return identify(content) is None



import unittest

class PasteFilterTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_identify(self):
    	test_cases = [
    		(None, """Things http://www.google.com/sjbdsf drg sdb sgbsd"""),
    		(None, """A torrent of things"""),
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
    		('pirate', """http://www.filesonic.com/file/1560757611/Hoodwinked.Too.Hood.VS.Evil.2011.DVDRip.Xvid-MAX.part1.rar"""),
    		('html', '<html>' + 'lots of things. ' * 30 + '</html>'),
    		('html', '<!DOCTYPE HTML PUBLIC>\n<html>' + 'lots of things. ' * 30 + '</html>'),
    	]
    	for (expected, doc) in test_cases:
    		try:
	    		self.assertEquals(expected, identify(doc))
	    	except AssertionError as e:
	    		print((expected, doc))
	    		raise e


if __name__ == '__main__':
	unittest.main()

