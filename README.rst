.. image:: LOGO/osf-cli-logo-v1-small.png
   :alt: osfclient
   :align: right

*********
osfclient
*********

|travisbadge|

The ``osfclient`` is a python library and a command-line client for up-
and downloading files to and from your `Open Science
Framework <//osf.io>`__ projects. The *Open Science Framework* (OSF) is
an open source project which facilitates the open collaboration of
researchers on the web, by sharing data and other research outputs.

As such the OSF hosts large data sets, associated with papers or
scientific projects, that can be freely downloaded. The *osfclient*
allows people to store and retrieve large datasets associated to their
scientific projects and papers on the OSF via the command line
interface. If you are completely new to the OSF you can `read their
introductory materials <https://cos.io/our-products/osf>`__

This is a very new project, it has some rough edges.

.. |travisbadge| image:: https://travis-ci.org/osfclient/osfclient.svg?branch=master
   :target: https://travis-ci.org/osfclient/osfclient

Installing
==========

To use ``osfclient`` install it via pip:

::

    $ pip install osfclient

For details on participating in the development of ``osfclient`` check
out the `Contributing
section <https://github.com/osfclient/osfclient#contributing>`__.

Usage
=====

This project provides two things: a python library and a command-line
program for interacting with files stored in the
`OSF <https://osf.io/>`__.

The python library forms the basis for the command-line program. If you
want programmatic access to your files use the library, otherwise try
out the command-line program.

Read the full documentation: https://osfclient.readthedocs.io/en/latest/

Below are some examples on how to use it:

::

    # get help and see available commands, get help on a specific command
    $ osf -h
    $ osf <command> -h

    # setup a local folder for an existing project
    $ osf init

    # list all files for the project
    $ osf ls

    # fetch all files for the project
    $ osf clone

    # fetch an individual file from a project
    $ osf fetch remote/path.txt local/file.txt

    # get web view url for an individual file from a project
    $ osf geturl remote/path.txt

    # add a new file
    $ osf upload local/file.txt remote/path.txt

    # add a new directory
    $ osf upload -r local/directory/ remote/directory

If the project is private you will need to provide authentication
details. The password will be retrieved from the ``OSF_PASSWORD``
environment variable or you will be asked directly by the tool when you
run it.

You can set default values by using a configuration file in the
current directory. This is what ``osf init`` does for you. To set the
username and project ID create ``.osfcli.config``:

::

    [osf]
    username = yourOSFaccount@example.com
    project = 9zpcy

after which you can simply run ``osf ls`` to list the contents of the
project.

JSON-LD Support
===============

You can find some json-ld support for project metadata. To create a project in OSF with JSON-LD, you can use the following command.

::

    from osfclient import OSF
    osf = OSF()
    osf.login(token="XYZ")
    osf.create_project_jsonld(jsonld)

The `jsonld` object have to have the following structure. 
Title and category are mandatory, description and keywords should be given by the user, otherwise it is empty. 

::

    {
        "https://schema.org/category":"project",
        "https://schema.org/description":"this is a test for preprint citations",
        "https://schema.org/dateModified":"2017-03-17T16:11:35.721000",
        "https://schema.org/title":"Preprint Citations Test",
        "https://schema.org/dateCreated":"2017-03-17T16:09:14.864000",
        "https://schema.org/publicAccess":true,
        "https://schema.org/keywords":[
            "qatest"
        ],
        "https://schema.org/identifier":"f3szh",
        "https://schema.org/url":"https://api.osf.io/v2/nodes/f3szh/",
        "https://schema.org/downloadUrl":"https://api.osf.io/v2/nodes/f3szh/files/"
    }

All other keys are optional or cannot be set by the user, but will be printed out, when you call want to get the metadata.

::

    from osfclient import OSF
    osf = OSF()
    osf.login(token="XYZ")
    osf.project("f3szh").metadata(jsonld=True)

Contributing
============

Contributions from everyone and anyone are welcome. Fork this
repository, make your changes, add a test to cover them and create a
Pull Request. Then one of the maintainers will review your changes. When
all comments have been addressed and all tests pass your changes will be
merged.

To setup a development version:

::

    $ git clone https://github.com/YOURNAMEHERE/osfclient
    $ git remote add upstream https://github.com/osfclient/osfclient
    $ cd osfclient
    $ pip install -r devRequirements.txt
    $ pip install -e.

There are a few secret keys relevant to this project, like passwords to
pypi.org, test.pypi.org, and the osfclient email account. We store these in an
encrypted git repo on `Keybase <//keybase.io>`__. If you need access to this
repo, contact any of the following maintainters on Keybase:

- Tim Head (@betatim)
- Ben Lindsay (@benlindsay)
- Fitz Elliott (@felliott)
- Longze Chen (@cslzchen)

For more details and instructions: `CONTRIBUTING.md <CONTRIBUTING.md>`__
