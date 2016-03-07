# Croquemort

## Vision

The aim of this project is to provide a way to check HTTP resources: hunting 404s, updating redirections and so on.

For instance, given a website that stores a list of external resources (html, images or documents), this product allows the owner to send its URLs in bulk and retrieve information for each URL fetched in background (status code and useful headers for now). This way he can be informed of dead links or outdated resources and acts accordingly.

The name comes from the [French term](https://fr.wikipedia.org/wiki/Croque-mort) for [Funeral director](https://en.wikipedia.org/wiki/Funeral_director).


## Language

The development language is English. All comments and documentation should be written in English, so that we don't end up with “franglais” methods, and so we can share our learnings with developers around the world.


## History

We started this project on May, 2015 for [data.gouv.fr](http://data.gouv.fr/).

We open-sourced it since the beginning because we want to design things in the open and involve citizens and hackers in our developments.


## Installation

We’re using these technologies: RabbitMQ and Redis. You have to install and launch these dependencies prior to install and run the Python packages.

Once installed, run these commands to setup the project:

```shell
$ python3.5 -m venv ~/.virtualenvs/croquemort
$ source ~/.virtualenvs/croquemort/bin/activate
$ pip3.5 install -r requirements.txt
```

You're good to go!


## Usage

First you have to run the `http` service in order to receive incoming HTTP calls. You can run it with this command:

```shell
$ nameko run croquemort.http
starting services: http_server
Connected to amqp://guest:**@127.0.0.1:5672//
```

Then launch the `crawler` in a new shell that will fetch the submitted URL in the background.

```shell
$ nameko run croquemort.crawler
starting services: url_crawler
Connected to amqp://guest:**@127.0.0.1:5672//
```

You can optionnaly use the proposed configuration with more workers for the crawler (from 10 (default) to 50):

```shell
$ nameko run --config config_crawler.yaml croquemort.crawler
```


### Browsing your data

At any time, you can open `http://localhost:8000/` and check the availability of your URLs collections within a nice dashboard that allows you to filter by statuses, content types, URL schemes, last updates and/or domains. There is even a CSV export of the data you are currently viewing if you want to script something.


### Fetching one URL

Now you can use your favorite HTTP client (mine is [httpie](https://github.com/jakubroztocil/httpie)) to issue a POST request againt `localhost:8000/check/one` with the URL as a parameter:

```shell
$ http :8000/check/one url="https://www.data.gouv.fr/fr/"
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 28
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:21:50 GMT

{
  "url-hash": "fc6040c5"
}
```

The service returns a URL hash that will be used to retrieve informations related to that URL:

```shell
$ http :8000/url/fc6040c5
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 335
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:22:57 GMT

{
  "etag": "",
  "url": "https://www.data.gouv.fr/fr/",
  "content-length": "",
  "content-disposition": "",
  "content-md5": "",
  "content-location": "",
  "expires": "",
  "status": "200",
  "updated": "2015-06-03T16:21:52.569974",
  "last-modified": "",
  "content-encoding": "gzip",
  "content-type": "text/html; charset=utf-8"
}
```

Or you can use the URL passed as a GET parameter (less error prone):

```shell
$ http GET :8000/url url=https://www.data.gouv.fr/fr/
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 335
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:23:35 GMT

{
  "etag": "",
  "url": "https://www.data.gouv.fr/fr/",
  "content-length": "",
  "content-disposition": "",
  "content-md5": "",
  "content-location": "",
  "expires": "",
  "status": "200",
  "updated": "2015-06-03T16:21:52.569974",
  "last-modified": "",
  "content-encoding": "gzip",
  "content-type": "text/html; charset=utf-8"
}
```

Both return the same amount of information.


### Fetching many URLs

You can also use your  HTTP client to issue a POST request againt `localhost:8000/check/many` with the URLs and the name of the group as parameters:

```shell
$ http :8000/check/many urls:='["https://www.data.gouv.fr/fr/","https://www.data.gouv.fr/s/images/2015-03-31/d2eb53b14c5f4e6690e150ea7be40a88/cover-datafrance-retina.png"]' group="datagouvfr"
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 30
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:24:00 GMT

{
  "group-hash": "efcf3897"
}
```

This time, the service returns a group hash that will be used to retrieve informations related to that group:

```shell
$ http :8000/group/efcf3897
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 941
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:26:04 GMT

{
  "179d104f": {
    "content-encoding": "",
    "content-disposition": "",
    "group": "efcf3897",
    "last-modified": "Tue, 31 Mar 2015 14:38:37 GMT",
    "content-md5": "",
    "url": "https://www.data.gouv.fr/s/images/2015-03-31/d2eb53b14c5f4e6690e150ea7be40a88/cover-datafrance-retina.png",
    "status": "200",
    "expires": "",
    "content-type": "image/png",
    "content-length": "280919",
    "updated": "2015-06-03T16:24:00.405636",
    "etag": "\"551ab16d-44957\"",
    "content-location": ""
  },
  "name": "datagouvfr",
  "fc6040c5": {
    "content-disposition": "",
    "content-encoding": "gzip",
    "group": "efcf3897",
    "last-modified": "",
    "content-md5": "",
    "content-location": "",
    "content-length": "",
    "expires": "",
    "content-type": "text/html; charset=utf-8",
    "status": "200",
    "updated": "2015-06-03T16:24:02.398105",
    "etag": "",
    "url": "https://www.data.gouv.fr/fr/"
  }
}
```

Or you can use the group name passed as a GET parameter (less error prone):

```shell
$ http GET :8000/group/ group=datagouvfr
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 335
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:23:35 GMT

{
  "etag": "",
  "url": "https://www.data.gouv.fr/fr/",
  "content-length": "",
  "content-disposition": "",
  "content-md5": "",
  "content-location": "",
  "expires": "",
  "status": "200",
  "updated": "2015-06-03T16:21:52.569974",
  "last-modified": "",
  "content-encoding": "gzip",
  "content-type": "text/html; charset=utf-8"
}
```

Both return the same amount of information.


### Filtering results

You can filter results returned for a given group by header (or status) with the `filter_` prefix:

```shell
$ http GET :8000/group/efcf3897 filter_content-type="image/png"
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 539
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:27:07 GMT

{
  "179d104f": {
    "content-encoding": "",
    "content-disposition": "",
    "group": "efcf3897",
    "last-modified": "Tue, 31 Mar 2015 14:38:37 GMT",
    "content-md5": "",
    "url": "https://www.data.gouv.fr/s/images/2015-03-31/d2eb53b14c5f4e6690e150ea7be40a88/cover-datafrance-retina.png",
    "status": "200",
    "expires": "",
    "content-type": "image/png",
    "content-length": "280919",
    "updated": "2015-06-03T16:24:00.405636",
    "etag": "\"551ab16d-44957\"",
    "content-location": ""
  },
  "name": "datagouvfr"
}
```

You can exclude results returned for a given group by header (or status) with the `exclude_` prefix:

```shell
$ http GET :8000/group/efcf3897 exclude_content-length=""
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 539
Content-Type: text/plain; charset=utf-8
Date: Wed, 03 Jun 2015 14:27:58 GMT

{
  "179d104f": {
    "content-encoding": "",
    "content-disposition": "",
    "group": "efcf3897",
    "last-modified": "Tue, 31 Mar 2015 14:38:37 GMT",
    "content-md5": "",
    "url": "https://www.data.gouv.fr/s/images/2015-03-31/d2eb53b14c5f4e6690e150ea7be40a88/cover-datafrance-retina.png",
    "status": "200",
    "expires": "",
    "content-type": "image/png",
    "content-length": "280919",
    "updated": "2015-06-03T16:24:00.405636",
    "etag": "\"551ab16d-44957\"",
    "content-location": ""
  },
  "name": "datagouvfr"
}
```

Note that in both cases, the `http` and the `crawler` services return interesting logging information for debugging.


### Computing many URLs

You can programmatically register new URLs and groups using the RPC proxy. There is an example within the `example_csv.py` file which computes URLs from a CSV file (one URL per line).

```shell
$ PYTHONPATH=. python tests/example_csv.py --csvfile path/to/your/file.csv --group groupname
Group hash: 2752262332
```

The script returns a group hash that you can use through the HTTP interface as documented above.


### Frequencies

You may want to periodically check existing groups of URLs in the background. In that case launch the `timer` service:

```shell
$ nameko run croquemort.timer
starting services: timer
Connected to amqp://guest:**@127.0.0.1:5672//
```

You can now specify a `frequency` parameter when you `POST` against `/check/many` or when you launch the command via the shell:

```shell
$ PYTHONPATH=. python example_csv.py --csvfile path/to/your/file.csv --group groupname --frequency hourly
Group hash: 2752262332
```

There are three possibilities: "hourly", "daily" and "monthly". If you don't specify any you'll have to refresh URL checks manually. The `timer` service will check groups with associated frequencies and refresh associated URLs accordingly.


### Migrations

You may want to migrate some data over time with the `migrations` service:

```shell
$ nameko run croquemort.migrations
starting services: migrations
Connected to amqp://guest:**@127.0.0.1:5672//
```

You can now run a nameko shell:

```shell
$ nameko shell
>>> n.rpc.migrations.split_content_types()
>>> n.rpc.migrations.delete_urls_for('www.data.gouv.fr')
>>> n.rpc.migrations.delete_urls_for('static.data.gouv.fr')
```

The `split_content_types` migration is useful if you use Croquemort prior to the integration of the report: we use to store the whole string without splitting on the `charset` leading to fragmentation of the Content-types report graph.

The `delete_urls_for` is useful if you want to delete all URLs related to a given `domain` you must pass as a paramater: we accidently checked URLs that are under our control so we decided to clean up in order to reduce the size of the Redis database and increase the relevance of reports.

You are encouraged to add your own generic migrations to the service and share those with the community via pull-requests (see below).


## Contributing

We’re really happy to accept contributions from the community, that’s the main reason why we open-sourced it! There are many ways to contribute, even if you’re not a technical person.

We’re using the infamous [simplified Github workflow](http://scottchacon.com/2011/08/31/github-flow.html) to accept modifications (even internally), basically you’ll have to:

* create an issue related to the problem you want to fix (good for traceability and cross-reference)
* fork the repository
* create a branch (optionally with the reference to the issue in the name)
* hack hack hack
* commit incrementally with readable and detailed commit messages
* submit a pull-request against the master branch of this repository

We’ll take care of tagging your issue with the appropriated labels and answer within a week (hopefully less!) to the problem you encounter.

If you’re not familiar with open-source workflows or our set of technologies, do not hesitate to ask for help! We can mentor you or propose good first bugs (as labeled in our issues). Also welcome to add your name to Credits section of this document.


### Submitting bugs

You can report issues directly on Github, that would be a really useful contribution given that we lack some user testing on the project. Please document as much as possible the steps to reproduce your problem (even better with screenshots).


### Adding documentation

We’re doing our best to document each usage of the project but you can improve this file and add you own sections.


### Hacking backend

Hello fellow hacker, it’s good to have you on board! We plan to implement these features in a reasonable future, feel free to pick the one you want to contribute too and declare an issue for it:

* verifying mimetypes, extensions, sizes, caches, etc
* periodical fetching
* reporting for a group of URLs


### Testing

Before submitting any pull-request, you must ensure tests are passing.
You should add tests for any new feature and/or bugfix.
You can run tests with the following command:
```shell
$ python -m pytest
```

You must have rabbitmq and redis running to pass the test.

A ``docker-compose.yml`` file is provided to be quickly ready:
```shell
$ docker-compose up -d
Creating croquemort_redis_1...
Creating croquemort_rabbitmq_1...
$ python -m pytest
```

In the case you use your own middleware with different configuration,
you can pass this configuration as py.test command line arguments:
```shell
python -m pytest --redis-uri=redis://myredis:6379/0 --amqp-uri=amqp://john:doe@myrabbit
```

Read the py.test help to see all available options:
```shell
python -m pytest --help
```


## Versioning

Version numbering follows the [Semantic versioning](http://semver.org/) approach.


## License

We’re using the [MIT license](https://tldrlegal.com/license/mit-license).


## Credits

* [David Larlet](https://larlet.fr/david/)
