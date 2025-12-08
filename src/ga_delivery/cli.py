"""Command-line interface to run GA delivery route optimization."""

from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from .data import DEFAULT_POINTS, Point, build_distance_matrix
from .genetic import GAConfig, GeneticRouteOptimizer
from .visualization import plot_history, plot_route


def _generate_points(count: int, seed: int | None) -> List[Point]:
    rng = random.Random(seed)
    # Keep coordinates within a 0-10 grid for easy visualization.
    return [(rng.uniform(0, 10), rng.uniform(0, 10)) for _ in range(count)]


def _default_csv_path() -> Path | None:
    """Return bundled sample CSV path if it exists."""
    candidate = Path(__file__).resolve().parents[2] / "data" / "polska_trasa.csv"
    return candidate if candidate.exists() else None


def _load_points_from_csv(path: Path) -> List[Point]:
    points: List[Point] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            x, y = float(row[0]), float(row[1])
            points.append((x, y))
    if not points:
        raise ValueError("Brak punktów w pliku CSV.")
    return points


def _try_load_csv(path_str: str) -> List[Point] | None:
    path_str = path_str.strip()
    if not path_str:
        print("Nie podano ścieżki. Wróć do menu.")
        return None
    path = Path(path_str)
    if not path.exists():
        print(f"Plik nie istnieje: {path}")
        return None
    if not path.is_file():
        print(f"Ścieżka nie jest plikiem: {path}")
        return None
    try:
        return _load_points_from_csv(path)
    except PermissionError:
        print(f"Brak uprawnień do odczytu pliku: {path}")
    except ValueError as exc:
        print(f"Błąd danych CSV: {exc}")
    except Exception as exc:  # noqa: BLE001
        print(f"Nie udało się wczytać CSV ({exc}).")
    return None


def _export_history(path: Path, best: Sequence[float], avg: Sequence[float]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["generation", "best_distance", "avg_distance"])
        for gen, (b, a) in enumerate(zip(best, avg)):
            writer.writerow([gen, b, a])


def _export_route_json(path: Path, route: Iterable[int], distance: float) -> None:
    data = {
        "best_route": list(route),
        "distance": distance,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _save_points_csv(path: Path, points: Sequence[Point]) -> None:
    """Zapisz punkty (wraz z depo) do CSV: jedna linia = x,y."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for x, y in points:
            writer.writerow([x, y])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optymalizacja trasy dostaw przy użyciu algorytmu genetycznego.",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Uruchom tryb interaktywny (menu: losuj, ręcznie, CSV, domyślne).",
    )
    parser.add_argument(
        "--population",
        type=int,
        default=None,
        help="Rozmiar populacji (domyślnie dobierany dynamicznie do liczby punktów).",
    )
    parser.add_argument("--elite", type=int, default=2, help="Liczba osobników elitarnych.")
    parser.add_argument(
        "--mutation",
        type=float,
        default=0.05,
        help="Prawdopodobieństwo mutacji (0-1).",
    )
    parser.add_argument(
        "--generations", type=int, default=400, help="Liczba pokoleń do ewolucji."
    )
    parser.add_argument(
        "--tournament",
        type=int,
        default=5,
        help="Rozmiar turnieju przy selekcji.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Ziarno RNG dla powtarzalności.",
    )
    parser.add_argument(
        "--random-points",
        type=int,
        default=0,
        help="Jeśli >0, generuje losowy zestaw punktów (bez depo).",
    )
    parser.add_argument(
        "--points-file",
        type=str,
        default=None,
        help="Ścieżka do CSV z punktami (x,y w wierszu). Jeśli podasz, nadpisze domyślne punkty.",
    )
    parser.add_argument(
        "--generate-csv",
        type=str,
        default=None,
        help="Wygeneruj losowy zestaw punktów (z depo) i zapisz do CSV podaną ścieżkę, potem zakończ.",
    )
    parser.add_argument(
        "--generate-count",
        type=int,
        default=10,
        help="Liczba punktów (bez depo) do wygenerowania przy --generate-csv.",
    )
    parser.add_argument(
        "--plot/--no-plot",
        dest="plot",
        default=True,
        help="Pokazuje wykres najlepszej trasy.",
    )
    parser.add_argument(
        "--history/--no-history",
        dest="plot_history",
        default=True,
        help="Pokazuje wykres postępu GA.",
    )
    parser.add_argument(
        "--save-route",
        type=str,
        default=None,
        help="Ścieżka do zapisania wykresu trasy (PNG).",
    )
    parser.add_argument(
        "--save-history",
        type=str,
        default=None,
        help="Ścieżka do zapisania wykresu postępu (PNG).",
    )
    parser.add_argument(
        "--export-history",
        type=str,
        default=None,
        help="Eksport historii (best/avg) do CSV.",
    )
    parser.add_argument(
        "--export-route",
        type=str,
        default=None,
        help="Eksport najlepszej trasy do pliku JSON.",
    )
    return parser.parse_args()


def _prompt_menu() -> str:
    print("\nWybierz sposób wczytania punktów:")
    print("1) Losuj punkty")
    print("2) Wpisz ręcznie")
    print("3) Wczytaj z CSV")
    print("4) Użyj domyślnych")
    print("5) Zamknij")
    while True:
        choice = input("Twój wybór (1-5): ").strip()
        if choice in {"1", "2", "3", "4", "5"}:
            return choice
        print("Podaj 1, 2, 3, 4 lub 5.")


def _prompt_int(prompt: str, min_value: int = 1, max_value: int | None = None) -> int:
    while True:
        try:
            value = int(input(prompt).strip())
            if value < min_value:
                raise ValueError
            if max_value is not None and value > max_value:
                raise ValueError
            return value
        except ValueError:
            print(f"Podaj liczbę całkowitą z zakresu {min_value}-{max_value or '∞'}.")


def _prompt_points_manual() -> List[Point]:
    points: List[Point] = [(0.0, 0.0)]  # depot
    n = _prompt_int("Ile punktów (bez depo) chcesz dodać? ", min_value=1)
    for i in range(1, n + 1):
        while True:
            raw = input(f"Punkt {i} (format x,y): ").strip()
            try:
                x_str, y_str = raw.split(",")
                x, y = float(x_str), float(y_str)
                points.append((x, y))
                break
            except Exception:
                print("Niepoprawny format, spróbuj ponownie (np. 3.5,7).")
    return points


def main() -> None:
    args = parse_args()

    # Tryb: generuj CSV i zakończ.
    if args.generate_csv:
        count = args.generate_count if args.generate_count > 0 else 1
        points = [(0.0, 0.0)] + _generate_points(count, args.seed)
        out_path = Path(args.generate_csv)
        _save_points_csv(out_path, points)
        print(f"Wygenerowano CSV: {out_path} (depo + {count} punktów).")
        print(f"Użyj go flagą: --points-file \"{out_path}\"")
        return

    if args.interactive:
        print("Tryb interaktywny: wybierz 1-5. Program zakończy się po wybraniu 5 (Zamknij).")
        while True:
            choice = _prompt_menu()
            if choice == "5":
                print("Zamykam.")
                return

            if choice == "1":
                count = _prompt_int("Ile punktów (bez depo) wylosować? ", min_value=1)
                points = [(0.0, 0.0)] + _generate_points(count, args.seed)
            elif choice == "2":
                points = _prompt_points_manual()
            elif choice == "3":
                sample_csv = _default_csv_path()
                if sample_csv:
                    print(f"Nacisnij ENTER aby wczytac domyslny plik: {sample_csv}")
                path_str = input("Sciezka do pliku CSV: ").strip()
                if not path_str and sample_csv:
                    path_str = str(sample_csv)
                loaded = _try_load_csv(path_str)
                if not loaded:
                    continue
                points = loaded
            else:
                points = DEFAULT_POINTS

            _run_ga(points, args)
    else:
        points: List[Point]
        if args.points_file:
            points = _load_points_from_csv(Path(args.points_file))
        elif args.random_points and args.random_points > 0:
            # +1 to include depot at index 0
            points = [(0.0, 0.0)] + _generate_points(args.random_points, args.seed)
        else:
            points = DEFAULT_POINTS
        _run_ga(points, args)


def _run_ga(points: List[Point], args: argparse.Namespace) -> None:
    """Uruchom GA dla podanych punktów z parametrami z args."""

    config = GAConfig(
        population_size=args.population,
        elite_size=args.elite,
        mutation_rate=args.mutation,
        generations=args.generations,
        tournament_size=args.tournament,
        seed=args.seed,
    )

    distance_matrix = build_distance_matrix(points)
    optimizer = GeneticRouteOptimizer(distance_matrix, config)
    result = optimizer.run()

    route_str = " -> ".join(["Depot"] + [f"P{idx}" for idx in result.best_route] + ["Depot"])
    print(f"Najlepsza trasa: {route_str}")
    print(f"Długość trasy: {result.best_distance:.2f}")
    print(f"Średnia z ostatniej populacji: {result.avg_per_generation[-1]:.2f}")

    if args.plot:
        plot_route(points, result.best_route, result.best_distance, save_path=args.save_route)
    if args.plot_history:
        plot_history(
            result.best_per_generation,
            result.avg_per_generation,
            save_path=args.save_history,
        )
    if args.export_history:
        _export_history(Path(args.export_history), result.best_per_generation, result.avg_per_generation)
        print(f"Zapisano historię do: {args.export_history}")
    if args.export_route:
        _export_route_json(Path(args.export_route), result.best_route, result.best_distance)
        print(f"Zapisano trasę do: {args.export_route}")


if __name__ == "__main__":
    main()
