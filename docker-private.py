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
    print('  -s   --server            Docker registry URL, prefixed with http:// or https://')
    print('  -u   --username          docker registry user-name')
    print('  -p   --password          docker registry user\'s password')
    print('  -d   --delete            a specific image name:tag format')
    print('')
    print('example: ' + sys.argv[0] + ' -s http://129.157.181.199:5000 -u admin -p p@ssword -d name:1.0.0')


def make_request(url, method):
    global _AUTH_TOKEN

    try:
        if method == "DELETE":
            # ignore 404s as they mean it is already gone
            if len(_AUTH_TOKEN) > 0:
                r = requests.delete(url, headers={"Authorization": "Basic %s" % _AUTH_TOKEN,
                                                  "Accept": "application/vnd.docker.distribution.manifest.v2+json"})
                if r.status_code not in range(200, 299) and r.status_code != 404:
                    raise ValueError("\"%s\":DELETE returned status code %s" % (url, r.status_code))
                return r
            else:
                r = requests.delete(url, headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
                if r.status_code not in range(200, 299) and r.status_code != 404:
                    raise ValueError("\"%s\":DELETE returned status code %s" % (url, r.status_code))
                return r
        else:
            if len(_AUTH_TOKEN) > 0:
                r = requests.get(url, headers={"Authorization": "Basic %s" % _AUTH_TOKEN,
                                               "Accept": "application/vnd.docker.distribution.manifest.v2+json"})
                if r.status_code not in range(200, 299):
                    raise ValueError("\"%s\":GET returned status code %s" % (url, r.status_code))
                return r
            else:
                r = requests.get(url, headers={"Accept": "application/vnd.docker.distribution.manifest.v2+json"})
                if r.status_code not in range(200, 299):
                    raise ValueError("\"%s\":GET returned status code %s" % (url, r.status_code))
                return r

    except ValueError as ex:
        print("Unknown error occurred during execution: %s" % ex)


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


# get details on a repo item
def get_repo_item_details(repo):
    item_detail_list = []
    global _SERVER, _TAGS
    _url = _SERVER + repo + _TAGS
    result = make_request(_url, "GET")
    tags = result.json()
    try:
        for tag in tags["tags"]:
            _url = _SERVER + repo + _MANIFEST + tag
            result = make_request(_url, "GET")
            sha1 = result.headers[_DOCKER_CONT_HDR]
            item_detail_list.append((repo, tag, sha1, result.json()))
    except TypeError:
        pass
    return item_detail_list


# list all items in a repo
def list_repo():
    global _SERVER, _CATALOG

    _url = _SERVER + _CATALOG
    result = make_request(_url, "GET")
    repos = result.json()
    num_repos = 0
    for repo in repos["repositories"]:
        item_list = get_repo_item_details(repo)
        for _, tag, sha1, _ in item_list:
            pretty_print(repo, tag, sha1)
            num_repos += 1
    if num_repos == 0:
        print("empty repository")


# delete a specific name:version item
def delete_repo_item(repo, tag):
    # get all the versions for this item
    item_list = get_repo_item_details(repo)
    found = False
    delete_set = set()
    for _, item_tag, sha1, fs_layers in item_list:
        # can we find the one that matches?
        if tag == item_tag:
            found = True
            if sha1 not in delete_set:
                delete_set.add(sha1)
                _url = _SERVER + repo + _MANIFEST + sha1
                print(sha1)
                make_request(_url, "DELETE")
                if _FS_LAYERS in fs_layers:
                    for fs_layer in fs_layers[_FS_LAYERS]:
                        sha1_layer = fs_layer[_BLOB_SUM]
                        if sha1_layer not in delete_set:
                            delete_set.add(sha1_layer)
                            _url = _SERVER + repo + _MANIFEST + sha1_layer
                            print(sha1_layer)
                            make_request(_url, "DELETE")
    if not found:
        print("could not find %s:%s" % (repo, tag))
    else:
        print("make sure you run:")
        print("  docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml")


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
            if not arg.startswith("http://") and not arg.startswith("https://"):
                print("server url must start with http:// or https://")
                sys.exit(2)
            _SERVER = arg + "/v2/"
        elif opt in ('-u', '--username'):
            username = arg
        elif opt in ('-p', '--password'):
            password = arg
        elif opt in ('-d', '--delete'):
            delete = True
            image_to_delete = arg
            if len(image_to_delete.strip()) < 3 or ":" not in image_to_delete:
                print("delete error: requires name:tag format")
                sys.exit(2)
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

    if delete:
        repo = image_to_delete.split(':')[0]
        tag = image_to_delete.split(':')[1]
        delete_repo_item(repo.strip(), tag.strip())
    else:
        list_repo()


if __name__ == "__main__":
    main()
