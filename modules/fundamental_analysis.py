#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基本面分析模块 - 增强版多因子Alpha框架
"""

import pandas as pd
import numpy as np
from typing import List
from sklearn.linear_model import LinearRegression


class FundamentalAnalyzer:
    """基本面分析器 - 增强版多因子Alpha框架"""
    
    def __init__(self):
        self.factor_weights = {
            'value': 0.25,
            'quality': 0.50,
            'growth': 0.25
        }
        self.rolling_window = 20  # 滚动窗口长度
        self.ic_history = {}  # IC历史记录
        self.ir_history = {}  # IR历史记录
        self.priority_data_source = 'xueqiu'  # 优先数据来源
    
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
            if std == 0 or pd.isna(std):
                return group - mean
            return (group - mean) / std
        
        return df.groupby(industry_col)[factor_col].transform(neutralize_group)
    
    def size_neutralize(self, df: pd.DataFrame, factor_col: str, size_col: str = 'log_mktcap') -> pd.Series:
        """
        市值中性化：对因子做市值回归，取残差
        """
        df_valid = df[[factor_col, size_col]].dropna().copy()
        
        if len(df_valid) < 10:
            return df[factor_col].copy()
        
        X = df_valid[[size_col]]
        y = df_valid[factor_col]
        
        model = LinearRegression().fit(X, y)
        residual = y - model.predict(X)
        
        result = df[factor_col].copy()
        result.loc[df_valid.index] = residual
        
        return result
    
    def fill_missing_with_industry_mean(self, df: pd.DataFrame, factor_col: str, industry_col: str = '行业') -> pd.Series:
        """用行业均值填充缺失数据"""
        return df.groupby(industry_col)[factor_col].transform(
            lambda x: x.fillna(x.mean())
        )
    
    def orthogonalize_factors(self, df: pd.DataFrame, primary_col: str, secondary_col: str) -> pd.Series:
        """因子正交化：将secondary_col对primary_col做回归，取残差作为正交化后的因子"""
        valid_mask = df[primary_col].notna() & df[secondary_col].notna()
        if valid_mask.sum() < 2:
            return df[secondary_col].copy()
        
        x = df.loc[valid_mask, primary_col].values.reshape(-1, 1)
        y = df.loc[valid_mask, secondary_col].values
        
        x_mean = x.mean()
        y_mean = y.mean()
        x_centered = x - x_mean
        y_centered = y - y_mean
        
        beta = (x_centered.T @ x_centered).item()
        if beta == 0:
            return df[secondary_col].copy()
        
        beta = (x_centered.T @ y_centered).item() / beta
        
        result = df[secondary_col].copy()
        result.loc[valid_mask] = y_centered - beta * x_centered.flatten() + y_mean
        
        return result
    
    def calculate_ic(self, factor: pd.Series, returns: pd.Series) -> float:
        """计算因子与收益的相关系数(IC)"""
        valid_mask = factor.notna() & returns.notna()
        if valid_mask.sum() < 10:
            return 0.0
        return factor[valid_mask].corr(returns[valid_mask])
    
    def calculate_ic_ir(self, factor_series: pd.Series, returns_series: pd.Series) -> float:
        """计算因子的信息比率(IC_IR)"""
        ics = []
        for i in range(len(factor_series) - self.rolling_window + 1):
            factor_window = factor_series.iloc[i:i+self.rolling_window]
            returns_window = returns_series.iloc[i:i+self.rolling_window]
            ic = self.calculate_ic(factor_window, returns_window)
            if ic != 0:
                ics.append(ic)
        
        if not ics:
            return 0.0
        
        mean_ic = np.mean(ics)
        std_ic = np.std(ics)
        if std_ic == 0:
            return 0.0
        return mean_ic / std_ic
    
    def calculate_rolling_ic(self, df: pd.DataFrame, factor_col: str, return_col: str = 'next_return') -> pd.Series:
        """计算滚动IC"""
        rolling_ics = []
        for i in range(len(df) - self.rolling_window + 1):
            window_df = df.iloc[i:i+self.rolling_window]
            ic = self.calculate_ic(window_df[factor_col], window_df[return_col])
            rolling_ics.append(ic)
        return pd.Series(rolling_ics)
    
    def dynamic_factor_weights(self, df: pd.DataFrame) -> dict:
        """基于滚动IC或风险平价法动态确定因子权重"""
        # 这里简化实现，使用风险平价法
        weights = {}
        factors = ['value', 'quality', 'growth']
        
        # 计算各因子的波动率
        volatilities = {}
        for factor in factors:
            if factor in df.columns:
                vol = df[factor].std()
                volatilities[factor] = vol if vol > 0 else 0.1
            else:
                volatilities[factor] = 0.1
        
        # 风险平价权重
        inv_vol_sum = sum(1/vol for vol in volatilities.values())
        for factor, vol in volatilities.items():
            weights[factor] = (1/vol) / inv_vol_sum
        
        print(f"📊 动态因子权重: {weights}")
        return weights
    
    def calculate_alpha_score(self, spot_df: pd.DataFrame, financial_df: pd.DataFrame = None) -> pd.DataFrame:
        """计算增强版多因子Alpha评分"""
        
        df = spot_df.copy()
        
        numeric_cols = ['最新价', '市盈率-动态', '市净率', '总股本', '总市值']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df = df[
            (df['市盈率-动态'] > 0) &
            (df['市净率'] > 0)
        ].copy()
        
        if financial_df is not None and not financial_df.empty and '代码' in financial_df.columns:
            print(f"📊 开始合并财务数据，财务数据行数: {len(financial_df)}")
            print(f"📊 股票数据中代码列的示例: {df['代码'].head(5).tolist()}")
            print(f"📊 财务数据中代码列的示例: {financial_df['代码'].head(5).tolist()}")
            
            # 检查代码格式
            df['代码'] = df['代码'].astype(str)
            financial_df['代码'] = financial_df['代码'].astype(str)
            
            # 合并数据
            merged_df = df.merge(financial_df, on='代码', how='left')
            
            # 检查合并结果
            merged_count = len(merged_df[merged_df['ROE'].notna()]) if 'ROE' in merged_df.columns else 0
            print(f"✅ 财务数据合并完成，成功匹配的股票数量: {merged_count}")
            
            df = merged_df
        
        if '行业' in df.columns:
            industry_counts = df['行业'].value_counts()
            valid_industries = industry_counts[industry_counts >= 5].index
            df = df[df['行业'].isin(valid_industries)].copy()
            print(f"✅ 过滤小样本行业后，剩余 {len(df)} 只股票，{len(valid_industries)} 个行业")
        
        # 计算市值
        if '总市值' in df.columns:
            df['总市值'] = pd.to_numeric(df['总市值'], errors='coerce')
            df = df[df['总市值'] > 0].copy()
            df['log_mktcap'] = np.log(df['总市值'])
        elif '总股本' in df.columns and '最新价' in df.columns:
            df['总市值'] = df['总股本'] * df['最新价']
            df = df[df['总市值'] > 0].copy()
            df['log_mktcap'] = np.log(df['总市值'])
        
        # 计算价值因子相关指标
        df['log_pe'] = np.log(df['市盈率-动态'])
        df['log_pb'] = np.log(df['市净率'])
        
        # 计算EV/EBITDA、PS、CF yield（如果有数据）
        if 'EV/EBITDA' in df.columns:
            df['EV/EBITDA'] = pd.to_numeric(df['EV/EBITDA'], errors='coerce')
            df = df[df['EV/EBITDA'] > 0].copy()
            df['log_ev_ebitda'] = np.log(df['EV/EBITDA'])
        
        if '市销率' in df.columns:
            df['市销率'] = pd.to_numeric(df['市销率'], errors='coerce')
            df = df[df['市销率'] > 0].copy()
            df['log_ps'] = np.log(df['市销率'])
        
        if '经营现金流' in df.columns and '总市值' in df.columns:
            df['经营现金流'] = pd.to_numeric(df['经营现金流'], errors='coerce')
            df['cf_yield'] = df['经营现金流'] / df['总市值']
        
        # 去极值处理
        df['log_pe'] = self.winsorize(df['log_pe'], method='quantile')
        df['log_pb'] = self.winsorize(df['log_pb'], method='quantile')
        if 'log_ev_ebitda' in df.columns:
            df['log_ev_ebitda'] = self.winsorize(df['log_ev_ebitda'], method='quantile')
        if 'log_ps' in df.columns:
            df['log_ps'] = self.winsorize(df['log_ps'], method='quantile')
        if 'cf_yield' in df.columns:
            df['cf_yield'] = self.winsorize(df['cf_yield'], method='quantile')
        
        # 计算价值因子
        value_factors = []
        
        # 基本价值因子
        df['value_pe'] = -df['log_pe']
        df['value_pb'] = -df['log_pb']
        value_factors.extend(['value_pe', 'value_pb'])
        
        # 扩展价值因子
        if 'log_ev_ebitda' in df.columns:
            df['value_ev_ebitda'] = -df['log_ev_ebitda']
            value_factors.append('value_ev_ebitda')
        
        if 'log_ps' in df.columns:
            df['value_ps'] = -df['log_ps']
            value_factors.append('value_ps')
        
        if 'cf_yield' in df.columns:
            df['value_cf'] = df['cf_yield']
            value_factors.append('value_cf')
        
        # 市值中性化
        for factor in value_factors:
            if 'log_mktcap' in df.columns:
                df[factor] = self.size_neutralize(df, factor)
        
        # 正交化降冗余
        if len(value_factors) > 1:
            primary_factor = value_factors[0]
            for factor in value_factors[1:]:
                df[factor] = self.orthogonalize_factors(df, primary_factor, factor)
        
        # 计算综合价值因子
        df['value_raw'] = df[value_factors].mean(axis=1)
        
        # 行业中性化
        if '行业' in df.columns and df['行业'].notna().any():
            df['value'] = self.industry_neutralize(df, 'value_raw')
        else:
            df['value'] = df['value_raw']
        
        print(f"✅ 价值因子计算完成，使用了 {len(value_factors)} 个价值指标")
        
        # 计算质量因子
        quality_components = []
        
        # ROE
        if 'ROE' in df.columns:
            df['ROE'] = pd.to_numeric(df['ROE'], errors='coerce')
            df['ROE_clean'] = self.winsorize(df['ROE'], method='quantile')
            quality_components.append('ROE_clean')
        
        # 毛利率
        if '毛利率' in df.columns:
            df['毛利率'] = pd.to_numeric(df['毛利率'], errors='coerce')
            df['毛利率_clean'] = self.winsorize(df['毛利率'], method='quantile')
            quality_components.append('毛利率_clean')
        
        # 资产负债率（取负值）
        if '资产负债率' in df.columns:
            df['资产负债率'] = pd.to_numeric(df['资产负债率'], errors='coerce')
            df['资产负债率_clean'] = -self.winsorize(df['资产负债率'], method='quantile')
            quality_components.append('资产负债率_clean')
        
        # ROE波动率（如果有数据）
        if 'ROE波动率' in df.columns:
            df['ROE波动率'] = pd.to_numeric(df['ROE波动率'], errors='coerce')
            df['ROE波动率_clean'] = -self.winsorize(df['ROE波动率'], method='quantile')
            quality_components.append('ROE波动率_clean')
        
        # 计算质量因子
        if quality_components:
            # 市值中性化
            for component in quality_components:
                if 'log_mktcap' in df.columns:
                    df[component] = self.size_neutralize(df, component)
            
            # 计算综合质量因子
            df['quality_raw'] = df[quality_components].mean(axis=1)
            
            # 行业中性化
            if '行业' in df.columns and df['行业'].notna().any():
                df['quality'] = self.industry_neutralize(df, 'quality_raw')
            else:
                df['quality'] = df['quality_raw']
        else:
            # 如果没有质量因子数据，使用ROE作为默认
            df['quality'] = 0.0
            if 'ROE' in df.columns:
                df['ROE'] = pd.to_numeric(df['ROE'], errors='coerce')
                df['ROE_clean'] = self.winsorize(df['ROE'], method='quantile')
                if 'log_mktcap' in df.columns:
                    df['ROE_clean'] = self.size_neutralize(df, 'ROE_clean')
                if '行业' in df.columns and df['行业'].notna().any():
                    df['quality'] = self.industry_neutralize(df, 'ROE_clean')
                else:
                    df['quality'] = df['ROE_clean']
        
        print(f"✅ 质量因子计算完成，使用了 {len(quality_components)} 个质量指标")
        
        # 计算成长因子
        growth_components = []
        
        # 营收同比
        if '营收同比' in df.columns:
            df['营收同比'] = pd.to_numeric(df['营收同比'], errors='coerce')
            # 对负值做分位截断
            neg_mask = df['营收同比'] < 0
            if neg_mask.any():
                q25 = df.loc[neg_mask, '营收同比'].quantile(0.25)
                df.loc[neg_mask, '营收同比'] = df.loc[neg_mask, '营收同比'].clip(lower=q25)
            df['营收同比_clean'] = self.winsorize(df['营收同比'], method='quantile')
            growth_components.append('营收同比_clean')
        
        # 净利润同比
        if '净利润同比' in df.columns:
            df['净利润同比'] = pd.to_numeric(df['净利润同比'], errors='coerce')
            # 对负值做分位截断
            neg_mask = df['净利润同比'] < 0
            if neg_mask.any():
                q25 = df.loc[neg_mask, '净利润同比'].quantile(0.25)
                df.loc[neg_mask, '净利润同比'] = df.loc[neg_mask, '净利润同比'].clip(lower=q25)
            df['净利润同比_clean'] = self.winsorize(df['净利润同比'], method='quantile')
            growth_components.append('净利润同比_clean')
        
        # 计算成长因子
        if growth_components:
            # 市值中性化
            for component in growth_components:
                if 'log_mktcap' in df.columns:
                    df[component] = self.size_neutralize(df, component)
            
            # 计算综合成长因子
            df['growth_raw'] = df[growth_components].mean(axis=1)
            
            # 行业中性化
            if '行业' in df.columns and df['行业'].notna().any():
                df['growth'] = self.industry_neutralize(df, 'growth_raw')
            else:
                df['growth'] = df['growth_raw']
        else:
            df['growth'] = 0.0
        
        print(f"✅ 成长因子计算完成，使用了 {len(growth_components)} 个成长指标")
        
        # 因子归一化处理
        def normalize_factor(series):
            """对因子进行rank标准化（百分位秩归一化）"""
            # 计算百分位秩，范围[0, 1]
            rank_pct = series.rank(pct=True)
            # 转换为[-1, 1]范围
            return (rank_pct * 2) - 1
        
        # 对所有因子进行归一化
        df['value_normalized'] = normalize_factor(df['value'])
        df['quality_normalized'] = normalize_factor(df['quality'])
        df['growth_normalized'] = normalize_factor(df['growth'])
        print("✅ 因子rank标准化处理完成")
        
        # 使用静态因子权重
        static_weights = self.factor_weights
        print(f"📊 使用静态因子权重: {static_weights}")
        
        # 计算alpha_score
        try:
            df['alpha_score'] = (
                static_weights.get('value', 0.25) * df['value_normalized'] +
                static_weights.get('quality', 0.50) * df['quality_normalized'] +
                static_weights.get('growth', 0.25) * df['growth_normalized']
            )
            
            # 检查alpha_score的分布
            print(f"✅ alpha_score计算完成，平均值: {df['alpha_score'].mean():.4f}, 标准差: {df['alpha_score'].std():.4f}")
            print(f"📊 alpha_score非空值数量: {len(df[df['alpha_score'].notna()])}")
            
            # 填充缺失值
            if df['alpha_score'].isna().any():
                mean_score = df['alpha_score'].mean()
                df['alpha_score'] = df['alpha_score'].fillna(mean_score)
                print(f"✅ 填充了 {df['alpha_score'].isna().sum()} 个缺失值")
                
        except Exception as e:
            print(f"⚠️ alpha_score计算失败: {e}")
            # 使用简单的替代方法
            df['alpha_score'] = df['value']
            print("✅ 使用value作为alpha_score的替代")
        
        # 计算排名
        try:
            df['alpha_score_rank'] = df['alpha_score'].rank(pct=True, ascending=False)
            print(f"✅ alpha_score_rank计算完成，最小值: {df['alpha_score_rank'].min():.4f}, 最大值: {df['alpha_score_rank'].max():.4f}")
            
            # 检查排名分布
            top_10_percent_count = len(df[df['alpha_score_rank'] <= 0.1])
            print(f"📊 前10%的股票数量: {top_10_percent_count}")
            
        except Exception as e:
            print(f"⚠️ 计算排名时出错: {e}")
            # 使用替代方法计算排名
            df = df.sort_values('alpha_score', ascending=False).reset_index(drop=True)
            df['alpha_score_rank'] = (df.index + 1) / len(df)
            print(f"✅ 使用替代方法计算排名，前10%的股票数量: {len(df[df['alpha_score_rank'] <= 0.1])}")
        
        return df.sort_values('alpha_score', ascending=False)
    
    def find_undervalued_stocks(self, spot_df: pd.DataFrame, financial_df: pd.DataFrame = None, top_percent: float = 0.1) -> pd.DataFrame:
        """找出被低估的股票"""
        
        print(f"\n📊 开始分析 {len(spot_df)} 只股票...")
        
        df_analyzed = self.calculate_alpha_score(spot_df, financial_df)
        
        if df_analyzed is None or df_analyzed.empty:
            print("❌ 没有找到符合条件的股票")
            return None
        
        print(f"✅ 分析完成，共 {len(df_analyzed)} 只股票通过初步筛选")
        
        # 计算符合条件的股票数量
        top_count = int(len(df_analyzed) * top_percent)
        print(f"📈 准备选取前 {top_percent*100:.1f}% 的股票，约 {top_count} 只")
        
        result = df_analyzed[df_analyzed['alpha_score_rank'] <= top_percent].copy()
        
        if result is None or result.empty:
            print("❌ 没有找到符合条件的股票")
            return None
        
        print(f"✅ 成功找到 {len(result)} 只被低估的股票")
        
        return result


def get_fundamental_analyzer():
    """获取基本面分析器"""
    return FundamentalAnalyzer()
