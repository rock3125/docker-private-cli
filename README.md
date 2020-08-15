## very simple private docker registry reader
Written in Python 3, based on https://github.com/dhamya/docker-registry-cli

usage:
```
# list repo
./docker-private.py -s https://129.157.181.199:5000 -u admin -p p@ssw0rd

# or list repo without credentials

./docker-private.py -s https://129.157.181.199:5000

# remove an item from the repo
./docker-private.py -s https://129.157.181.199:5000 -d name:tag

# and then run garbage collection to actually remove it
docker exec registry bin/registry garbage-collect /etc/docker/registry/config.yml
```

## Delete function does not garbage collect
see https://docs.docker.com/registry/garbage-collection/

## Running a private repo
To run a private repo with certs locally on port 8443
```
docker run -d \
  --restart=always \
  --name registry \
  -v /docker-registry:/var/lib/registry \
  -v "$(pwd)"/certs:/certs \
  -e REGISTRY_HTTP_ADDR=0.0.0.0:443 \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/cert-bundle.txt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/key.txt \
  -e REGISTRY_STORAGE_DELETE_ENABLED="true" \
  -p 8443:443 \
  registry:2
```
To run a private repo without certs locally on port 8080
```
docker run -d \
  --restart=always \
  --name registry \
  -v /docker-registry:/var/lib/registry \
  -e REGISTRY_HTTP_ADDR=0.0.0.0:8000 \
  -e REGISTRY_STORAGE_DELETE_ENABLED="true" \
  -p 8080:8000 \
  registry:2
```

## adding files to your private repo
```
docker tag local-item:1.0.0 localhost:8443/local-item:1.0.0
docker push localhost:8443/local-item:1.0.0
```
