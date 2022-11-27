# wacks by warby

![tests passing badge](https://github.com/allisonking/wacks-by-warby/actions/workflows/pytest.yaml/badge.svg)

Send Discord alerts whenever there's new sales at [WicksByWerby](https://www.etsy.com/shop/WicksByWerby)

![diagram](./images/wack.png)

## Developer Setup

```sh
# Set up a virtual env
$ python -m venv venv
$ source venv/bin/activate

# Install pip tools
$ python -m pip install pip-tools

# Install dependencies
pip install -r requirements.txt
```

### Installing new dependencies

We use [pip-tools](https://github.com/jazzband/pip-tools) for dependency management. If you need a new dependency, add it to `requirements.in`, then:

```sh
pip-compile requirements.in
```

Will generate a new `requirements.txt` file for you.
