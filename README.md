# mailman-membership

A simple API that allows to add members to and remove members from a Mailman 3 mailing list. Written in Python (wsgi).

The API supports the following endpoints:

  * /add:            Add email addresses
  * /remove:         Remove email addresses
  * /clear:          Remove all email addresses
  * /replace:        Remove and add (in this order) email addresses
  * /replace_all:    Remove all email addresses and add new ones


The full documentation of the API can be found in [api_documentation.txt](api_documentation.txt).

## Configuration

To set up a configuration, you can just copy/rename the file `config.json.sample` to `config.json` and set up some lists in there.

If you changed the configuration of you Mailman installation, you might need to change the parameters `resturl`, `restadmin` and `restpass`.

## Testserver

In order to start a testserver serving the API, just run

    python3 testserver.py

## Installation using Apache

In order to make the API available via http(s)://my.domain.tld/public/path/ using Apache, you can write into the site configuration of my.domain.tld

    <VirtualHost>
        … # your vhost configuration

        WSGIScriptAlias /public/path /path/to/dir/mailman_membershipmanager.py
        WSGIPythonPath /path/to/dir
        <Directory /path/to/dir/>
            <Files mailman_membershipmanager.py>
                Require all granted
            </Files>
        </Directory>
     </VirtualHost>
