# Delivery Optimization Using Genetic Algorithm

Algorytm genetyczny optymalizujący trasę dostaw (problem TSP) dla kuriera lub dronów. Trasę kodujemy jako permutację punktów (depo = 0), populacja ewoluuje przez selekcję turniejową, krzyżowanie OX i mutację zamiany.

## Struktura
- `src/ga_delivery/data.py` – przykładowe punkty i macierz odległości.
- `src/ga_delivery/genetic.py` – konfiguracja GA i implementacja algorytmu.
- `src/ga_delivery/visualization.py` – wykres trasy i postępu algorytmu.
- `src/ga_delivery/cli.py` – skrypt CLI do eksperymentów i wizualizacji.
- `requirements.txt` – zależności (matplotlib).

## Uruchomienie
Wymagany Python 3.11+.

```bash
python -m venv .venv
.\.venv\Scripts\activate        # Windows
# source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
set PYTHONPATH=src              # Windows (dla Pythona uruchamianego z repo)
# export PYTHONPATH=src         # macOS/Linux
python -m ga_delivery.cli --help
python main.py                  # automatycznie uruchamia tryb interaktywny (menu)
```

Przykłady:
```bash
# Domyślne dane (12 punktów + depo), z wykresami
python -m ga_delivery.cli

# Większa populacja i mutacja, zapis wykresów do plików
python -m ga_delivery.cli --population 150 --generations 500 --mutation 0.08 --save-route best.png --save-history history.png

# Losowe punkty (np. 15 lokalizacji + depo), bez wyświetlania wykresów
python -m ga_delivery.cli --random-points 15 --no-plot --no-history

# Własne punkty z CSV (x,y w wierszu), eksporty do CSV/JSON
python -m ga_delivery.cli --points-file dane.csv --export-history historia.csv --export-route best.json --no-plot

# Tryb interaktywny (menu: losuj / ręcznie / CSV / domyślne)
python -m ga_delivery.cli --interactive
# lub po prostu:
python main.py   # menu trwa do wyboru 5) Zamknij

# Wygeneruj przykładowy CSV z losowymi punktami i zakończ
python -m ga_delivery.cli --generate-csv sample_points.csv --generate-count 12
python -m ga_delivery.cli --points-file sample_points.csv   # użycie wygenerowanego pliku

# Przykładowa trasa miast (depo = Opole) w repo:
python -m ga_delivery.cli --points-file data/polska_trasa.csv
```

Parametry, którymi warto się pobawić:
- `--population` (rozmiar populacji),
- `--generations` (liczba pokoleń),
- `--mutation` (prawdopodobieństwo mutacji),
- `--tournament` (presja selekcji),
- `--elite` (liczba elit),
- `--random-points` (generuje własny zestaw punktów),
- `--points-file` (własne punkty z CSV),
- `--export-history` (CSV z best/avg per pokolenie),
- `--export-route` (JSON z najlepszą trasą i jej długością).
