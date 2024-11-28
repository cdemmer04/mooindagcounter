# Mooindagcounter DB
Deze versie van de Mooindagcounter maakt gebruik van een MySQL Database die ervoor zorgt dat de counts, berichten en datums worden bijgehouden.

# Script voor development
#!/bin/bash
gunicorn app:app --certfile=/etc/letsencrypt/live/mooindagcounter.nl/cert.pem --keyfile=/etc/letsencrypt/live/mooindagcounter.nl/privkey.pem --bind 0.0.0.0:$1
