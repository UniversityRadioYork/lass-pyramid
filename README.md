lass-pyramid
============

The Pyramid application that powers the URY (University Radio York) website.

This is the code _only_, and is licenced under 2-clause BSD.  It supercedes the `django-lass-*` and `lass` repositories.

Requirements
------------

* Python 3.3+
* Setuptools or something else that can understand a "setup.py".
* See `setup.py` for other requirements which should be installed automatically via that script.

Usage
-----

Use `python setup.py develop` to install the application.  Doing this in a virtualenv is recommended.

Use the Pyramid pserve/proutes/etc programs as usual.

Scripts for maintaining the website may be published at a later date.

What's provided
---------------

* All Python-based website code, licenced under BSD
* That's it for now

What's missing
--------------

* Templates
* Assets
* Routing configuration
* Documentation (URY have a privately available document collection, but this is not yet available outside the station)
* API server; see UniversityRadioYork/MyRadio.

In addition, since we tend to update all of the website "in step" in a private workflow, updates to this repository from URY may be slow to materialise.

For information on producing these, lodge an issue or contact CaptainHayashi.
