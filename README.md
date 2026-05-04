# Mooindagcounter

Een simpele teller-app gebouwd met Flask.

## Deployment varianten

| Map | Beschrijving |
|---|---|
| [`bunny/`](bunny/) | Bunny.net deployment met **Magic Containers** (app) + **Bunny Database** (managed) + optioneel Edge Script |
| [`self-hosted/`](self-hosted/) | Zelf hosten met Docker Compose (app + MariaDB) |

## Belangrijk onderscheid

- Het GHCR package `ghcr.io/stensel8/mooindagcounter` is een **kant-en-klare app image** voor Magic Containers.
- De database zit **niet** in die image. Die koppel je apart (standaard: Bunny Database).
- Wil je app + database als twee samenwerkende containers draaien, gebruik dan de `self-hosted/` variant of maak zelf een multi-container setup in Bunny.

Zie de README in elke map voor de concrete stappen.
