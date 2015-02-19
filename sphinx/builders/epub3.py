# -*- coding: utf-8 -*-
"""
    sphinx.builders.epub3
    ~~~~~~~~~~~~~~~~~~~~

    Build epub3 files.
    Originally derived from epub.py.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys
import codecs
import zipfile
from os import path

try:
    from PIL import Image
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None

from sphinx.builders.epub import EpubBuilder

# (Fragment) templates from which the metainfo files content.opf, nav.xhtml,
# toc.ncx, mimetype, and META-INF/container.xml are created.
# This template section also defines strings that are embedded in the html
# output but that may be customized by (re-)setting module attributes,
# e.g. from conf.py.

_navigation_doc_template_pre = u'''\
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="%(lang)s" xml:lang="%(lang)s">
  <head>
    <title>%(toc_locale)s</title>
  </head>
  <body>
    <nav epub:type="toc" id="toc">
      <h1>%(toc_locale)s</h1>
      <ol>
'''
_navigation_doc_template_post = u'''\
      </ol>
    </nav>
  </body>
</html>
'''

_navlist_single_entry = u'''\
%(indent)s  <li>
%(indent)s    <a href="%(refuri)s">%(text)s</a>
%(indent)s  </li>
'''

_navlist_entry_parent = u'''\
%(indent)s<li>
%(indent)s  <a href="%(refuri)s">%(text)s</a>
%(indent)s  <ol>
'''

_navlist_entry_leave = u'''\
%(indent)s  </ol>
%(indent)s</li>
'''

_navlist_indent = '    '


_package_doc_template = u'''\
<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" xml:lang="%(lang)s"
      unique-identifier="%(uid)s">
  <metadata xmlns:opf="http://www.idpf.org/2007/opf"
        xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:language>%(lang)s</dc:language>
    <dc:title>%(title)s</dc:title>
    <dc:creator>%(author)s</dc:creator>
    <dc:publisher>%(publisher)s</dc:publisher>
    <dc:rights>%(copyright)s</dc:rights>
    <dc:identifier id="%(uid)s">%(id)s</dc:identifier>
    <dc:date>%(date)s</dc:date>
    <meta property="dcterms:modified">%(datetimemodified)s</meta>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
%(files)s
  </manifest>
  <spine toc="ncx" page-progression-direction="%(page_progression_direction)s">
    <itemref idref="nav" />
%(spine)s
  </spine>
  <guide>
%(guide)s
  </guide>
</package>
'''


# The epub publisher

class Epub3Builder(EpubBuilder):
    """
    Builder that outputs epub3 files.

    It creates the metainfo files content.opf, nav.xhtml, toc.ncx, mimetype, and
    META-INF/container.xml.  Afterwards, all necessary files are zipped to an
    epub file.
    """
    name = 'epub3'

    _navigation_doc_template_pre = _navigation_doc_template_pre
    _navigation_doc_template_post = _navigation_doc_template_post
    #_navlist_template = _navlist_template
    _navlist_indent = _navlist_indent
    _content_template = _package_doc_template

    def init(self):
        super(Epub3Builder, self).init()

    # Finish by building the epub file
    def handle_finish(self):
        """Create the metainfo files and finally the epub."""
        self.get_toc()
        self.build_mimetype(self.outdir, 'mimetype')
        self.build_container(self.outdir, 'META-INF/container.xml')
        self.build_content(self.outdir, 'content.opf')
        self.build_navigation_doc_PGh(self.outdir, 'nav.xhtml')
        self.build_toc(self.outdir, 'toc.ncx')
        self.build_epub(self.outdir, self.config.epub_basename + '.epub')

    def build_navigation_doc_PGh(self,outdir,outname):
        prev_entry = None

        metadata = {}
        metadata['lang'] = self.esc(self.config.epub_language)
        metadata['toc_locale'] = self.esc(self._guide_titles['toc'])

        with open(os.path.join(outdir,outname),"w") as nav:
            nav.write(self._navigation_doc_template_pre % metadata)
            for n in self.refnodes:
                cur_entry = n.copy()
                cur_entry['indent'] = cur_entry['level'] * self._navlist_indent
                if prev_entry:
                    if cur_entry['level'] == prev_entry['level']:
                        nav.write(_navlist_single_entry % prev_entry)
                    elif cur_entry['level'] > prev_entry['level']:
                        nav.write(_navlist_entry_parent % prev_entry)
                    else:
                        nav.write(_navlist_single_entry % prev_entry)
                        while cur_entry['level'] < prev_entry['level']:
                            prev_entry['level'] = prev_entry['level'] - 1
                            prev_entry['indent'] = prev_entry['level'] * self._navlist_indent
                            nav.write(_navlist_entry_leave % prev_entry)
                prev_entry = cur_entry
            if prev_entry:
                nav.write(_navlist_single_entry % prev_entry)
                while 1 < prev_entry['level']:
                    prev_entry['level'] = prev_entry['level'] - 1
                    prev_entry['indent'] = prev_entry['level'] * self._navlist_indent
                    nav.write(_navlist_entry_leave % prev_entry)
            nav.write(self._navigation_doc_template_post % metadata)
        self.files.append(outname)

    def content_metadata(self, files, spine, guide):
        metadata = super(Epub3Builder, self).content_metadata(files, spine, guide)
        metadata['page_progression_direction'] = self.esc('ltr')
        return metadata
