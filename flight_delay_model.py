"""Flight delay probability model.

This module computes the probability that a flight will be delayed by more
than 15 minutes (`DepDel15 == 1`) for a given day and airport pair, using
the historical data in `data/flights_cleaned.csv`.

The model is a simple empirical estimator: for every combination of
(Year, Month, DayofMonth, OriginAirportID, DestAirportID) we compute the
historical average of `DepDel15`. That average is the probability a flight
on that specific day and route is delayed by more than 15 minutes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "data" / "flights_cleaned.csv"

# Columns used to identify a unique "flight context".
GROUP_KEYS = ["Year", "Month", "DayofMonth", "OriginAirportID", "DestAirportID"]
TARGET_COLUMN = "DepDel15"


class FlightDelayModel:
    """Empirical flight delay probability model."""

    def __init__(self, data_path: str | Path = DEFAULT_DATA_PATH) -> None:
        self.data_path = Path(data_path)
        self._probabilities: Optional[pd.DataFrame] = None
        self._lookup: Optional[pd.DataFrame] = None

    def load_data(self) -> pd.DataFrame:
        """Load the cleaned flights CSV into a DataFrame."""
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")
        df = pd.read_csv(self.data_path)
        # Ensure the target column is numeric (0/1). Some rows may have NaNs
        # in `DepDel15` when the flight was cancelled; treat those as 0.
        df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce").fillna(0)
        return df

    def fit(self) -> pd.DataFrame:
        """Group the data and compute the delay probability per group."""
        df = self.load_data()
        grouped = (
            df.groupby(GROUP_KEYS, as_index=False)[TARGET_COLUMN]
            .mean()
            .rename(columns={TARGET_COLUMN: "DelayProbability"})
        )
        counts = (
            df.groupby(GROUP_KEYS, as_index=False)
            .size()
            .rename(columns={"size": "FlightCount"})
        )
        grouped = grouped.merge(counts, on=GROUP_KEYS)
        self._probabilities = grouped
        # Build an indexed lookup for fast querying.
        self._lookup = grouped.set_index(GROUP_KEYS)
        return grouped

    def get_delay_probability(
        self,
        year: int,
        month: int,
        day: int,
        origin_airport_id: int,
        dest_airport_id: int,
    ) -> float:
        """Return the probability of a >15 minute delay for the given flight.

        Args:
            year: Year of the flight (e.g. 2013).
            month: Month of the flight (1-12).
            day: Day of the month (1-31).
            origin_airport_id: Origin airport ID (from OriginAirportID column).
            dest_airport_id: Destination airport ID (from DestAirportID column).

        Returns:
            A probability in [0.0, 1.0]. Returns 0.0 if no historical data is
            available for the requested combination.
        """
        if self._lookup is None:
            self.fit()
        assert self._lookup is not None  # for type checkers
        try:
            row = self._lookup.loc[
                (year, month, day, origin_airport_id, dest_airport_id)
            ]
            if isinstance(row, pd.DataFrame):
                # Multiple rows matched (shouldn't happen with our keys); average.
                return float(row["DelayProbability"].mean())
            return float(row["DelayProbability"])
        except KeyError:
            return 0.0

    def get_flight_count(
        self,
        year: int,
        month: int,
        day: int,
        origin_airport_id: int,
        dest_airport_id: int,
    ) -> int:
        """Return the number of historical flights available for the given group."""
        if self._lookup is None:
            self.fit()
        assert self._lookup is not None
        try:
            row = self._lookup.loc[
                (year, month, day, origin_airport_id, dest_airport_id)
            ]
            if isinstance(row, pd.DataFrame):
                return int(row["FlightCount"].sum())
            return int(row["FlightCount"])
        except KeyError:
            return 0
            
    def add_date_column(self) -> pd.DataFrame:
        """Adds a formatted 'DateStr' column (MM/DD/YYYY) to the probability DataFrame."""
        if self._probabilities is None:
            raise ValueError("Model must be fitted before adding columns.")
        
        # Create the string using vectorized pandas operations for speed
        self._probabilities["DateStr"] = (
            self._probabilities["Month"].astype(str).str.zfill(2) + "/" +
            self._probabilities["DayofMonth"].astype(str).str.zfill(2) + "/" +
            self._probabilities["Year"].astype(str)
        )
        return self._probabilities


def _demo() -> None:
    model = FlightDelayModel()
    model.fit()
    print(f"Loaded {len(model._probabilities):,} unique flight-context groups.")

    # Use the first row of the dataset as a sanity check.
    sample = pd.read_csv(DEFAULT_DATA_PATH, nrows=1)
    y, m, d = int(sample["Year"][0]), int(sample["Month"][0]), int(sample["DayofMonth"][0])
    o = int(sample["OriginAirportID"][0])
    d2 = int(sample["DestAirportID"][0])
    p = model.get_delay_probability(y, m, d, o, d2)
    n = model.get_flight_count(y, m, d, o, d2)
    print(
        f"Sample query: {y}-{m:02d}-{d:02d} {o} -> {d2} | "
        f"prob={p:.3f} (n={n})"
    )


if __name__ == "__main__":
    _demo()