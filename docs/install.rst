.. _installation:

Installation
============

To use certbot-openshift, you must install it on the system where you plan run the certbot client.

*Note: Unfortunately, you must install certbot-openshift globally on the system. Certbot will not be able to find the package if you install it in a virtual environment, even if certbot is installed and run from the same virtual environment.*

.. code-block:: bash

    $ pip install certbot
    $ pip install certbot-openshift
