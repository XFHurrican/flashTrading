#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短线交易回测系统
基于A股历史数据的隔日交易策略回测
"""

from .data_fetcher import ShortTermDataFetcher, get_data_fetcher
from .algorithms import (
    ShortTermAlgorithm,
    FundamentalMomentumAlgorithm,
    MeanReversionAlgorithm,
    BreakoutAlgorithm,
    get_all_algorithms
)
from .advanced_algorithms import (
    MACDAlgorithm,
    KDJAlgorithm,
    BOLLAlgorithm,
    TripleIndicatorAlgorithm,
    get_all_advanced_algorithms
)
from .backtest import Trade, BacktestResult, BacktestEngine

__all__ = [
    "ShortTermDataFetcher",
    "get_data_fetcher",
    "ShortTermAlgorithm",
    "FundamentalMomentumAlgorithm",
    "MeanReversionAlgorithm",
    "BreakoutAlgorithm",
    "get_all_algorithms",
    "MACDAlgorithm",
    "KDJAlgorithm",
    "BOLLAlgorithm",
    "TripleIndicatorAlgorithm",
    "get_all_advanced_algorithms",
    "Trade",
    "BacktestResult",
    "BacktestEngine"
]
