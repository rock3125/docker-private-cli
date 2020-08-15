#!/usr/bin/python3

import getopt
import sys
import base64
import requests

_SERVER = ""
_AUTH_TOKEN = ""
_CATALOG = "_catalog"
_MANIFEST = "/manifests/"
_TAGS = "/tags/list"
_DOCKER_CONT_HDR = "docker-content-digest"
_FS_LAYERS = "fsLayers"
_BLOB_SUM = "blobSum"
exclude_list = list()


def usage():
    print('')
    print('Usage: ' + sys.argv[0] + ' [-s server] [-u username] [-p password] [-v verbose] [-d delete] [-e EXCLUDE]')
    print('  -s   --server            Docker registry URL')
    print('  -u   --username          docker registry user-name')
    print('  -p   --password          docker registry user\'s password')
    print('  -d   --delete            a specific image name:tag format')
    print('')
    print('example: ' + sys.argv[0] + ' -s 129.157.181.199:5000 -u admin -p p@ssword -d name:1.0.0')


def make_request(url, method):
    global _AUTH_TOKEN

    try:
        if method == "DELETE":
            if len(_AUTH_TOKEN) > 0:
                return requests.delete(url, headers={"Authorization": "Basic %s" % _AUTH_TOKEN})
            else:
                return requests.delete(url)
        else:
            if len(_AUTH_TOKEN) > 0:
                return requests.get(url, headers={"Authorization": "Basic %s" % _AUTH_TOKEN})
            else:
                return requests.get(url)

    except ValueError:
        print("Unknown error occurred during execution")


# append spaces to a string to make it even length
def postfix(string, length):
    new_str = string
    while len(new_str) < length:
        new_str += ' '
    return new_str


# pretty print a line out to the terminal
def pretty_print(repo, tag, sha1):
    string_list = [postfix(repo, 30), postfix(tag, 20), sha1]
    print(''.join(string_list))


def main():
    global exclude_list, _SERVER

    _url = ""
    delete = False
    username = ""
    password = ""
    image_to_delete = ""

    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:u:p:d:h',
                                   [' server', 'username', 'password', 'delete', 'help'])
        if not opts:
            usage()
            sys.exit(2)
    except getopt.GetoptError as err:
        print(str(err))
        usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage()
            sys.exit(2)
        elif opt in ('-s', '--server'):
            global _SERVER
            _SERVER = "https://" + arg + "/v2/"
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-d', '--delete'):
            delete = True
            image_to_delete = arg
        else:
            usage()
            sys.exit(2)

    global _AUTH_TOKEN
    if len(username) > 0 and len(password) > 0:
        _AUTH_TOKEN = base64.b64encode('%s:%s' % (username, password))
    else:
        _AUTH_TOKEN = ""

    _url = _SERVER + _CATALOG
    result = make_request(_url, "GET")
    repos = result.json()

    for repo in repos["repositories"]:
        _url = _SERVER + repo + _TAGS
        result = make_request(_url, "GET")
        tags = result.json()
        try:
            for tag in tags["tags"]:
                _url = _SERVER + repo + _MANIFEST + tag
                result = make_request(_url, "GET")
                # fs_layers = result.json()
                sha1 = result.headers[_DOCKER_CONT_HDR]
                _lookupStr = repo + ":" + tag
                if delete and _lookupStr == image_to_delete:
                    print("removing " + repo + ":" + tag)
                    _url = _SERVER + repo + _MANIFEST + sha1
                    make_request(_url, "DELETE")
                else:
                    pretty_print(repo, tag, sha1)

        except TypeError:
            print("**** No tag found for this image/repo")


if __name__ == "__main__":
    main()
