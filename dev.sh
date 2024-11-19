#!/bin/bash

gunicorn app:app --certfile=/etc/letsencrypt/live/mooindagcounter.nl/cert.pem --keyfile=/etc/letsencrypt/live/mooindagcounter.nl/privkey.pem --bind 0.0.0.0:$1
