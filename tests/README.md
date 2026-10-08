# Tests

Les dossiers reproduisent les modules de `app/api/`. Les préfixes numériques
suivent l'ordre de déclaration des routes dans chaque module. Chaque test
utilise un stockage neuf ; aucun test ne dépend d'un test précédent.

```text
tests/
  unit/
    orders/test_orderbook.py    # Matching, FIFO, limites, reliquat, statuts
    orders/test_service.py      # Lecture, création et annulation des ordres
    trades/test_service.py      # Lecture et erreurs métier des trades
    orderbook/test_service.py   # Carnet partagé et mises à jour
    test_health.py             # Réponse de health
  http/
    orders/test_routes.py      # GET liste, GET détail, POST, PATCH annulation
    trades/test_routes.py      # GET liste, GET détail
    orderbook/test_routes.py   # GET carnet
    test_health.py             # GET health et isolation du lifespan
```

Les tests HTTP utilisent `TestClient`, le vrai lifespan et les vrais services.
Aucun serveur à lancer ni connexion réseau n'est nécessaire. Les scénarios
vérifient le stockage partagé entre routes, les erreurs 404/409/422, les prix
et quantités décimaux, les exécutions partielles et complètes et les annulations.
Les tests unitaires vérifient directement les services et le moteur de matching.

Depuis la racine du projet :

```sh
# Toute la suite
.venv/bin/python -B -m unittest discover -s tests -t . -v

# Unitaires ou HTTP uniquement
.venv/bin/python -B -m unittest discover -s tests/unit -t . -v
.venv/bin/python -B -m unittest discover -s tests/http -t . -v

# Module orders (remplacer par trades ou orderbook pour les autres modules)
.venv/bin/python -B -m unittest discover -s tests/unit/orders -t . -v
.venv/bin/python -B -m unittest discover -s tests/http/orders -t . -v

# Un test précis
.venv/bin/python -B -m unittest tests.http.orders.test_routes.TestOrdersHTTP.test_04_cancel_unknown_order -v

# Health uniquement
.venv/bin/python -B -m unittest tests.unit.test_health tests.http.test_health -v
```

Dépendances : FastAPI et httpx pour `TestClient`, déjà présents dans `.venv`.
Le runner `unittest` fait partie de Python ; pytest n'est pas nécessaire.
Tous les tests sont actifs, sans `expectedFailure` ni tests ignorés.
