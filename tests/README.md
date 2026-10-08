# Tests

Les dossiers suivent les modules de `app/api/` : `orders` pour `/orders`,
et `test_health.py` pour la route `/health` définie dans `main.py`.

```text
tests/
  unit/orders/
    test_orderbook.py   # Matching, FIFO, prix, reliquat et statuts
    test_service.py     # Lecture, création, trades et annulation
  http/orders/
    test_routes.py      # GET /orders, GET /orders/{id}, POST /orders
  http/test_health.py   # Health et remise à zéro au démarrage
```

Les préfixes `01`, `02`, `03` suivent l'ordre de déclaration des routes.
Les annulations sont testées uniquement au niveau du service, car il n'existe
pas encore de route d'annulation. Chaque test utilise un stockage neuf et ne
dépend pas du résultat d'un autre test. Les tests HTTP utilisent `TestClient`
avec le vrai service et le lifespan, sans serveur à lancer ni accès réseau.

Depuis la racine du projet :

```sh
# Toute la suite
.venv/bin/python -B -m unittest discover -s tests -t . -v

# Module orders : unitaires uniquement
.venv/bin/python -B -m unittest discover -s tests/unit/orders -t . -v

# Module orders : HTTP uniquement
.venv/bin/python -B -m unittest discover -s tests/http/orders -t . -v

# Tous les tests unitaires ou tous les tests HTTP
.venv/bin/python -B -m unittest discover -s tests/unit -t . -v
.venv/bin/python -B -m unittest discover -s tests/http -t . -v

# Une route ou un fichier précis
.venv/bin/python -B -m unittest tests.http.orders.test_routes.TestOrdersHTTP.test_02_get_order_unknown -v
.venv/bin/python -B -m unittest tests.http.test_health -v
```

Dépendances : FastAPI et httpx pour `TestClient`, déjà présents dans `.venv`.
Le runner `unittest` fait partie de Python ; pytest n'est pas nécessaire.

Deux tests HTTP sont marqués `expectedFailure` : les prix et quantités nuls
ou négatifs devraient retourner 422, mais sont actuellement acceptés.
Une fois la validation corrigée, retirer les décorateurs : unittest signalera
entre-temps un `unexpected success`, afin de ne pas oublier cette étape.
