#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短线分析模块 - 算法、回测、模拟
"""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np


class ShortTermAlgorithm:
    """短线交易算法基类"""
    name = "基类算法"
    
    def select_stocks(self, stock_data: Dict[str, pd.DataFrame], date_str: str, top_n: int = 10) -> List[str]:
        """
        选择股票
        
        Args:
            stock_data: 股票数据字典 {code: DataFrame}
            date_str: 日期字符串 YYYYMMDD
            top_n: 选择前N只股票
            
        Returns:
            股票代码列表
        """
        raise NotImplementedError
    
    def calculate_score(self, df: pd.DataFrame, date_str: str) -> float:
        """计算单只股票得分"""
        raise NotImplementedError


class FundamentalMomentumAlgorithm(ShortTermAlgorithm):
    """基本面+动量算法"""
    name = "基本面+动量"
    
    def select_stocks(self, stock_data: Dict[str, pd.DataFrame], date_str: str, top_n: int = 10) -> List[str]:
        scores = {}
        for code, df in stock_data.items():
            score = self.calculate_score(df, date_str)
            if score is not None:
                scores[code] = score
        
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [code for code, _ in sorted_stocks[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, date_str: str) -> Optional[float]:
        if len(df) < 20:
            return None
        
        try:
            target_date = pd.to_datetime(date_str)
            df = df[df["日期"] <= target_date].copy()
            if len(df) < 20:
                return None
            
            latest = df.iloc[-1]
            prev_20 = df.iloc[-20]
            
            if prev_20["收盘"] <= 0:
                return None
            
            momentum = (latest["收盘"] / prev_20["收盘"] - 1)
            
            if len(df) >= 5:
                prev_5 = df.iloc[-5]
                if prev_5["收盘"] > 0:
                    short_momentum = (latest["收盘"] / prev_5["收盘"] - 1)
                    momentum = momentum * 0.7 + short_momentum * 0.3
            
            return momentum
        except Exception:
            return None


class MeanReversionAlgorithm(ShortTermAlgorithm):
    """均值回归算法"""
    name = "均值回归"
    
    def select_stocks(self, stock_data: Dict[str, pd.DataFrame], date_str: str, top_n: int = 10) -> List[str]:
        scores = {}
        for code, df in stock_data.items():
            score = self.calculate_score(df, date_str)
            if score is not None:
                scores[code] = score
        
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [code for code, _ in sorted_stocks[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, date_str: str) -> Optional[float]:
        if len(df) < 20:
            return None
        
        try:
            target_date = pd.to_datetime(date_str)
            df = df[df["日期"] <= target_date].copy()
            if len(df) < 20:
                return None
            
            latest = df.iloc[-1]
            ma20 = df["收盘"].iloc[-20:].mean()
            
            if ma20 <= 0:
                return None
            
            deviation = (ma20 - latest["收盘"]) / ma20
            
            if len(df) >= 60:
                ma60 = df["收盘"].iloc[-60:].mean()
                if ma60 > 0 and latest["收盘"] < ma60:
                    deviation += 0.5 * (ma60 - latest["收盘"]) / ma60
            
            return deviation
        except Exception:
            return None


class BreakoutAlgorithm(ShortTermAlgorithm):
    """突破算法"""
    name = "突破"
    
    def select_stocks(self, stock_data: Dict[str, pd.DataFrame], date_str: str, top_n: int = 10) -> List[str]:
        scores = {}
        for code, df in stock_data.items():
            score = self.calculate_score(df, date_str)
            if score is not None:
                scores[code] = score
        
        sorted_stocks = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [code for code, _ in sorted_stocks[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, date_str: str) -> Optional[float]:
        if len(df) < 30:
            return None
        
        try:
            target_date = pd.to_datetime(date_str)
            df = df[df["日期"] <= target_date].copy()
            if len(df) < 30:
                return None
            
            latest = df.iloc[-1]
            high_20 = df["最高"].iloc[-20:-1].max()
            
            if latest["收盘"] > high_20 and len(df) >= 2:
                prev = df.iloc[-2]
                if prev["收盘"] > 0:
                    return (latest["收盘"] - prev["收盘"]) / prev["收盘"]
            
            return None
        except Exception:
            return None


class Trade:
    """交易记录"""
    def __init__(self, code: str, buy_date: str, buy_price: float, sell_date: str = None, sell_price: float = None):
        self.code = code
        self.buy_date = buy_date
        self.buy_price = buy_price
        self.sell_date = sell_date
        self.sell_price = sell_price
    
    def is_closed(self) -> bool:
        return self.sell_date is not None
    
    def calculate_return(self) -> float:
        if not self.is_closed():
            return 0.0
        return (self.sell_price - self.buy_price) / self.buy_price


class BacktestResult:
    """回测结果"""
    def __init__(self, algorithm_name: str):
        self.algorithm_name = algorithm_name
        self.trades: List[Trade] = []
        self.initial_capital = 0.0
        self.final_capital = 0.0
    
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
    
    def calculate_statistics(self) -> Optional[Dict]:
        if not self.trades:
            return None
        
        closed_trades = [t for t in self.trades if t.is_closed()]
        if not closed_trades:
            return None
        
        returns = [t.calculate_return() for t in closed_trades]
        win_trades = [r for r in returns if r > 0]
        
        win_rate = len(win_trades) / len(closed_trades)
        total_return = sum(returns)
        avg_return = total_return / len(closed_trades)
        
        return {
            'algorithm': self.algorithm_name,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_return': avg_return,
            'total_trades': len(closed_trades)
        }


class BacktestEngine:
    """回测引擎"""
    def __init__(self, data_fetcher, initial_capital: float = 100000):
        self.data_fetcher = data_fetcher
        self.initial_capital = initial_capital
    
    def run_backtest(
        self,
        algorithm: ShortTermAlgorithm,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        top_n: int = 10
    ) -> BacktestResult:
        result = BacktestResult(algorithm.name)
        result.initial_capital = self.initial_capital
        
        stock_data = {}
        for code in stock_codes[:100]:
            df = self.data_fetcher.get_stock_historical_data(code, start_date, end_date)
            if df is not None and len(df) > 30:
                stock_data[code] = df
        
        if not stock_data:
            return result
        
        trading_days = sorted({df["日期"].max() for df in stock_data.values()})
        if not trading_days:
            return result
        
        result.final_capital = self.initial_capital
        
        return result


class Position:
    """持仓"""
    def __init__(self, code: str, quantity: int, buy_price: float, buy_date: str):
        self.code = code
        self.quantity = quantity
        self.buy_price = buy_price
        self.buy_date = buy_date


class SimulationResult:
    """模拟结果"""
    def __init__(self):
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Trade] = []
        self.capital_history: List[Dict] = []
    
    def print_summary(self):
        print("\n📊 模拟结果总结")
        print("=" * 80)
        print(f"持仓数量: {len(self.positions)}")
        print(f"交易次数: {len(self.trade_history)}")


class PortfolioSimulator:
    """组合模拟器"""
    def __init__(self, data_fetcher, algorithm, initial_capital: float = 100000, top_n: int = 8):
        self.data_fetcher = data_fetcher
        self.algorithm = algorithm
        self.initial_capital = initial_capital
        self.top_n = top_n
    
    def run_simulation(
        self,
        stock_codes: List[str],
        start_date: str,
        end_date: str
    ) -> SimulationResult:
        result = SimulationResult()
        return result


def get_all_algorithms() -> List[ShortTermAlgorithm]:
    """获取所有基础算法"""
    return [
        FundamentalMomentumAlgorithm(),
        MeanReversionAlgorithm(),
        BreakoutAlgorithm()
    ]
