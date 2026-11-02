# Multiportal24 — publiczny katalog routingu

To repozytorium jest jedynym katalogiem publicznych tras aplikacji
Multiportal24. Zmiany trafiają przez Pull Request i są automatycznie
walidowane przed zatwierdzeniem przez operatora.

## Zgłoszenie trasy

Edytuj wyłącznie `catalog/apps.yml`. Każdy wpis zawiera:

```yaml
version: 1
applications:
  - domain: crm.apps.multi.bofh.pm
    namespace: bofh
    service: crm-web
    port: 8080
    health_path: /healthz
```

Wymagane pola:

- `domain` — publiczna nazwa aplikacji;
- `namespace` — namespace Kubernetes;
- `service` — stabilna nazwa Kubernetes Service;
- `port` — port Service, nie `containerPort`;
- `health_path` — opcjonalna ścieżka kontroli zdrowia; domyślnie `/`.

Nie wpisuj adresów podów, workerów, NodePortów ani fragmentów
konfiguracji proxy. Nie umieszczaj sekretów, tokenów, kubeconfigów,
certyfikatów ani kluczy.

## Praca przez fork i Pull Request

1. Utwórz fork repozytorium.
2. Załóż osobną gałąź dla zmiany.
3. Zmień `catalog/apps.yml` bez usuwania cudzych wpisów.
4. Uruchom testy lokalne.
5. Otwórz Pull Request do `main`.
6. Poczekaj na check `validate` i zatwierdzenie CODEOWNER.

Po merge zaufana automatyka operatorska pobiera wyłącznie zatwierdzony
`catalog/apps.yml`, ponownie go waliduje i publikuje routing. Kod z gałęzi PR
nie ma dostępu do infrastruktury ani sekretów.

## Walidacja lokalna

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests
python3 scripts/catalog.py catalog/apps.yml --output build
```

Repozytorium nie zawiera kompletnej konfiguracji infrastruktury. Zmiana
generatora w tym repo nie zmienia samodzielnie konfiguracji produkcyjnej.
