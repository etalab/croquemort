# CroqueMort

## Vision

The aim of this project is to provide a way to check HTTP resources: hunting 404s, updating redirections and so on.

For instance, given a website that stores a list of external resources, this product allows the owner to send its URLs in bulk and retrieve information for each URL fetched in background (only status code and content type for now). This way he can be informed of dead links or outdated resources and acts accordingly.

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
$ pip install -r requirements.txt
```

You're good to go!


## Usage

First you have to run the `http` service in order to receive incoming HTTP calls. You can run it with this command:

```shell
$ nameko run http
starting services: http_server
Connected to amqp://guest:**@127.0.0.1:5672//
```

Then launch the `crawler` in a new shell that will fetch the submitted URL in the background.

```shell
$ nameko run crawler
starting services: url_crawler
Connected to amqp://guest:**@127.0.0.1:5672//
```


### Fetching one URL

Now you can use your favorite HTTP client (mine is [httpie](https://github.com/jakubroztocil/httpie)) to issue a POST request againt `localhost:8000/check/one` with the URL as a parameter:

```shell
$ http :8000/check/one url="https://larlet.fr/david/"
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 29
Content-Type: text/plain; charset=utf-8
Date: Tue, 26 May 2015 14:06:28 GMT

{
  "url-hash": 9094602859126452657
}
```

The service returns a URL hash that will be used to retrieve informations related to that URL:

```shell
$ http :8000/url/9094602859126452657
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 91
Content-Type: text/plain; charset=utf-8
Date: Tue, 26 May 2015 14:07:18 GMT

{
  "url": "https://larlet.fr/david/", 
  "status": "200", 
  "content-type": "text/html; charset=utf-8"
}
```


### Fetching many URLs

You can also use your  HTTP client to issue a POST request againt `localhost:8000/check/many` with the URLs and the name of the group as parameters:

```shell
$ http :8000/check/many urls:='["https://larlet.fr/david/","http://noirbizarre.info/"]' group="group-name"
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 31
Content-Type: text/plain; charset=utf-8
Date: Tue, 26 May 2015 14:09:22 GMT

{
  "group-hash": 6931515092077926289
}
```

This time, the service returns a group hash that will be used to retrieve informations related to that group:

```shell
$ http :8000/group/6931515092077926289
HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 296
Content-Type: text/plain; charset=utf-8
Date: Tue, 26 May 2015 14:10:04 GMT

{
  "https://larlet.fr/david/": {
    "url": "https://larlet.fr/david/", 
    "status": "200", 
    "group": "6931515092077926289", 
    "content-type": "text/html; charset=utf-8"
  }, 
  "http://noirbizarre.info/": {
    "url": "http://noirbizarre.info/", 
    "status": "200", 
    "group": "6931515092077926289", 
    "content-type": "text/html"
  }, 
  "name": "group-name"
}
```

Note that in both cases, the `http` and the `crawler` services return interesting logging information for debugging.


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


## Versioning

Version numbering follows the [Semantic versioning](http://semver.org/) approach.


## License

We’re using the [MIT license](https://tldrlegal.com/license/mit-license). 


## Credits

* [David Larlet](https://larlet.fr/david/)
