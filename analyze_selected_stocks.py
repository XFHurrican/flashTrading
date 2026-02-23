#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
分析指定股票的基本面和技术面
"""

from modules import (
    get_data_fetcher,
    get_fundamental_analyzer,
    get_output_manager
)

# 圈住的股票列表
TARGET_STOCKS = [
    ("600633", "浙数文化"),
    ("603296", "华勤技术"),
    ("300547", "川环科技"),
    ("603728", "鸣志电器"),
    ("600410", "华胜天成"),
]


def analyze_target_stocks():
    """分析目标股票"""
    print("=" * 80)
    print("📊 分析指定股票".center(80))
    print("=" * 80)
    
    # 获取数据
    data_fetcher = get_data_fetcher()
    fundamental_analyzer = get_fundamental_analyzer()
    output_manager = get_output_manager()
    
    # 获取实时行情数据
    print("\n📈 获取实时行情数据...")
    spot_df = data_fetcher.get_stock_spot_data()
    
    if spot_df is None or spot_df.empty:
        print("❌ 无法获取实时行情数据")
        return
    
    # 获取财务数据
    print("\n📋 获取财务数据...")
    financial_df = data_fetcher.get_financial_data()
    
    # 计算Alpha得分
    print("\n🧮 计算基本面Alpha得分...")
    alpha_df = fundamental_analyzer.calculate_alpha_score(spot_df, financial_df)
    
    # 筛选目标股票
    print("\n" + "=" * 80)
    print("🎯 目标股票分析结果".center(80))
    print("=" * 80)
    
    target_codes = [code for code, name in TARGET_STOCKS]
    target_df = alpha_df[alpha_df["代码"].isin(target_codes)].copy()
    
    if target_df.empty:
        print("❌ 未找到目标股票数据")
        return
    
    # 按目标列表顺序排序
    target_df["_sort"] = target_df["代码"].apply(lambda x: target_codes.index(x))
    target_df = target_df.sort_values("_sort").drop("_sort", axis=1)
    
    # 显示结果
    display_cols = ["代码", "名称", "最新价", "涨跌幅", "市盈率-动态", "市净率", "alpha_score", "alpha_score_rank"]
    available_cols = [col for col in display_cols if col in target_df.columns]
    
    # 重命名列以便显示
    display_df = target_df[available_cols].copy()
    display_df = display_df.rename(columns={
        "alpha_score": "Alpha总分",
        "alpha_score_rank": "综合排名(%)"
    })
    
    print("\n📋 目标股票详情：")
    print(display_df.to_string(index=False))
    
    # 显示详细因子得分
    print("\n" + "=" * 80)
    print("📊 详细因子得分".center(80))
    print("=" * 80)
    
    factor_cols = ["代码", "名称", "factor_pe", "factor_pb", "factor_growth_revenue", "factor_growth_profit", "factor_quality_roe", "value_score", "growth_score", "quality_score"]
    available_factor_cols = [col for col in factor_cols if col in target_df.columns]
    
    if available_factor_cols:
        factor_df = target_df[available_factor_cols].copy()
        factor_df = factor_df.rename(columns={
            "factor_pe": "PE因子",
            "factor_pb": "PB因子",
            "factor_growth_revenue": "营收增长因子",
            "factor_growth_profit": "利润增长因子",
            "factor_quality_roe": "ROE因子",
            "value_score": "价值得分",
            "growth_score": "成长得分",
            "quality_score": "质量得分"
        })
        
        print("\n📈 因子得分详情：")
        print(factor_df.to_string(index=False))
    else:
        print("\n⚠️ 未找到详细因子数据（可能缺少财务数据）")
    
    print("\n" + "=" * 80)
    print("✅ 分析完成".center(80))
    print("=" * 80)


if __name__ == "__main__":
    analyze_target_stocks()
