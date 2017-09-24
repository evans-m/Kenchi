import numpy as np
from sklearn.base import BaseEstimator
from sklearn.neighbors import NearestNeighbors
from sklearn.utils.validation import check_array, check_is_fitted

from ..base import DetectorMixin
from ..utils import assign_info_on_pandas_obj, construct_pandas_obj


class EmpiricalOutlierDetector(BaseEstimator, DetectorMixin):
    """Outlier detector using the k-nearest neighbors algorithm.

    Parameters
    ----------
    fpr : float, default 0.01
        False positive rate. Used to compute the threshold.

    n_jobs : integer, default 1
        Number of jobs to run in parallel. If -1, then the number of jobs is
        set to the number of CPU cores. Doesn't affect fit method.

    n_neighbors : integer, default 5
        Number of neighbors.

    p : integer, default 2
        Power parameter for the Minkowski metric.

    Attributes
    ----------
    threshold_ : float
        Threshold.
    """

    def __init__(self, fpr=0.01, n_jobs=1, n_neighbors=5, p=2):
        self.fpr         = fpr
        self.n_jobs      = n_jobs
        self.n_neighbors = n_neighbors
        self.p           = p

    @assign_info_on_pandas_obj
    def fit(self, X, y=None):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Samples.

        Returns
        -------
        self : detector
            Return self.
        """

        X               = check_array(X)

        self._neigh     = NearestNeighbors(
            metric      = 'minkowski',
            n_jobs      = self.n_jobs,
            n_neighbors = self.n_neighbors,
            p           = self.p
        ).fit(X)

        scores          = self.anomaly_score(X)
        self.threshold_ = np.percentile(scores, 100.0 * (1.0 - self.fpr))

        return self

    @construct_pandas_obj
    def anomaly_score(self, X, y=None):
        """Compute anomaly scores for test samples.

        Parameters
        ----------
        X : array-like, shape = (n_samples, n_features)
            Test samples.

        Returns
        -------
        scores : array-like, shape = (n_samples,)
            anomaly scores for test samples.
        """

        check_is_fitted(self, '_neigh')

        X             = check_array(X)
        _, n_features = X.shape

        dist, _       = self._neigh.kneighbors(X)
        radius        = np.max(dist, axis=1)

        return -np.log(self.n_neighbors) + n_features * np.log(radius)
