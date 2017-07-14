#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to walk AWOL backup and create json resource files.
"""

import _mypath
import argparse
import errno
import fileinput
from functools import wraps
import hashlib
import json
import logging
import os
import pprint
import re
import sys
import traceback

from isaw.awol import awol_article, resource
from isaw.awol.parse.awol_parsers import AwolParsers

RX_URLFLAT = re.compile(r'[=+\?\{\}\{\}\(\)\\\-_&%#/,\.;:]+')
RX_DEDUPEH = re.compile(r'[-]+')
DEFAULTLOGLEVEL = logging.WARNING

def arglogger(func):
    """
    decorator to log argument calls to functions
    """
    @wraps(func)
    def inner(*args, **kwargs):
        logger = logging.getLogger(func.__name__)
        logger.debug("called with arguments: %s, %s" % (args, kwargs))
        return func(*args, **kwargs)
    return inner


@arglogger
def main (args):
    """
    main functions
    """
    logger = logging.getLogger(sys._getframe().f_code.co_name)
    root_dir = args.whence[0]
    dest_dir = args.thence[0]
    walk_count = 0
    resources = None
    index = {}
    parsers = AwolParsers()
    for dir_name, sub_dir_list, file_list in os.walk(root_dir):
        if resources is not None:
            del resources
        for file_name in file_list:
            if 'post-' in file_name and file_name[-4:] == '.xml':
                walk_count = walk_count + 1
                if args.progress and walk_count % 50 == 1:
                    print('\n*****************************\nPERCENT COMPLETE: {0:.0f}\n'.format(float(walk_count)/4261.0*100.0))
                logger.info('\n=========================================================================================\nARTICLE:\n')
                target = os.path.join(dir_name, file_name)
                try:
                    a = awol_article.AwolArticle(atom_file_name=target)
                except (ValueError, RuntimeError) as e:
                    logger.warning(e)
                else:
                    logger.info(u'article title: {0}'.format(a.title))
                    logger.info(u'url: {0}'.format(a.url))
                    awol_id = '-'.join(('awol', a.id.split('.')[-1]))
                    logger.info('awol_id: {0}'.format(awol_id))
                    resources = None
                    try:
                        resources = parsers.parse(a)
                    except NotImplementedError as e:
                        logger.warning(e)
                    else:
                        try:
                            length = len(resources)
                        except TypeError:
                            length = 0
                        if length > 0:
                            for i,r in enumerate(resources):
                                logger.info(u'\n-----------------------------------------------------------------------------------------\nRESOURCE\n')
                                logger.info(u'url: {0}'.format(r.url))
                                logger.info(u'title: {0}'.format(r.title))
                                domain = r.domain
                                this_dir = os.path.join(dest_dir, domain)
                                try:
                                    os.makedirs(this_dir)
                                except OSError as exc:
                                    if exc.errno == errno.EEXIST and os.path.isdir(this_dir):
                                        pass
                                    else: raise
                                try:
                                    domain_index = index[domain]
                                except KeyError:
                                    domain_index = index[domain] = {}
                                stub = r.url.split(domain)[-1][1:].encode('utf-8')
                                if stub == '' or stub == '/':
                                    stub = domain.encode('utf-8').replace('.', '-')
                                if stub[-1] == '/':
                                    stub = stub[:-1]
                                if len(stub) > 80 or '?' in stub or '&' in stub or '%' in stub or ' ' in stub:
                                    m = hashlib.sha1()
                                    m.update(stub)
                                    resource_key = m.hexdigest()
                                else:
                                    resource_key = RX_DEDUPEH.sub('-', RX_URLFLAT.sub('-', stub))
                                filename = '.'.join((resource_key, 'json'))
                                this_path = os.path.join(this_dir, filename)
                                try:
                                    domain_resources = domain_index[resource_key]
                                except KeyError:
                                    pass
                                else:
                                    # collision! load earlier version from disk and merge
                                    logger.warning('collision in {0}: {1}/{2}'.format(a.url, r.domain, resource_key))
                                    r_earlier = resource.Resource()
                                    r_earlier.json_load(this_path)
                                    try:
                                        r_merged = resource.merge(r_earlier, r)
                                    except ValueError(e):
                                        logger.error(unicode(e) + u' while trying to merge; saving separately')
                                        m = hashlib.sha1()
                                        m.update(r.url)
                                        resource_key = m.hexdigest()
                                        filename = '.'.join((resource_key, 'json'))
                                        this_path = os.path.join(this_dir, filename)
                                    else:
                                        r = r_merged
                                    del r_earlier
                                r.resource_key = resource_key
                                r.json_dump(this_path, formatted=True)
                                logger.info(u'filename: {0}'.format(this_path))
                                try:
                                    resource_title = r.extended_title
                                except AttributeError:
                                    resource_title = r.title
                                resource_package = {
                                    'title_full': resource_title,
                                    'url': r.url,
                                    'key': resource_key,
                                }
                                if resource_title != r.title:
                                    resource_package['title'] = r.title
                                try:
                                    resource_list = domain_index[resource_key]
                                except KeyError:
                                    resource_list = domain_index[resource_key] = []
                                resource_list.append(resource_package)
            else:
                logger.debug('skipping {0}'.format(file_name))
        for ignore_dir in ['.git', '.svn', '.hg']:
            if ignore_dir in sub_dir_list:
                sub_dir_list.remove(ignore_dir)

    logger.info('sorting domain list')
    domain_list = sorted(index.keys())
    domain_count = len(domain_list)
    resource_count = 0
    record_count = 0
    max_collisions = 0
    total_collisions = 0
    redundant_resources = 0
    logger.info("FULL INDEX OF RESOURCES")
    logger.info("=======================")
    for domain in domain_list:
        logger.info(domain)
        i = 0
        dash = ''
        while i < len(domain):
            dash = dash+'-'
            i = i+1
        logger.info(dash)
        logger.info(u'sorting resource list for domain {0}'.format(domain))
        resource_list = sorted(index[domain].keys())
        logger.info('{0} unique resources in this domain'.format(len(resource_list)))
        resource_count = resource_count + len(resource_list)
        for resource_key in resource_list:
            resources = index[domain][resource_key]
            logger.info(u'    {0}'.format(resources[0]['title_full']))
            record_count = record_count + len(resources)
            if len(resources) > 1:
                logger.info ('        multiple records: {0}'.format(len(resources)))
                total_collisions = total_collisions + len(resources)
                redundant_resources = redundant_resources + 1
                if len(resources) > max_collisions:
                    max_collisions = len(resources)
    logger.info("=======================")
    logger.info("Total {0} domains".format(domain_count))
    logger.info("Total {0} unique resources recorded".format(resource_count))
    logger.info("Total number of records: {0}".format(record_count))
    logger.info("Highest number of redundancies (collisions): {0}".format(max_collisions))
    logger.info("Total number of redundant records: {0}".format(total_collisions))
    try:
    logger.info("Percentage of redundantly recorded resources:  {0:.2f}".format(round(float(redundant_resources)/float(resource_count)*100.0),2))
    except ZeroDivisionError:
        print("No records!")
if __name__ == "__main__":
    log_level = DEFAULTLOGLEVEL
    log_level_name = logging.getLevelName(log_level)
    logging.basicConfig(level=log_level)

    try:
        parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument ("-l", "--loglevel", type=str, help="desired logging level (case-insensitive string: DEBUG, INFO, WARNING, ERROR" )
        parser.add_argument ("-v", "--verbose", action="store_true", default=False, help="verbose output (logging level == INFO")
        parser.add_argument ("-vv", "--veryverbose", action="store_true", default=False, help="very verbose output (logging level == DEBUG")
        parser.add_argument ("--progress", action="store_true", default=False, help="show progress")
        #parser.add_argument('postfile', type=str, nargs='?', help='filename containing list of post files to process')
        parser.add_argument('whence', type=str, nargs=1, help='path to directory to read and process')
        parser.add_argument('thence', type=str, nargs=1, help='path to directory where you want the json-serialized resources dumped')
        args = parser.parse_args()
        if args.loglevel is not None:
            args_log_level = re.sub('\s+', '', args.loglevel.strip().upper())
            try:
                log_level = getattr(logging, args_log_level)
            except AttributeError:
                logging.error("command line option to set log_level failed because '%s' is not a valid level name; using %s" % (args_log_level, log_level_name))
        if args.veryverbose:
            log_level = logging.DEBUG
        elif args.verbose:
            log_level = logging.INFO
        log_level_name = logging.getLevelName(log_level)
        logging.getLogger().setLevel(log_level)
        if log_level != DEFAULTLOGLEVEL:
            logging.warning("logging level changed to %s via command line option" % log_level_name)
        else:
            logging.info("using default logging level: %s" % log_level_name)
        logging.debug("command line: '%s'" % ' '.join(sys.argv))
        main(args)
        sys.exit(0)
    except KeyboardInterrupt as e: # Ctrl-C
        raise e
    except SystemExit as e: # sys.exit()
        raise e
    except Exception as e:
        print("ERROR, UNEXPECTED EXCEPTION")
        print(str(e))
        traceback.print_exc()
        os._exit(1)
