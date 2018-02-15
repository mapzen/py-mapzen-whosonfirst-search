# py-mapzen-whosonfirst-search

Python packages for talking to the Who's On First (spelunker) Elasticsearch index

## Install

```
sudo pip install -r requirements.txt .
```

## IMPORTANT

This library is provided as-is, right now. It lacks proper
documentation which will probably make it hard for you to use unless
you are willing to poke and around and investigate things on your
own.

## Tools

_This documentation is incomplete._

### wof-es-index

Index Who's On First documents in a Who's On First "spelunker" Elasticsearch endpoint.

```
./scripts/wof-es-index -h
Usage: wof-es-index [options] [files]

Options:
  -h, --help            show this help message and exit
  -s SOURCE, --source=SOURCE
                        The path to the directory you want to index. This flag is deprecated, please use -m(ode) directory) instead
  -m MODE, --mode=MODE  A valid indexing mode. Valid modes are: directory, filelist, files, meta, repo, sqlite.
  -b, --bulk            Index files in bulk mode (default is False)
  --index=INDEX         Where to write the records to (default is spelunker)
  --host=HOST           What host your search index lives (default is localhost)
  --port=PORT           What port your search index lives on (default is 9200)
  --timeout=TIMEOUT     Timeout in seconds for talking to you search index lives on (default is 600)
  -v, --verbose         Be chatty (default is false)
```

## See also

* https://github.com/mapzen/whosonfirst-data
* https://github.com/mapzen/py-mapzen-whosonfirst-index
* https://github.com/mapzen/py-mapzen-whosonfirst-elasticsearch
* https://github.com/mapzen/es-whosonfirst-schema
