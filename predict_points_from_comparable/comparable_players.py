import pandas
from pathlib import Path
from typing import Union, Sequence, Dict
from predict_points_from_comparable.prepare_dataframe import extract_features
from sklearn.neighbors import NearestNeighbors
from operator import itemgetter
from dataclasses import dataclass
import progressbar
import numpy as np

@dataclass
class ComparablePlayer:
    name:str
    seasons_range:Sequence[str]

def create_dataframe_from_csv(stat_path: Union[Path, str]) -> pandas.DataFrame:
    data = pandas.read_csv(str(stat_path), header=0, encoding='unicode_escape')
    data = data.set_index('Player')

    # By doing this, we eliminate players with the same names, but deleting only the one with the less points.
    # TODO : Change this when using player_id
    data = data[data.index.duplicated() == False]

    return data

def create_dataframes_from_csv(csv_path: Union[Path, str], last_finished_season: str) \
        -> Sequence[pandas.DataFrame]:
    """

    :param csv_path:
    :param last_finished_season:
    :return:
    """

    stats_per_year_ordered = sorted(Path(csv_path).glob('*.csv'),
                                    key=lambda x: int(x.stem.split('-')[0]))
    stats_per_year_dfs = []

    for stat_path in stats_per_year_ordered:
        if stat_path.stem == last_finished_season:
            break

        data = create_dataframe_from_csv(stat_path)
        stats_per_year_dfs.append(data)

    return stats_per_year_dfs


def _create_features_per_player_from_yearly_statistics(yearly_statistics: Sequence[pandas.DataFrame]) \
        -> pandas.DataFrame:
    """

    :param yearly_statistics:
    :return:
    """

    sequence = yearly_statistics[0]
    features_sequence = extract_features(sequence).add_suffix(f'-{sequence["Season"][0]}')

    # Extract features and aggregate them based on the player name
    # TODO : Using the player_id from NHL's API would be a good thing to avoid the double Sebastian Aho problem would be a good thing
    for next_sequences_idx in range(1, len(yearly_statistics)):
        next_sequence = yearly_statistics[next_sequences_idx]
        prepared_next_seq = extract_features(next_sequence).add_suffix(f'-{next_sequence["Season"][0]}')

        features_sequence = features_sequence.join(prepared_next_seq, how='outer', sort=True).fillna(0)

    # Aggregate features that exist in many seasons but shouldn't
    is_forward = features_sequence.filter(regex='Forward*').aggregate('max', 1).astype(int)
    features_sequence.drop(list(features_sequence.filter(regex='Forward*')), axis=1, inplace=True)

    avg_shot_perc = features_sequence.filter(regex='S/GP*').aggregate('mean', 1).astype(int)
    features_sequence.drop(list(features_sequence.filter(regex='S/GP*')), axis=1, inplace=True)

    features_sequence["Forward"] = is_forward
    features_sequence["S/GP"] = avg_shot_perc

    return features_sequence


def create_n_years_sequences_of_player_features(yearly_statistics: Sequence[pandas.DataFrame],
                                                 n_years: int=3) \
        -> Sequence[pandas.DataFrame]:
    """

    :param yearly_statistics:
    :param n_years:
    :return:
    """

    n_years_sequences = []

    for i in range(0, len(yearly_statistics) - n_years + 1):
        n_years_sequences.append(_create_features_per_player_from_yearly_statistics(yearly_statistics[i:i + n_years]))

    return n_years_sequences


def create_nearest_neighbors_for_n_years_stats_sequences(n_years_sequences: Sequence[pandas.DataFrame],
                                                          n_nearest_neighbors: int=3) \
        -> Sequence[NearestNeighbors]:
    """

    :param n_years_sequences:
    :param n_nearest_neighbors:
    :return:
    """

    # Removing the last sequence because we'll need to look past the found sequence neighbor to see future stats.
    nn_per_sequence = [NearestNeighbors(n_neighbors=n_nearest_neighbors, algorithm='ball_tree')
                           .fit(seq.values) for seq in n_years_sequences[:-1]]

    return nn_per_sequence

def find_comparables_from_last_sequence(nearest_neighbors : Sequence[NearestNeighbors],
                                        n_years_sequences : Sequence[pandas.DataFrame],
                                        seasons_names_ordered : Sequence[str],
                                        searched_player_stats_over_last_n_years: Union[pandas.DataFrame, pandas.Series]) \
        -> Sequence[ComparablePlayer]:
    """

    :param nearest_neighbors:
    :param n_years_sequences:
    :param seasons_names_ordered:
    :param searched_player_stats_over_last_n_years:
    :return:
    """
    neighbors = []
    n_neighbors:int = -1

    for seq_id, nn in enumerate(nearest_neighbors):
        dist, idx = nn.kneighbors([searched_player_stats_over_last_n_years.values])
        n_neighbors = len(dist[0])
        neighbors += list(zip(dist[0], idx[0], [seq_id]*n_neighbors))

    neighbors_raw = list(sorted(neighbors, key=itemgetter(0)))[:n_neighbors]

    closest_comparables = []
    for dist, player_id, sequence_id in neighbors_raw:
        player_name = n_years_sequences[sequence_id].iloc[player_id].name
        season_range = seasons_names_ordered[sequence_id:sequence_id+n_neighbors]

        closest_comparables.append(ComparablePlayer(player_name, season_range))

    return closest_comparables

def get_comparables_for_all_players_in_last_n_years(yearly_statistics: Sequence[pandas.DataFrame],
                                                    seasons_name_ordered: Sequence[str],
                                                    n_neighbors:int = 3,
                                                    n_years:int = 3,
                                                    add_progressbar:bool = False)\
        -> Dict[str, Sequence[ComparablePlayer]]:

    players_features_aggregated_over_n_years_sequences = create_n_years_sequences_of_player_features(yearly_statistics, n_years)
    nearest_neighbors_per_sequence = create_nearest_neighbors_for_n_years_stats_sequences(players_features_aggregated_over_n_years_sequences, n_neighbors)

    comparables_per_player = {}
    if add_progressbar:
        pg = progressbar.ProgressBar(max_value=len(players_features_aggregated_over_n_years_sequences[-1]))

    for i, (player_name, player_stats_from_last_sequence) in enumerate(players_features_aggregated_over_n_years_sequences[-1].iterrows()):
        comparables = find_comparables_from_last_sequence(nearest_neighbors_per_sequence,
                                            players_features_aggregated_over_n_years_sequences,
                                            seasons_name_ordered,
                                            player_stats_from_last_sequence)

        comparables_per_player[str(player_name)] = comparables

        if add_progressbar:
            pg.update(i)

    if add_progressbar:
        pg.finish()

    return comparables_per_player


def _maybe_extract_pgp_from_df(df, name):
    result = 0.0
    try:
        result = df.loc[name]["P/GP"].astype(float)
    except KeyError:
        pass

    return result


def build_pgp_prediction_features_from_comparables(comparables_per_player : Dict[str, Sequence[ComparablePlayer]],
                                                   stats_per_season: Dict[str, pandas.DataFrame],
                                                   observed_seasons_for_prediction_ordered: Sequence[str],
                                                   last_finished_season : pandas.DataFrame)\
        -> np.ndarray:

    features_set = []

    for name, comparables in comparables_per_player.items():
        features_for_player = []

        for observed_season in observed_seasons_for_prediction_ordered:
            features_for_player.append(_maybe_extract_pgp_from_df(stats_per_season[observed_season], name))

        for comparable in comparables:
            for season in comparable.seasons_range:
                features_for_player.append(_maybe_extract_pgp_from_df(stats_per_season[season], comparable.name))

            last_observed_season_first_year = int(comparable.seasons_range[-1].split('-')[0])
            next_season = f'{last_observed_season_first_year+1}-{str(last_observed_season_first_year+2)[-2:]}'

            features_for_player.append(_maybe_extract_pgp_from_df(stats_per_season[next_season], comparable.name))

        features_for_player.append(_maybe_extract_pgp_from_df(last_finished_season, name))

        features_set.append(features_for_player)

    for i,f in enumerate(features_set):
        if not len(f) == 16:
            raise Exception()

        if len(list(filter(lambda x: not isinstance(x, float), f))) > 0:
            raise Exception

    return np.array(features_set, np.float32)


def main():
    import pickle

    stats_path = Path('D:/Repositories/nhl-statistics/statistics')

    # TODO : Retirer les joueurs doublons.

    yearly_stats = create_dataframes_from_csv(stats_path, '2020-2021')
    seasons_names_ordered = sorted([x["Season"][0] for x in yearly_stats],
                                   key=lambda x: int(x.split('-')[0]))

    comparables_per_player = get_comparables_for_all_players_in_last_n_years(yearly_stats, seasons_names_ordered, 3, 3, add_progressbar=True)

    stats_per_season = {x[0]:x[1] for x in zip(seasons_names_ordered, yearly_stats)}

    observed_seasons = ['2017-18','2018-19','2019-20']

    last_finished_season = create_dataframe_from_csv(str(stats_path / '2020-2021.csv'))

    prediction_features_ds = build_pgp_prediction_features_from_comparables(comparables_per_player,
                                                                            stats_per_season,
                                                                            observed_seasons,
                                                                            last_finished_season)

    with open('prediction_features_ds.dat', 'wb') as fs:
        pickle.dump(prediction_features_ds, fs, protocol=pickle.HIGHEST_PROTOCOL)

if __name__ == '__main__':
    main()
