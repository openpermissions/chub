# -*- coding: utf-8 -*-
# Copyright 2016 Open Permissions Platform Coalition
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and limitations under the License.
# 

import sys
import os
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('..'))
import subprocess
subprocess.Popen(["make", "sphinx"], cwd=os.path.abspath('..')).communicate()

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
]

templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'

project = u'chub'
copyright = u'2016, Open Permissions Platform Coalition'

version = '0.4.0'
release = '0.4.0'

exclude_patterns = ['_build']

pygments_style = 'sphinx'

html_theme = 'default'

html_static_path = ['_static']

htmlhelp_basename = 'chubdoc'

latex_elements = {

}

latex_documents = [
  ('index', 'chub.tex', u'chub Documentation',
   u'Open Permissions Platform Coalition', 'manual'),
]

man_pages = [
    ('index', 'chub', u'chub Documentation',
     [u'Open Permissions Platform Coalition'], 1)
]

texinfo_documents = [
  ('index', 'chub', u'chub Documentation',
   u'Open Permissions Platform Coalition', 'chub', 'One line description of project.',
   'Miscellaneous'),
]

epub_title = u'chub'
epub_author = u'Open Permissions Platform Coalition'
epub_publisher = u'Open Permissions Platform Coalition'
epub_copyright = u'2016, Open Permissions Platform Coalition'

epub_exclude_files = ['search.html']

