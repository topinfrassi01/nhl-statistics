import pandas
from typing import Tuple, Dict, Union
from data_preparation.prepare_data_knn import prepare
from sklearn.neighbors import NearestNeighbors
from pathlib import Path
from operator import itemgetter


class ClosestComparableFinder:
    def __init__(self, csv_path: Union[Path, str], k=5):
        self.k = k

        self.prepared_datasets: Dict[str, pandas.DataFrame] = {}
        self.datasets: Dict[str, pandas.DataFrame] = {}
        self.nn_indices: Dict[str, NearestNeighbors] = {}

        for csv_file in Path(csv_path).glob('*.csv'):
            df = pandas.read_csv(str(csv_file), header=0, encoding='unicode_escape')
            df = df.set_index('Player')
            prepared_df = prepare(df)

            self.prepared_datasets[csv_file.stem] = prepared_df
            self.datasets[csv_file.stem] = df
            self.nn_indices[csv_file.stem] = NearestNeighbors(n_neighbors=self.k, algorithm='ball_tree').fit(prepared_df)

    def get_closest_players(self, observed_season: str, observed_player_name: str) \
            -> Tuple[pandas.DataFrame, pandas.DataFrame]:

        observed_player = self.datasets[observed_season].loc[observed_player_name]
        observed_player_prepared = self.prepared_datasets[observed_season].loc[observed_player_name]
        nearest_neighbors = []

        for season, nn in self.nn_indices.items():
            if season == observed_season:
                continue

            distances, indices = nn.kneighbors([observed_player_prepared])
            nearest_neighbors += list(zip([season] * 5, distances[0], indices[0]))

        top = list(sorted(nearest_neighbors, key=itemgetter(1)))[:self.k]

        results = list()
        for season, dist, idx in top:
            results.append(self.datasets[season].loc[self.prepared_datasets[season].index[idx]])

        return pandas.DataFrame([observed_player]), pandas.DataFrame(results)
