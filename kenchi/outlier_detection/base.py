import time
from abc import abstractmethod, ABC

import numpy as np
from sklearn.base import BaseEstimator
from sklearn.externals.joblib import logger
from sklearn.preprocessing import MinMaxScaler
from sklearn.utils import check_array
from sklearn.utils.validation import check_is_fitted

from .visualization import plot_anomaly_score, plot_roc_curve

__all__ = ['is_outlier_detector', 'BaseOutlierDetector', 'OutlierMixin']


def is_outlier_detector(estimator):
    """Return True if the given estimator is (probably) an outlier detector.

    Parameters
    ----------
    estimator : object
        Estimator object to test.

    Returns
    -------
    out : bool
        True if estimator is an outlier detector and False otherwise.
    """

    return getattr(estimator, '_estimator_type', None) == 'outlier_detector'


class OutlierMixin:
    """Mixin class for all outlier detectors."""

    _estimator_type = 'outlier_detector'

    def fit_predict(self, X, y=None):
        """Fit the model according to the given training data and predict if a
        particular sample is an outlier or not.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training Data.

        y : ignored

        Returns
        -------
        y_pred : array-like of shape (n_samples,)
            Return 1 for inliers and -1 for outliers.
        """

        return self.fit(X).predict(X)


class BaseOutlierDetector(BaseEstimator, OutlierMixin, ABC):
    """Base class for all outlier detectors in kenchi.

    References
    ----------
    H.-P. Kriegel, P. Kroger, E. Schubert and A. Zimek,
    "Interpreting and unifying outlier scores,"
    In Proceedings of SDM'11, pp. 13-24, 2011.
    """

    # TODO: Implement score_samples method
    # TODO: Implement decision_function method

    @abstractmethod
    def __init__(self, contamination=0.1, verbose=False):
        self.contamination = contamination
        self.verbose       = verbose

    @abstractmethod
    def _fit(self, X):
        """Fit the model according to the given training data."""

    @abstractmethod
    def _anomaly_score(self, X):
        """Compute the anomaly score for each sample."""

    def _check_params(self):
        """Check validity of parameters and raise ValueError if not valid."""

        if not 0. <= self.contamination <= 0.5:
            raise ValueError(
                f'contamination must be between 0.0 and 0.5 inclusive '
                f'but was {self.contamination}'
            )

    def _get_threshold(self):
        """Define the threshold according to the given training data."""

        return np.percentile(
            self.anomaly_score_, 100. * (1. - self.contamination)
        )

    def fit(self, X, y=None):
        """Fit the model according to the given training data.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.

        y : ignored

        Returns
        -------
        self : object
            Return self.
        """

        self._check_params()

        X                   = check_array(X, estimator=self)

        start_time          = time.time()
        self._fit(X)
        self.fit_time_      = time.time() - start_time

        self.anomaly_score_ = self._anomaly_score(X)
        self.threshold_     = self._get_threshold()
        self._scaler        = MinMaxScaler(
        ).fit(self.anomaly_score_[:, np.newaxis])

        if getattr(self, 'verbose', False):
            print(f'elaplsed: {logger.short_format_time(self.fit_time_)}')

        return self

    def anomaly_score(self, X, normalize=False):
        """Compute the anomaly score for each sample.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data.

        normalize : bool, default False
            If True, return the normalized anomaly score.

        Returns
        -------
        anomaly_score : array-like of shape (n_samples,)
            Anomaly score for each sample.
        """

        check_is_fitted(self, '_scaler')

        X             = check_array(X, estimator=self)
        anomaly_score = self._anomaly_score(X)

        if normalize:
            return self._scaler.transform(anomaly_score[:, np.newaxis]).flat[:]
        else:
            return anomaly_score

    def predict(self, X, threshold=None):
        """Predict if a particular sample is an outlier or not.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data.

        threshold : float, default None
            User-provided threshold.

        Returns
        -------
        y_pred : array-like of shape (n_samples,)
            Return 1 for inliers and -1 for outliers.
        """

        anomaly_score = self.anomaly_score(X)

        if threshold is None:
            threshold = self.threshold_

        return np.where(anomaly_score <= threshold, 1, -1)

    def plot_anomaly_score(self, X, **kwargs):
        """Plot the anomaly score for each sample.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data.

        ax : matplotlib Axes, default None
            Target axes instance.

        bins : int, str or array-like, default 'auto'
            Number of hist bins.

        figsize : tuple, default None
            Tuple denoting figure size of the plot.

        filename : str, default None
            If provided, save the current figure.

        grid : boolean, default True
            If True, turn the axes grids on.

        hist : bool, default True
            If True, plot a histogram of anomaly scores.

        title : string, default None
            Axes title. To disable, pass None.

        xlabel : string, default 'Samples'
            X axis title label. To disable, pass None.

        xlim : tuple, default None
            Tuple passed to `ax.xlim`.

        ylabel : string, default 'Anomaly score'
            Y axis title label. To disable, pass None.

        ylim : tuple, default None
            Tuple passed to `ax.ylim`.

        **kwargs : dict
            Other keywords passed to `ax.plot`.

        Returns
        -------
        ax : matplotlib Axes
            Axes on which the plot was drawn.
        """

        kwargs['threshold'] = self.threshold_

        return plot_anomaly_score(self.anomaly_score(X), **kwargs)

    def plot_roc_curve(self, X, y, **kwargs):
        """Plot the Receiver Operating Characteristic (ROC) curve.

        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Data.

        y : array-like of shape (n_samples,)
            Labels.

        ax : matplotlib Axes, default None
            Target axes instance.

        figsize: tuple, default None
            Tuple denoting figure size of the plot.

        filename : str, default None
            If provided, save the current figure.

        grid : boolean, default True
            If True, turn the axes grids on.

        label : str, default None
            Legend label.

        title : string, default None
            Axes title. To disable, pass None.

        xlabel : string, default 'FPR'
            X axis title label. To disable, pass None.

        ylabel : string, default 'TPR'
            Y axis title label. To disable, pass None.

        **kwargs : dict
            Other keywords passed to `ax.plot`.

        Returns
        -------
        ax : matplotlib Axes
            Axes on which the plot was drawn.
        """

        return plot_roc_curve(y, self.anomaly_score(X), **kwargs)