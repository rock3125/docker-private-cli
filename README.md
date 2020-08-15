## very simple private docker registry reader
Written in Python 3, based on https://github.com/dhamya/docker-registry-cli

usage:
```
./docker-private.py -s 129.157.181.199:5000 -u admin -p p@ssw0rd

# or

./docker-private.py -s 129.157.181.199:5000
```

## Delete function does not garbage collect
see https://docs.docker.com/registry/garbage-collection/
