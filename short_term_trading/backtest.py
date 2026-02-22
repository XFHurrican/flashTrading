#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短线交易回测系统 - 回测引擎模块
实现买入/卖出逻辑和回测结果统计
"""

import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .algorithms import ShortTermAlgorithm
from .data_fetcher import ShortTermDataFetcher


class Trade:
    """单笔交易记录"""
    
    def __init__(
        self, 
        code: str, 
        buy_date: str, 
        buy_price: float, 
        sell_date: str, 
        sell_price: float
    ):
        self.code = code
        self.buy_date = buy_date
        self.buy_price = buy_price
        self.sell_date = sell_date
        self.sell_price = sell_price
        
        if buy_price > 0:
            self.return_rate = (sell_price - buy_price) / buy_price
        else:
            self.return_rate = 0
        
        self.profit = sell_price - buy_price
        self.is_win = self.return_rate > 0


class BacktestResult:
    """回测结果"""
    
    def __init__(self, algorithm_name: str):
        self.algorithm_name = algorithm_name
        self.trades: List[Trade] = []
        self.start_date = None
        self.end_date = None
        self.initial_capital = 100000
        self.final_capital = 100000
    
    def add_trade(self, trade: Trade):
        self.trades.append(trade)
    
    def calculate_statistics(self) -> Dict:
        """计算回测统计指标"""
        if not self.trades:
            return {}
        
        total_trades = len(self.trades)
        win_trades = sum(1 for t in self.trades if t.is_win)
        lose_trades = total_trades - win_trades
        
        win_rate = win_trades / total_trades if total_trades > 0 else 0
        
        returns = [t.return_rate for t in self.trades]
        avg_return = np.mean(returns)
        total_return = sum(t.return_rate for t in self.trades)
        
        win_returns = [t.return_rate for t in self.trades if t.is_win]
        lose_returns = [t.return_rate for t in self.trades if not t.is_win]
        
        avg_win = np.mean(win_returns) if win_returns else 0
        avg_lose = np.mean(lose_returns) if lose_returns else 0
        max_win = max(win_returns) if win_returns else 0
        max_lose = min(lose_returns) if lose_returns else 0
        
        profit_loss_ratio = abs(avg_win / avg_lose) if avg_lose != 0 else 0
        
        cumulative = np.cumsum(returns)
        peak = np.maximum.accumulate(cumulative)
        drawdown = peak - cumulative
        max_drawdown = np.max(drawdown) if len(drawdown) > 0 else 0
        
        if self.start_date and self.end_date:
            start = datetime.strptime(self.start_date, "%Y%m%d")
            end = datetime.strptime(self.end_date, "%Y%m%d")
            years = (end - start).days / 365.25
            if years > 0 and self.initial_capital > 0:
                self.final_capital = self.initial_capital * (1 + total_return)
                annual_return = (self.final_capital / self.initial_capital) ** (1 / years) - 1
            else:
                annual_return = 0
        else:
            annual_return = 0
        
        return {
            "algorithm": self.algorithm_name,
            "total_trades": total_trades,
            "win_trades": win_trades,
            "lose_trades": lose_trades,
            "win_rate": win_rate,
            "avg_return": avg_return,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_lose": avg_lose,
            "max_win": max_win,
            "max_lose": max_lose,
            "profit_loss_ratio": profit_loss_ratio,
            "max_drawdown": max_drawdown,
            "annual_return": annual_return,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "start_date": self.start_date,
            "end_date": self.end_date
        }
    
    def print_summary(self):
        """打印回测总结"""
        stats = self.calculate_statistics()
        if not stats:
            print("没有交易记录")
            return
        
        print("\n" + "=" * 80)
        print(f"📊 回测结果 - {self.algorithm_name}")
        print("=" * 80)
        print(f"交易时段: {stats['start_date']} 至 {stats['end_date']}")
        print(f"初始资金: ¥{stats['initial_capital']:,.2f}")
        print(f"最终资金: ¥{stats['final_capital']:,.2f}")
        print()
        print(f"总交易次数: {stats['total_trades']}")
        print(f"盈利次数: {stats['win_trades']}")
        print(f"亏损次数: {stats['lose_trades']}")
        print()
        print(f"胜率: {stats['win_rate']*100:.2f}%")
        print(f"总收益率: {stats['total_return']*100:.2f}%")
        print(f"年化收益率: {stats['annual_return']*100:.2f}%")
        print(f"平均单次收益: {stats['avg_return']*100:.2f}%")
        print()
        print(f"平均盈利: {stats['avg_win']*100:.2f}%")
        print(f"平均亏损: {stats['avg_lose']*100:.2f}%")
        print(f"盈亏比: {stats['profit_loss_ratio']:.2f}")
        print()
        print(f"最大盈利: {stats['max_win']*100:.2f}%")
        print(f"最大亏损: {stats['max_lose']*100:.2f}%")
        print(f"最大回撤: {stats['max_drawdown']*100:.2f}%")
        print("=" * 80)


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self, 
        data_fetcher: ShortTermDataFetcher,
        initial_capital: float = 100000,
        position_size: float = 0.1
    ):
        self.data_fetcher = data_fetcher
        self.initial_capital = initial_capital
        self.position_size = position_size
    
    def run_backtest(
        self,
        algorithm: ShortTermAlgorithm,
        stock_codes: List[str],
        start_date: str,
        end_date: str,
        top_n: int = 10
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            algorithm: 推荐算法
            stock_codes: 股票代码列表
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            top_n: 每日选择前N只股票
        
        Returns:
            回测结果
        """
        print(f"\n🚀 开始回测 - {algorithm.name}")
        print(f"股票数量: {len(stock_codes)}")
        print(f"回测时段: {start_date} 至 {end_date}")
        
        result = BacktestResult(algorithm.name)
        result.start_date = start_date
        result.end_date = end_date
        result.initial_capital = self.initial_capital
        
        print("\n正在下载股票数据...")
        stock_data = {}
        for i, code in enumerate(stock_codes):
            if i % 50 == 0:
                print(f"  进度: {i}/{len(stock_codes)}")
            df = self.data_fetcher.get_stock_historical_data(code, start_date, end_date)
            if df is not None and len(df) > 30:
                stock_data[code] = df
        
        print(f"✅ 成功加载 {len(stock_data)} 只股票数据")
        
        print("\n正在获取交易日历...")
        trading_days = self.data_fetcher.get_trading_days(start_date, end_date)
        if not trading_days:
            print("❌ 获取交易日历失败")
            return result
        
        print(f"✅ 共 {len(trading_days)} 个交易日")
        
        print("\n正在执行回测...")
        for i in range(len(trading_days) - 1):
            buy_date = trading_days[i]
            sell_date = trading_days[i + 1]
            
            if i % 50 == 0:
                print(f"  进度: {i}/{len(trading_days)-1}")
            
            selected_stocks = algorithm.select_stocks(stock_data, buy_date, top_n)
            
            for code in selected_stocks:
                df = stock_data.get(code)
                if df is None:
                    continue
                
                buy_idx = df[df["日期"] == pd.to_datetime(buy_date)].index
                sell_idx = df[df["日期"] == pd.to_datetime(sell_date)].index
                
                if len(buy_idx) == 0 or len(sell_idx) == 0:
                    continue
                
                buy_idx = buy_idx[0]
                sell_idx = sell_idx[0]
                
                buy_price = df.iloc[buy_idx]["收盘"]
                sell_price = df.iloc[sell_idx]["开盘"]
                
                if buy_price > 0 and sell_price > 0:
                    trade = Trade(code, buy_date, buy_price, sell_date, sell_price)
                    result.add_trade(trade)
        
        print(f"✅ 回测完成，共 {len(result.trades)} 笔交易")
        
        return result
