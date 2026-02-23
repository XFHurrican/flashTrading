#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基本面分析模块 - 标准多因子Alpha框架
"""

import pandas as pd
import numpy as np
from typing import List


class FundamentalAnalyzer:
    """基本面分析器 - 标准多因子Alpha框架"""
    
    def __init__(self):
        self.factor_weights = {
            'value_pe': 0.28,
            'value_pb': 0.28,
            'growth_revenue': 0.17,
            'growth_profit': 0.17,
            'quality_roe': 0.10
        }
    
    def winsorize(self, series: pd.Series, method: str = 'quantile', lower: float = 0.01, upper: float = 0.99) -> pd.Series:
        """去极值处理"""
        s = series.copy()
        if method == 'quantile':
            q_low = s.quantile(lower)
            q_high = s.quantile(upper)
            s = s.clip(lower=q_low, upper=q_high)
        elif method == '3sigma':
            mean = s.mean()
            std = s.std()
            s = s.clip(lower=mean - 3 * std, upper=mean + 3 * std)
        return s
    
    def industry_neutralize(self, df: pd.DataFrame, factor_col: str, industry_col: str = '行业') -> pd.Series:
        """行业内标准化（Z-score）"""
        def neutralize_group(group):
            mean = group.mean()
            std = group.std()
            if std == 0:
                return group - mean
            return (group - mean) / std
        
        return df.groupby(industry_col)[factor_col].transform(neutralize_group)
    
    def calculate_alpha_score(self, spot_df: pd.DataFrame, financial_df: pd.DataFrame = None) -> pd.DataFrame:
        """计算标准多因子Alpha评分"""
        
        df = spot_df.copy()
        
        numeric_cols = ['最新价', '市盈率-动态', '市净率', '总股本']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df[
            (df['市盈率-动态'] > 0) &
            (df['市净率'] > 0)
        ].copy()
        
        if financial_df is not None and not financial_df.empty and '代码' in financial_df.columns:
            df = df.merge(financial_df, on='代码', how='left')
        
        if '行业' in df.columns:
            industry_counts = df['行业'].value_counts()
            valid_industries = industry_counts[industry_counts >= 5].index
            df = df[df['行业'].isin(valid_industries)].copy()
            print(f"✅ 过滤小样本行业后，剩余 {len(df)} 只股票，{len(valid_industries)} 个行业")
        
        df['log_pe'] = np.log(df['市盈率-动态'])
        df['log_pb'] = np.log(df['市净率'])
        
        df['log_pe'] = self.winsorize(df['log_pe'], method='quantile')
        df['log_pb'] = self.winsorize(df['log_pb'], method='quantile')
        
        if '行业' in df.columns and df['行业'].notna().any():
            df['factor_pe'] = -self.industry_neutralize(df, 'log_pe')
            df['factor_pb'] = -self.industry_neutralize(df, 'log_pb')
        else:
            df['factor_pe'] = -(df['log_pe'] - df['log_pe'].mean()) / df['log_pe'].std()
            df['factor_pb'] = -(df['log_pb'] - df['log_pb'].mean()) / df['log_pb'].std()
        
        df['factor_growth_revenue'] = 0.0
        df['factor_growth_profit'] = 0.0
        
        if '营收同比' in df.columns:
            df['营收同比'] = pd.to_numeric(df['营收同比'], errors='coerce')
            df['营收同比_clean'] = self.winsorize(df['营收同比'], method='quantile')
            df['factor_growth_revenue'] = np.where(
                df['营收同比_clean'].notna(),
                df['营收同比_clean'],
                0.0
            )
            
            df['factor_growth_revenue'] = np.where(
                df['营收同比_clean'] < 0,
                df['factor_growth_revenue'] * 1.5,
                df['factor_growth_revenue']
            )
        
        if '净利润同比' in df.columns:
            df['净利润同比'] = pd.to_numeric(df['净利润同比'], errors='coerce')
            df['净利润同比_clean'] = self.winsorize(df['净利润同比'], method='quantile')
            df['factor_growth_profit'] = np.where(
                df['净利润同比_clean'].notna(),
                df['净利润同比_clean'],
                0.0
            )
            
            df['factor_growth_profit'] = np.where(
                df['净利润同比_clean'] < 0,
                df['factor_growth_profit'] * 1.5,
                df['factor_growth_profit']
            )
        
        if '行业' in df.columns and df['行业'].notna().any():
            df['factor_growth_revenue'] = self.industry_neutralize(df, 'factor_growth_revenue')
            df['factor_growth_profit'] = self.industry_neutralize(df, 'factor_growth_profit')
        
        df['factor_quality_roe'] = 0.0
        if 'ROE' in df.columns:
            df['ROE'] = pd.to_numeric(df['ROE'], errors='coerce')
            df['ROE_clean'] = self.winsorize(df['ROE'], method='quantile')
            df['factor_quality_roe'] = np.where(
                df['ROE_clean'].notna(),
                df['ROE_clean'],
                0.0
            )
            
            if '行业' in df.columns and df['行业'].notna().any():
                df['factor_quality_roe'] = self.industry_neutralize(df, 'factor_quality_roe')
        
        df['alpha_score'] = (
            self.factor_weights['value_pe'] * df['factor_pe'] +
            self.factor_weights['value_pb'] * df['factor_pb'] +
            self.factor_weights['growth_revenue'] * df['factor_growth_revenue'] +
            self.factor_weights['growth_profit'] * df['factor_growth_profit'] +
            self.factor_weights['quality_roe'] * df['factor_quality_roe']
        )
        
        df['alpha_score_rank'] = df['alpha_score'].rank(pct=True, ascending=False)
        
        df['value_score'] = (
            self.factor_weights['value_pe'] * df['factor_pe'] +
            self.factor_weights['value_pb'] * df['factor_pb']
        )
        df['growth_score'] = (
            self.factor_weights['growth_revenue'] * df['factor_growth_revenue'] +
            self.factor_weights['growth_profit'] * df['factor_growth_profit']
        )
        df['quality_score'] = self.factor_weights['quality_roe'] * df['factor_quality_roe']
        
        return df.sort_values('alpha_score', ascending=False)
    
    def find_undervalued_stocks(self, spot_df: pd.DataFrame, financial_df: pd.DataFrame = None, top_percent: float = 0.1) -> pd.DataFrame:
        """找出被低估的股票"""
        
        df_analyzed = self.calculate_alpha_score(spot_df, financial_df)
        
        if df_analyzed is None or df_analyzed.empty:
            print("❌ 没有找到符合条件的股票")
            return None
        
        result = df_analyzed[df_analyzed['alpha_score_rank'] <= top_percent].copy()
        
        return result


def get_fundamental_analyzer():
    """获取基本面分析器"""
    return FundamentalAnalyzer()
