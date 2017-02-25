.. _usage:

Usage
=====


1. Obtain a `bearer token<https://docs.openshift.com/dedicated/dev_guide/service_accounts.html#using-a-service-accounts-credentials-inside-a-container>`_ to authenticate with Openshift. This can be your personal token or the token of a `service account <https://docs.openshift.com/dedicated/dev_guide/service_accounts.html#managing-service-accounts>`_.

2. Run certbot and tell it to use the ``certbot_openshift:installer`` installer plugin.

.. code-block:: bash

    certbot run -d my.domain.com \
                # Insert your authentication plugin settings here \
                -i certbot-openshift:installer \
                --certbot-openshift:installer-api-host api.example.com
                --certbot-openshift:installer-namespace my-project-namespace
                --certbot-openshift:installer-token $TOKEN

3. If you already have a certificate, you can use certbot to install it.

.. code-block:: bash

    certbot install -d my.domain.com \
                    -i certbot-openshift:installer \
                    --chain-path /etc/letsencrypt/live/my.domain.com/chain.pem
                    --cert-path /etc/letsencrypt/live/my.domain.com/cert.pem
                    --key-path /etc/letsencrypt/live/my.domain.com/privkey.pem
                    --certbot-openshift:installer-api-host api.example.com
                    --certbot-openshift:installer-namespace my-project-namespace
                    --certbot-openshift:installer-token $TOKEN

Theres a few things here to pay attention to here.

**Certbot Options:**

-d domain     Certificate domain name.
-i installer  Tell certbot to use certbot-openshift for certificate installation by specifying ``certbot-openshift:installer``.

**Certbot-Openshift Options:**

--api-host   Openshift API domain.
--namespace  Openshift route namespace (project).
--token      Openshift Bearer Token.

Certbot will attempt to fine the route matching the given domain name and install the certificate on it. If a matching route can't be found, the command will fail.
