from sklearn.linear_model import LinearRegression
from sklearn.model_selection import KFold
from sklearn.metrics import r2_score
import pickle
from statistics import mean


def main():
    features = pickle.load(open('prediction_features_ds.dat', 'rb'))

    X = features[:,:-1]
    y = features[:,-1]

    kf = KFold(n_splits=10)
    r2_coeff = []
    for train_id, test_id in kf.split(X):
        X_train, X_test = X[train_id], X[test_id]
        y_train, y_test = y[train_id], y[test_id]

        model = LinearRegression().fit(X_train, y_train)

        r2_pred = r2_score(y_test, model.predict(X_test))

        # The 2nd feature of the dataset is the number of points in the last season
        r2_baseline = r2_score(y_test, X_test[:, 2])

        r2_coeff.append((r2_pred, r2_baseline))

    print("Prediction R2: " + str(mean([x[0] for x in r2_coeff])))
    print("Baseline R2: " + str(mean([x[1] for x in r2_coeff])))


if __name__ == '__main__':
    main()