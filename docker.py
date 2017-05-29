#!/usr/bin/env python

'''
docker.py: Script to delete docker image tag from Docker Hub

Copyright (c) 2017, AppsCode Inc. All rights reserved.
Copyright (c) 2016, Vanessa Sochat. All rights reserved.

"Singularity" Copyright (c) 2016, The Regents of the University of California,
through Lawrence Berkeley National Laboratory (subject to receipt of any
required approvals from the U.S. Dept. of Energy).  All rights reserved.
 
This software is licensed under a customized 3-clause BSD license.  Please
consult LICENSE file distributed with the sources of this project regarding
your rights to use or distribute this software.
 
NOTICE.  This Software was developed under funding from the U.S. Department of
Energy and the U.S. Government consequently retains certain rights. As such,
the U.S. Government has been granted for itself and others acting on its
behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
to reproduce, distribute copies to the public, prepare derivative works, and
perform publicly and display publicly, and to permit other to do so. 

'''

# Needed for antipackage with python 2
from __future__ import absolute_import

import base64
import json
import re
import sys
from os.path import expanduser

try:
    from urllib.parse import urlencode, urlparse
    from urllib.request import urlopen, Request, unquote
    from urllib.error import HTTPError
except ImportError:
    from urllib import urlencode, unquote
    from urlparse import urlparse
    from urllib2 import urlopen, Request, HTTPError
    from urllib2 import build_opener, HTTPHandler

api_base = "https://index.docker.io"
api_version = "v2"


# Authentication not required ---------------------------------------------------------------------------------

def parse_headers(default_header, headers=None):
    '''parse_headers will return a completed header object, adding additional headers to some
    default header
    :param default_header: include default_header (above)
    :param headers: headers to add (default is None)
    '''

    # default header for all calls
    header = {'Accept': 'application/json', 'Content-Type': 'application/json; charset=utf-8'}

    if default_header == True:
        if headers != None:
            final_headers = header.copy()
            final_headers.update(headers)
        else:
            final_headers = header

    else:
        final_headers = headers
        if headers == None:
            final_headers = dict()

    return final_headers


def api_get(url, data=None, default_header=True, headers=None):
    '''api_get gets a url to the api with appropriate headers, and any optional data
    :param data: a dictionary of key:value items to add to the data args variable
    :param path: the url to get
    :returns response: the requests response object
    '''
    headers = parse_headers(default_header=default_header,
                            headers=headers)
    print url
    if data:
        args = urlencode(data)
        request = Request(url=url,
                          data=args,
                          headers=headers)
    else:
        request = Request(url=url,
                          headers=headers)
    try:
        return urlopen(request)
    # If we have an HTTPError, try to follow the response
    except HTTPError as response:
        if response.code != 401 or "WWW-Authenticate" not in response.headers:
            print("Authentication error for registry, exiting.")
            sys.exit(1)

        challenge = response.headers["WWW-Authenticate"]
        if not challenge.startswith('Bearer '):
            print("Unrecognized authentication challenge from registry, exiting.")
            sys.exit(1)
        challenge = challenge[len('Bearer '):]
        print challenge
        d = {}
        for x in challenge.split(','):
            k, v = x.split('=')
            d[k] = v.strip('"')

        realm = d['realm']
        del d['realm']
        base = "%s?%s" % (realm, urlencode(d))
        print base

        # challenge = response.headers["WWW-Authenticate"]
        # match = re.match('^Bearer\s+realm="([^"]+)",service="([^"]+)",scope="([^"]+)"\s*$', challenge)
        # if not match:
        #     print("Unrecognized authentication challenge from registry, exiting.")
        #     sys.exit(1)
        #
        # realm = match.group(1)
        # service = match.group(2)
        # scope = match.group(3)
        #
        # base = "%s?service=%s&scope=%s" % (realm, service, scope)
        tokenHeaders = dict()
        if "Authorization" in headers:
            tokenHeaders["Authorization"] = headers["Authorization"]

        response = api_get(base, default_header=False, headers=tokenHeaders)
        try:
            response = response.read().decode('utf-8')
            token = json.loads(response)["token"]
            token = {"Authorization": "Bearer %s" % token}
            print token
            return api_get(url, default_header=default_header, headers=token)
        except:
            print("Error getting token for repository, exiting.")
            sys.exit(1)


def api_delete(url, data=None, default_header=True, headers=None):
    '''api_delete gets a url to the api with appropriate headers, and any optional data
    :param data: a dictionary of key:value items to add to the data args variable
    :param path: the url to get
    :returns response: the requests response object
    '''
    headers = parse_headers(default_header=default_header,
                            headers=headers)
    print url
    if data:
        args = urlencode(data)
        request = Request(url=url,
                          data=args,
                          headers=headers)
    else:
        request = Request(url=url,
                          headers=headers)
    request.get_method = lambda: 'DELETE'
    try:
        opener = build_opener(HTTPHandler)
        return opener.open(request)
    # If we have an HTTPError, try to follow the response
    except HTTPError as response:
        if response.code != 401 or "WWW-Authenticate" not in response.headers:
            print("Authentication error for registry, exiting.")
            sys.exit(1)

        challenge = response.headers["WWW-Authenticate"]
        if not challenge.startswith('Bearer '):
            print("Unrecognized authentication challenge from registry, exiting.")
            sys.exit(1)
        challenge = challenge[len('Bearer '):]
        print challenge
        d = {}
        for x in challenge.split(','):
            k, v = x.split('=')
            d[k] = v.strip('"')
        print d, urlencode(d)

        realm = d['realm']
        del d['realm']
        base = "%s?%s" % (realm, urlencode(d))
        tokenHeaders = dict()
        if "Authorization" in headers:
            tokenHeaders["Authorization"] = headers["Authorization"]

        response = api_get(base, default_header=False, headers=tokenHeaders)
        try:
            response = response.read().decode('utf-8')
            token = json.loads(response)["token"]
            token = {"Authorization": "Bearer %s" % token}
            print token
            return api_delete(url, default_header=default_header, headers=token)
        except:
            print("Error getting token for repository, exiting.")
            sys.exit(1)


def basic_auth_header(username, password):
    '''basic_auth_header will return a base64 encoded header object to
    generate a token
    :param username: the username
    :param password: the password
    '''
    s = "%s:%s" % (username, password)
    if sys.version_info[0] >= 3:
        s = bytes(s, 'utf-8')
        credentials = base64.b64encode(s).decode('utf-8')
    else:
        credentials = base64.b64encode(s)
    auth = {"Authorization": "Basic %s" % credentials}
    return auth


# Authentication required ---------------------------------------------------------------------------------
# Docker Registry Version 2.0 Functions - IN USE

def version_info(registry=None, headers=None):
    '''get_tags will return the tags for a repo using the Docker Version 2.0 Registry API
    :param namespace: the namespace (eg, "library")
    :param repo_name: the name for the repo (eg, "ubuntu")
    :param registry: the docker registry to use (default will use index.docker.io)
    :param headers: dictionary of custom headers to add to token header (to get more specific manifest)
    '''
    if registry is None:
        registry = api_base

    base = "%s/%s/" % (registry, api_version)
    print("Obtaining registry v2 info: %s" % base)

    response = api_get(base, default_header=False, headers=headers)
    try:
        body = response.read().decode('utf-8')
        body = json.loads(body)
        return body, response.headers
    except:
        print("Error obtaining tags: %s" % base)
        sys.exit(1)


def get_tags(namespace, repo_name, registry=None, headers=None):
    '''get_tags will return the tags for a repo using the Docker Version 2.0 Registry API
    :param namespace: the namespace (eg, "library")
    :param repo_name: the name for the repo (eg, "ubuntu")
    :param registry: the docker registry to use (default will use index.docker.io)
    :param headers: dictionary of custom headers to add to token header (to get more specific manifest)
    '''
    if registry is None:
        registry = api_base

    base = "%s/%s/%s/%s/tags/list" % (registry, api_version, namespace, repo_name)
    print("Obtaining tags: %s" % base)

    response = api_get(base, default_header=False, headers=headers)
    try:
        body = response.read().decode('utf-8')
        body = json.loads(body)
        return body['tags'], response.headers
    except:
        print("Error obtaining tags: %s" % base)
        sys.exit(1)


def get_manifest(namespace, repo_name, repo_tag="latest", registry=None, headers=None):
    '''get_manifest should return an image manifest for a particular repo and tag. The token is expected to
    be from version 2.0 (function above)
    :param namespace: the namespace for the image, default is "library"
    :param repo_name: the name of the repo, eg "ubuntu"
    :param repo_tag: the repo tag, default is "latest"
    :param registry: the docker registry to use (default will use index.docker.io)
    :param headers: dictionary of custom headers to add to token header (to get more specific manifest)
    '''
    if registry == None:
        registry = api_base

    base = "%s/%s/%s/%s/manifests/%s" % (registry, api_version, namespace, repo_name, repo_tag)
    print("Obtaining manifest: %s" % base)

    print headers

    response = api_get(base, headers=headers, default_header=False)
    try:
        print response.headers
        body = response.read().decode('utf-8')
        body = json.loads(body)
        return body, response.headers
    except:
        # If the call fails, give the user a list of acceptable tags
        tags, _ = get_tags(namespace=namespace,
                           repo_name=repo_name,
                           registry=registry,
                           headers=headers)
        print("\n".join(tags))
        print("Error getting manifest for %s/%s:%s, exiting." % (namespace, repo_name, repo_tag))
        print(
            "Error getting manifest for %s/%s:%s. Acceptable tags are listed above." % (namespace, repo_name, repo_tag))
        sys.exit(1)


def delete_manifest(namespace, repo_name, digest, registry=None, headers=None):
    '''delete_manifest deletes an image manifest for a particular repo and tag. The token is expected to
    be from version 2.0 (function above)
    :param namespace: the namespace for the image, default is "library"
    :param repo_name: the name of the repo, eg "ubuntu"
    :param digest: the content digest of a tag
    :param registry: the docker registry to use (default will use index.docker.io)
    :param headers: dictionary of custom headers to add to token header (to get more specific manifest)
    '''
    if registry == None:
        registry = api_base

    base = "%s/%s/%s/%s/manifests/%s" % (registry, api_version, namespace, repo_name, digest)
    print("Deleting manifest: %s" % base)

    response = api_delete(base, headers=headers, default_header=True)
    try:
        print response.headers
        body = response.read().decode('utf-8')
        body = json.loads(body)
        return body, response.headers
    except:
        print("Error deleting manifest for %s/%s with digest %s, exiting." % (namespace, repo_name, digest))
        sys.exit(1)


# TODO: use unicode encoding
def read_json(name):
    try:
        with open(name, 'r') as f:
            return json.load(f)
    except IOError as err:
        print(err)
        sys.exit(1)


if __name__ == "__main__":
    m1, h1 = version_info()
    print h1.headers

    home = expanduser("~")
    config = read_json(home + "/.docker/config.json")
    print config['auths']['https://index.docker.io/v1/']['auth']
    # sys.exit(1)


    # print get_tags('appscode', 'voyager')
    # print '\n\n\n\n\n'
    m2, h2 = get_manifest('appscode', 'voyager', "1.5.5-5-g76c5a25", headers={
        'Accept': 'application/vnd.docker.distribution.manifest.v2+json',
    })

    print json.dumps(m2, sort_keys=True, indent=2, separators=(',', ': ')), h2['Docker-Content-Digest']
    _, h3 = delete_manifest('appscode', 'voyager', h2['Docker-Content-Digest'], headers={
        'Authorization': 'Basic ' + config['auths']['https://index.docker.io/v1/']['auth'],
    })
    print h3
