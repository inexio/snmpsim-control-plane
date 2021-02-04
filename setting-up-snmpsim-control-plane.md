# Installation snmpsim-control-plane

## Installation itself

First of all we need to install snmpsim-control-plane and snmpsim. It might be better to use the latest unreleased version from GitHub.

```
pip install setuptools -U
pip install https://github.com/inexio/snmpsim-control-plane/archive/master.zip
pip install https://github.com/inexio/snmpsim/archive/master.zip
```

The snmpsim have to run with an non-priviliedged-user and group (for example snmpsim)

```
adduser snmpsim
mkdir -p /var/snmpsim /etc/snmpsim /var/run/snmpsim /var/log/snmpsim/metrics
susu - snmpsim
```

## Configuration files 

You need to create a config file for the management API tools:

```
cat > /etc/snmpsim/snmpsim-management.conf <<EOF
```

Add these lines to the file:

```
SQLALCHEMY_DATABASE_URI = 'sqlite:////var/snmpsim/snmpsim-mgmt-restapi.db'
DEBUG = False
SNMPSIM_MGMT_DATAROOT = '/var/snmpsim/data'
SNMPSIM_MGMT_TEMPLATE = '/etc/snmpsim/snmpsim-command-responder.j2'
SNMPSIM_MGMT_DESTINATION = '/var/snmpsim/supervised'
EOF
```

Also you have to create a config file for Metrics API tools:

```
cat > /etc/snmpsim/snmpsim-metrics.conf <<EOF
```

Add these lines to the file:

```
SQLALCHEMY_DATABASE_URI = 'sqlite:////var/snmpsim/snmpsim-metrics-restapi.db'
EOF
```

And for the bootstrap underlying databases

```
snmpsim-mgmt-restapi --config /etc/snmpsim/snmpsim-management.conf \
    --recreate-db
    
snmpsim-metrics-restapi --config /etc/snmpsim/snmpsim-metrics.conf \
    --recreate-db
```



## SNMP Simulator Options

We want that the command responder is producing metrics, this could be enabled by passing the command-line optionto the process of command responder. You only have to modify the Management API template:

```
cat > /etc/snmpsim/snmpsim-command-responder.j2 <<EOF
#!/bin/sh
{% if context['labs'] %}
exec snmpsim-command-responder \
  --reporting-method fulljson:/var/log/snmpsim/metrics \
  {% for lab in context['labs'] %}
    {% for agent in lab['agents'] %}
      {% for engine in agent['engines'] %}
    --v3-engine-id "{{ engine['engine_id'] }}" \
        {% for user in engine['users'] %}
      --v3-user "{{ user['user'] }}" \
          {% if user['auth_key'] is not none %}
      --v3-auth-key "{{ user['auth_key'] }}" \
      --v3-auth-proto "{{ user['auth_proto'] }}" \
            {% if user['priv_key'] is not none %}
      --v3-priv-key "{{ user['priv_key'] }}" \
      --v3-priv-proto "{{ user['priv_proto'] }}" \
            {% endif %}
          {% endif %}
        {% endfor %}
        {% for endpoint in engine['endpoints'] %}
      --agent-{{ endpoint['protocol'] }}-endpoint "{{ endpoint['address'] }}" \
        {% endfor %}
      --data-dir "{{ agent['data_dir'] }}" \
      {% endfor %}
    {% endfor %}
  {% endfor %}
{% endif %}
EOF
```

To bind priviledeg UNIX Ports (<1024), you have to run *snmpsim-mgmt-supervisor* under root and tell *snmpsim-command-responder* to drop the priviledges after binding priviledged ports

This could be done if you use the options for the *snmpsim-command-responder* "--process-user" and "--process-group", as you could see in our service template too, here you should specify the non-priviledged-user and the group of this user.

```
cat > /etc/snmpsim/snmpsim-command-responder.j2 <<EOF
#!/bin/sh
{% if context['labs'] %}
exec snmpsim-command-responder \
  --process-user snmpsim --process-group snmpsim \
  ...
```

If you want to bind only non-priviledeg ports you can run *snmpsim-mgmt-supervisor* under a non-privileged-user and use these above mentioned options

## Rest-API servers

For bringing up Rest-API servers, you have just to follow WSGI application setup guidelines.

Here followed by an example for [gunicorn](https://gunicorn.org/) 

```
pip install gunicorn 
```

 To start the gunicorn (MGMT-config) on localhost, port 5000 use this command

```
gunicorn -b 127.0.0.1:5000 \
   --env "SNMPSIM_MGMT_CONFIG=/etc/snmpsim/snmpsim-management.conf" \
  --access-logfile /var/log/snmpsim/mgmt-access.log \
  --error-logfile /var/log/snmpsim/mgmt-error.log  \
  --daemon \
  snmpsim_control_plane.wsgi.management:app
```

and for the metrics config on port 5001:

```
gunicorn -b 127.0.0.1:5001 \
  --env "SNMPSIM_METRICS_CONFIG=/etc/snmpsim/snmpsim-metrics.conf" \
  --access-logfile /var/log/snmpsim/metrics-access.log \
  --error-logfile /var/log/snmpsim/metrics-error.log  \
  --daemon \
  snmpsim_control_plane.wsgi.metrics:app

```

## Infrastructure Daemons

Now you have to bring up the process supervision and metrics importer daemons

This command will bring you the supervision daemon process up

```
snmpsim-mgmt-supervisor \
  --watch-dir /var/snmpsim/supervised \
  --daemonize \
  --pid-file /var/run/snmpsim/supervisor.pid \
  --logging-method file:/var/log/snmpsim/supervisor.log \
  --reporting-method jsondoc:/var/log/snmpsim/metrics
```

And the following command will bring you up the metrics importer daemon

```
snmpsim-metrics-importer \
  --config /etc/snmpsim/snmpsim-metrics.conf \
  --watch-dir /var/log/snmpsim/metrics \
  --daemonize \
  --pid-file /var/log/snmpsim/importer.pid \
  --logging-method file:/var/log/snmpsim/importer.log
```

Its recommended to configure these commands within a systemd unit files or something like that

After setting up this point, you should be able to run REST-API calls against the Management and Metrics API endpoints.

## Calling REST-APIs

Now that you configured the snmpsim-control-plane, you could try uploading a simulation record

````
cat > /tmp/public.snmprec <<EOF
````

Add these lines to the file:

```
1.3.6.1.2.1.1.1.0|4|Linux zeus 4.8.6.5-smp #2 SMP Sun Nov 13 14:58:11 CDT 2016 i686
1.3.6.1.2.1.1.2.0|6|1.3.6.1.4.1.8072.3.2.10
1.3.6.1.2.1.1.3.0|67|123999999
1.3.6.1.2.1.1.4.0|4|SNMP Laboratories, info@snmplabs.com
1.3.6.1.2.1.1.5.0|4|zeus.snmplabs.com
1.3.6.1.2.1.1.6.0|4|San Francisco, California, United States
1.3.6.1.2.1.1.7.0|2|72
1.3.6.1.2.1.1.8.0|67|123999999
EOF
```

Now with the following command you could upload this snmprecording with the configured API endpoint

```
curl -s -d "@/tmp/public.snmprec" \
  -H "Content-Type: text/plain" \
  -X POST \
  http://127.0.0.1:5000/snmpsim/mgmt/v1/recordings/public.snmprec
```



Just try it out, if anything is unclear, just open an issue or if you got any enhancement, open an PR on this repo. :D

