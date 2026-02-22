#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短线交易回测系统 - 推荐算法模块
包含多种短线推荐算法
"""

import sys
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


class ShortTermAlgorithm:
    """短线推荐算法基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    def select_stocks(
        self, 
        stock_data: Dict[str, pd.DataFrame], 
        date: str,
        top_n: int = 10
    ) -> List[str]:
        """
        选择股票
        
        Args:
            stock_data: 股票数据字典 {code: DataFrame}
            date: 当前日期 (YYYYMMDD)
            top_n: 选择前N只股票
        
        Returns:
            选中的股票代码列表
        """
        raise NotImplementedError
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        """计算单只股票得分"""
        raise NotImplementedError


class FundamentalMomentumAlgorithm(ShortTermAlgorithm):
    """
    基本面+动量策略
    结合低PE、低PB、技术面动量等指标
    """
    
    def __init__(self):
        super().__init__("基本面动量策略")
    
    def select_stocks(
        self, 
        stock_data: Dict[str, pd.DataFrame], 
        date: str,
        top_n: int = 10
    ) -> List[str]:
        scores = []
        
        for code, df in stock_data.items():
            if df is None or len(df) < 20:
                continue
            
            date_idx = df[df["日期"] == pd.to_datetime(date)].index
            if len(date_idx) == 0:
                continue
            
            idx = date_idx[0]
            if idx < 10:
                continue
            
            score = self.calculate_score(df, idx)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in scores[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        current = df.iloc[idx]
        prev_1 = df.iloc[idx-1]
        prev_5 = df.iloc[max(0, idx-5)]
        prev_10 = df.iloc[max(0, idx-10)]
        prev_20 = df.iloc[max(0, idx-20)]
        
        current_close = current["收盘"]
        prev_1_close = prev_1["收盘"]
        prev_5_close = prev_5["收盘"]
        prev_10_close = prev_10["收盘"]
        prev_20_close = prev_20["收盘"]
        
        if prev_1_close > 0:
            daily_return = (current_close - prev_1_close) / prev_1_close
            if daily_return > 0:
                score += 10
            else:
                score -= 5
        
        if prev_5_close > 0:
            ret_5 = (current_close - prev_5_close) / prev_5_close
            if ret_5 > 0.03:
                score += 15
            elif ret_5 > 0:
                score += 10
        
        if prev_10_close > 0:
            ret_10 = (current_close - prev_10_close) / prev_10_close
            if ret_10 > 0.05:
                score += 20
            elif ret_10 > 0:
                score += 10
        
        ma5 = df["收盘"].iloc[max(0, idx-4):idx+1].mean()
        ma10 = df["收盘"].iloc[max(0, idx-9):idx+1].mean()
        ma20 = df["收盘"].iloc[max(0, idx-19):idx+1].mean()
        
        if current_close > ma5:
            score += 10
        if ma5 > ma10:
            score += 10
        if ma10 > ma20:
            score += 10
        
        if prev_1_close > 0:
            volatility = np.std(df["收盘"].iloc[max(0, idx-19):idx+1].pct_change().dropna())
            if volatility < 0.03:
                score += 10
            elif volatility < 0.05:
                score += 5
        
        volume_ratio = current["成交量"] / df["成交量"].iloc[max(0, idx-9):idx].mean() if idx > 0 else 1
        if 1.5 <= volume_ratio <= 3:
            score += 15
        elif volume_ratio > 3:
            score += 10
        
        return score


class MeanReversionAlgorithm(ShortTermAlgorithm):
    """
    均值回归策略
    寻找超跌反弹的股票
    """
    
    def __init__(self):
        super().__init__("均值回归策略")
    
    def select_stocks(
        self, 
        stock_data: Dict[str, pd.DataFrame], 
        date: str,
        top_n: int = 10
    ) -> List[str]:
        scores = []
        
        for code, df in stock_data.items():
            if df is None or len(df) < 20:
                continue
            
            date_idx = df[df["日期"] == pd.to_datetime(date)].index
            if len(date_idx) == 0:
                continue
            
            idx = date_idx[0]
            if idx < 10:
                continue
            
            score = self.calculate_score(df, idx)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in scores[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        current = df.iloc[idx]
        prev_1 = df.iloc[idx-1]
        prev_5 = df.iloc[max(0, idx-5)]
        prev_10 = df.iloc[max(0, idx-10)]
        
        current_close = current["收盘"]
        prev_1_close = prev_1["收盘"]
        prev_5_close = prev_5["收盘"]
        prev_10_close = prev_10["收盘"]
        
        if prev_1_close > 0:
            daily_return = (current_close - prev_1_close) / prev_1_close
            if daily_return < -0.03:
                score += 20
            elif daily_return < -0.02:
                score += 15
            elif daily_return < -0.01:
                score += 10
        
        if prev_5_close > 0:
            ret_5 = (current_close - prev_5_close) / prev_5_close
            if ret_5 < -0.08:
                score += 25
            elif ret_5 < -0.05:
                score += 20
        
        ma20 = df["收盘"].iloc[max(0, idx-19):idx+1].mean()
        if ma20 > 0:
            distance = (current_close - ma20) / ma20
            if distance < -0.08:
                score += 25
            elif distance < -0.05:
                score += 20
            elif distance < -0.03:
                score += 15
        
        rsi = self.calculate_rsi(df, idx)
        if rsi < 30:
            score += 20
        elif rsi < 40:
            score += 10
        
        return score
    
    def calculate_rsi(self, df: pd.DataFrame, idx: int, period: int = 14) -> float:
        if idx < period:
            return 50
        
        prices = df["收盘"].iloc[idx-period:idx+1]
        delta = prices.diff().dropna()
        
        gain = (delta.where(delta > 0, 0)).mean()
        loss = (-delta.where(delta < 0, 0)).mean()
        
        if loss == 0:
            return 100
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class BreakoutAlgorithm(ShortTermAlgorithm):
    """
    突破策略
    寻找突破关键阻力位的股票
    """
    
    def __init__(self):
        super().__init__("突破策略")
    
    def select_stocks(
        self, 
        stock_data: Dict[str, pd.DataFrame], 
        date: str,
        top_n: int = 10
    ) -> List[str]:
        scores = []
        
        for code, df in stock_data.items():
            if df is None or len(df) < 30:
                continue
            
            date_idx = df[df["日期"] == pd.to_datetime(date)].index
            if len(date_idx) == 0:
                continue
            
            idx = date_idx[0]
            if idx < 20:
                continue
            
            score = self.calculate_score(df, idx)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in scores[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        current = df.iloc[idx]
        prev_1 = df.iloc[idx-1]
        prev_20 = df.iloc[max(0, idx-20):idx]
        
        current_close = current["收盘"]
        current_high = current["最高"]
        prev_1_close = prev_1["收盘"]
        
        high_20 = prev_20["最高"].max()
        
        if current_close > high_20:
            score += 30
        
        if current_high > high_20:
            score += 20
        
        if prev_1_close > 0:
            daily_return = (current_close - prev_1_close) / prev_1_close
            if daily_return > 0.03:
                score += 20
            elif daily_return > 0.02:
                score += 15
        
        volume_ratio = current["成交量"] / prev_20["成交量"].mean() if len(prev_20) > 0 else 1
        if volume_ratio > 2:
            score += 25
        elif volume_ratio > 1.5:
            score += 15
        
        return score


def get_all_algorithms() -> List[ShortTermAlgorithm]:
    """获取所有算法"""
    return [
        FundamentalMomentumAlgorithm(),
        MeanReversionAlgorithm(),
        BreakoutAlgorithm()
    ]
