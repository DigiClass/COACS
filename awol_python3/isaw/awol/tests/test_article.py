#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test code in the article module."""

import logging
import os

from nose import with_setup
from nose.tools import *

from isaw.awol import article

PATH_TEST = os.path.dirname(os.path.abspath(__file__))
PATH_TEST_DATA = os.path.join(PATH_TEST, 'data')
PATH_TEST_TEMP = os.path.join(PATH_TEST, 'temp')

logging.basicConfig(level=logging.DEBUG)

def setup_function():
    """Test harness setup."""

    pass

def teardown_function():
    """Test harness teardown."""

    pass

@with_setup(setup_function, teardown_function)
def test_article_init():
    """Ensure class constructor can open and extract XML from file."""

    file_name = os.path.join(PATH_TEST_DATA, 'post-capitale-culturale.xml')
    a = article.Article(atom_file_name=file_name)
    assert_is_not_none(a.doc)
    assert_is_not_none(a.root)
    root = a.root
    assert_equals(root.tag, '{http://www.w3.org/2005/Atom}entry')
    assert_equals(a.id, 
        'tag:blogger.com,1999:blog-116259103207720939.post-107383690052898357')          
    assert_equals(a.title, u'Open Access Journal: Il capitale culturale')      
    assert_equals(a.url, 
        u'http://ancientworldonline.blogspot.com/2011/02/new-open-access-journal-il-capitale.html')   
    assert_equals(
        a.categories, 
        [
            {
                'term': 
                    'http://schemas.google.com/blogger/2008/kind#post',
                'vocabulary':
                    'http://schemas.google.com/g/2005#kind'
            }
        ])    
    assert_is_not_none(a.content)  
    assert_is_not_none(a.soup)     

