#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模块集合 - 统一导出接口
"""

from .data_acquisition import DataFetcher, get_data_fetcher
from .fundamental_analysis import FundamentalAnalyzer, get_fundamental_analyzer
from .short_term_analysis import (
    ShortTermAlgorithm,
    FundamentalMomentumAlgorithm,
    MeanReversionAlgorithm,
    BreakoutAlgorithm,
    Trade,
    BacktestResult,
    BacktestEngine,
    Position,
    SimulationResult,
    PortfolioSimulator,
    get_all_algorithms
)
from .output import OutputManager, get_output_manager

__all__ = [
    "DataFetcher",
    "get_data_fetcher",
    "FundamentalAnalyzer",
    "get_fundamental_analyzer",
    "ShortTermAlgorithm",
    "FundamentalMomentumAlgorithm",
    "MeanReversionAlgorithm",
    "BreakoutAlgorithm",
    "Trade",
    "BacktestResult",
    "BacktestEngine",
    "Position",
    "SimulationResult",
    "PortfolioSimulator",
    "get_all_algorithms",
    "OutputManager",
    "get_output_manager"
]
