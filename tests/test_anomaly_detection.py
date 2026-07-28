"""
Unit Tests for Statistical Anomaly Detection (IQR, Z-Score, Isolation Forest).
"""
import pandas as pd
import numpy as np
from scipy import stats


def test_iqr_outlier_detection():
    """Test IQR outlier detection logic on synthetic numerical data."""
    data = [10, 12, 11, 13, 12, 10, 11, 14, 12, 500] # 500 is extreme outlier
    df = pd.DataFrame({"revenue": data})
    
    q1 = df["revenue"].quantile(0.25)
    q3 = df["revenue"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr
    
    outliers = df[df["revenue"] > upper_bound]
    assert len(outliers) == 1
    assert outliers.iloc[0]["revenue"] == 500


def test_zscore_outlier_detection():
    """Test Z-score statistical outlier flagging."""
    data = [100] * 30 + [10000]
    z_scores = np.abs(stats.zscore(np.array(data, dtype=float)))  # type: ignore
    outlier_indices = np.where(z_scores > 3.0)[0]
    
    assert len(outlier_indices) == 1
    assert data[outlier_indices[0]] == 10000
