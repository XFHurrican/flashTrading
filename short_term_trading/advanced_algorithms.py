#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短线交易回测系统 - 高级算法模块
包含MACD、KDJ、BOLL等专业量化策略
"""

import sys
from typing import Dict, List
import pandas as pd
import numpy as np

from .algorithms import ShortTermAlgorithm


class MACDAlgorithm(ShortTermAlgorithm):
    """
    MACD策略
    DIF上穿DEA金叉，零轴上方更优
    """
    
    def __init__(self):
        super().__init__("MACD金叉策略")
    
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
            if idx < 26:
                continue
            
            score = self.calculate_score(df, idx)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in scores[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        closes = df["收盘"].iloc[:idx+1].values
        
        ema12 = self.calculate_ema(closes, 12)
        ema26 = self.calculate_ema(closes, 26)
        dif = ema12 - ema26
        dea = self.calculate_ema(dif, 9)
        macd_bar = (dif - dea) * 2
        
        if len(dif) >= 2 and len(dea) >= 2:
            dif_prev = dif[-2]
            dif_curr = dif[-1]
            dea_prev = dea[-2]
            dea_curr = dea[-1]
            
            if dif_prev <= dea_prev and dif_curr > dea_curr:
                score += 30
                
                if dif_curr > 0:
                    score += 20
            
            if len(macd_bar) >= 2:
                if macd_bar[-1] > 0 and macd_bar[-1] > macd_bar[-2]:
                    score += 15
        
        if len(dif) >= 1:
            if dif[-1] > 0:
                score += 10
        
        return score
    
    def calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        ema = np.zeros_like(data)
        ema[0] = data[0]
        alpha = 2 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema


class KDJAlgorithm(ShortTermAlgorithm):
    """
    KDJ策略
    K、D在20以下金叉，超卖反弹
    """
    
    def __init__(self):
        super().__init__("KDJ超卖金叉策略")
    
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
            if idx < 14:
                continue
            
            score = self.calculate_score(df, idx)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in scores[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        k, d, j = self.calculate_kdj(df, idx)
        
        if k is not None and d is not None and j is not None:
            k_prev, d_prev, j_prev = self.calculate_kdj(df, idx-1)
            
            if k_prev is not None and d_prev is not None:
                if k_prev <= d_prev and k > d:
                    score += 25
                    
                    if k < 30:
                        score += 20
                    elif k < 40:
                        score += 10
            
            if k < 20:
                score += 15
            elif k < 30:
                score += 10
            
            if j < 0:
                score += 20
            elif j < 10:
                score += 10
        
        return score
    
    def calculate_kdj(self, df: pd.DataFrame, idx: int, n: int = 9, m1: int = 3, m2: int = 3):
        if idx < n:
            return None, None, None
        
        data_slice = df.iloc[max(0, idx-n-5):idx+1]
        
        low_list = data_slice["最低"].rolling(n, min_periods=1).min()
        high_list = data_slice["最高"].rolling(n, min_periods=1).max()
        
        rsv = (data_slice["收盘"] - low_list) / (high_list - low_list) * 100
        rsv = rsv.fillna(50)
        
        k = rsv.ewm(com=m1-1, adjust=False).mean()
        d = k.ewm(com=m2-1, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return k.iloc[-1], d.iloc[-1], j.iloc[-1]


class BOLLAlgorithm(ShortTermAlgorithm):
    """
    BOLL布林带策略
    触及下轨反弹，或突破中轨
    """
    
    def __init__(self):
        super().__init__("BOLL下轨反弹策略")
    
    def select_stocks(
        self, 
        stock_data: Dict[str, pd.DataFrame], 
        date: str,
        top_n: int = 10
    ) -> List[str]:
        scores = []
        
        for code, df in stock_data.items():
            if df is None or len(df) < 25:
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
        
        data_slice = df.iloc[max(0, idx-25):idx+1]
        closes = data_slice["收盘"].values
        
        ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        std20 = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
        
        upper = ma20 + 2 * std20
        lower = ma20 - 2 * std20
        
        current_close = closes[-1]
        prev_close = closes[-2] if len(closes) >= 2 else current_close
        
        if current_close <= lower:
            score += 30
            
            if current_close > prev_close:
                score += 20
        
        if prev_close <= lower and current_close > lower:
            score += 25
        
        if current_close > ma20 and prev_close <= ma20:
            score += 20
        
        if current_close > ma20:
            score += 10
        
        return score


class TripleIndicatorAlgorithm(ShortTermAlgorithm):
    """
    MACD+RSI+BOLL三剑合璧策略
    多指标共振，高胜率
    """
    
    def __init__(self):
        super().__init__("MACD+RSI+BOLL共振策略")
    
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
            if idx < 26:
                continue
            
            score = self.calculate_score(df, idx)
            scores.append((code, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        return [code for code, score in scores[:top_n]]
    
    def calculate_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        macd_score = self.calculate_macd_score(df, idx)
        rsi_score = self.calculate_rsi_score(df, idx)
        boll_score = self.calculate_boll_score(df, idx)
        
        score = macd_score + rsi_score + boll_score
        
        if macd_score > 20 and rsi_score > 15 and boll_score > 15:
            score += 30
        
        return score
    
    def calculate_macd_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        closes = df["收盘"].iloc[:idx+1].values
        
        ema12 = self.calculate_ema(closes, 12)
        ema26 = self.calculate_ema(closes, 26)
        dif = ema12 - ema26
        dea = self.calculate_ema(dif, 9)
        
        if len(dif) >= 2 and len(dea) >= 2:
            if dif[-2] <= dea[-2] and dif[-1] > dea[-1]:
                score += 20
                if dif[-1] > 0:
                    score += 10
        
        return score
    
    def calculate_rsi_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        if idx < 14:
            return 0
        
        prices = df["收盘"].iloc[idx-14:idx+1]
        delta = prices.diff().dropna()
        
        gain = (delta.where(delta > 0, 0)).mean()
        loss = (-delta.where(delta < 0, 0)).mean()
        
        if loss == 0:
            rsi = 100
        else:
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
        
        if rsi < 30:
            score += 20
        elif rsi < 40:
            score += 10
        
        return score
    
    def calculate_boll_score(self, df: pd.DataFrame, idx: int) -> float:
        score = 0
        
        data_slice = df.iloc[max(0, idx-25):idx+1]
        closes = data_slice["收盘"].values
        
        ma20 = np.mean(closes[-20:]) if len(closes) >= 20 else np.mean(closes)
        std20 = np.std(closes[-20:]) if len(closes) >= 20 else np.std(closes)
        lower = ma20 - 2 * std20
        
        current_close = closes[-1]
        
        if current_close <= lower:
            score += 20
        
        return score
    
    def calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        ema = np.zeros_like(data)
        ema[0] = data[0]
        alpha = 2 / (period + 1)
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        return ema


def get_all_advanced_algorithms() -> List[ShortTermAlgorithm]:
    """获取所有高级算法"""
    return [
        MACDAlgorithm(),
        KDJAlgorithm(),
        BOLLAlgorithm(),
        TripleIndicatorAlgorithm()
    ]
