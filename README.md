# Multiportal24 — publiczny katalog routingu

To repozytorium jest jedynym katalogiem publicznych tras aplikacji
Multiportal24. Zmiany trafiają przez Pull Request i są automatycznie
walidowane. Bezpieczne dopisanie nowej trasy jest po pozytywnych testach
automatycznie scalane i wdrażane; nie trzeba zlecać tej operacji agentowi.

## Zgłoszenie trasy

Edytuj wyłącznie `catalog/apps.yml`. Każdy wpis zawiera:

```yaml
version: 1
applications:
  - domain: portal-demo.apps.multi.bofh.pm
    namespace: multiportale-dev
    service: portal-web
    port: 80
    health_path: /healthz
```

Wymagane pola:

- `domain` — publiczna nazwa aplikacji;
- `namespace` — namespace Kubernetes;
- `service` — stabilna nazwa Kubernetes Service;
- `port` — port Service; dla publicznego HTTP zawsze `80`;
- `health_path` — opcjonalna ścieżka kontroli zdrowia; domyślnie `/`.

Publiczny rekord A domeny musi zostać utworzony przed zgłoszeniem i wskazywać
na `188.68.243.210`. Automat jedynie sprawdza DNS; nie tworzy ani nie zmienia
rekordów.

Nie wpisuj adresów podów, workerów, NodePortów ani fragmentów
konfiguracji proxy. Nie umieszczaj sekretów, tokenów, kubeconfigów,
certyfikatów ani kluczy.

## Jak wskazywane są pody

Deweloper wdraża Deployment i selektorowy Service `ClusterIP` w tym samym
namespace. Etykiety podów muszą odpowiadać `spec.selector` Service. Przykład
znajduje się w `examples/application.yml`.

Service wystawia stabilny port `80`. Aplikacja w kontenerze może słuchać na
innym porcie; wtedy Service mapuje `port: 80` na odpowiedni `targetPort`.
Katalog zawsze podaje `port: 80`, czyli `Service.spec.ports[].port`, nigdy
`containerPort` ani `targetPort`.

Po merge automat tworzy Ingress z `ingressClassName: traefik`. Traefik odczytuje
Ingress, Service i gotowe EndpointSlices z API Kubernetes, dlatego katalog nie
zawiera adresów podów. Przed publikacją automat sprawdza istnienie namespace,
selektorowego Service `ClusterIP`, portu 80 i co najmniej jednego gotowego
endpointu. Brak któregokolwiek elementu zatrzymuje wdrożenie.

## Praca przez fork i Pull Request

1. Utwórz fork repozytorium.
2. Załóż osobną gałąź dla zmiany.
3. Zmień `catalog/apps.yml` bez usuwania cudzych wpisów.
4. Uruchom testy lokalne.
5. Otwórz Pull Request do `main`.
6. Poczekaj na check `validate` i automatyczny test działającego klastra.

Jeżeli PR tylko dopisuje nowe wpisy do `catalog/apps.yml`, automat potwierdza
rekord A, namespace, Service `ClusterIP` na porcie 80, gotowe endpointy oraz
brak konfliktu Ingress. Po pozytywnym wyniku sam scala PR. Następnie niezależny
automat operatorski pobiera wyłącznie zatwierdzony `catalog/apps.yml`, ponownie
go waliduje i publikuje Ingress oraz zgodną konfigurację obu HAProxy.

Usunięcie albo zmiana istniejącej trasy, modyfikacja innych plików oraz
nieudany test pozostają zatrzymane do ręcznej decyzji operatora. Kod z gałęzi
PR nigdy nie ma dostępu do infrastruktury ani sekretów.

## Walidacja lokalna

```bash
python3 -m pip install -r requirements.txt
python3 -m unittest discover -s tests
python3 scripts/catalog.py catalog/apps.yml --output build
```

Repozytorium nie zawiera kompletnej konfiguracji infrastruktury. Zmiana
generatora w tym repo nie zmienia samodzielnie konfiguracji produkcyjnej.
