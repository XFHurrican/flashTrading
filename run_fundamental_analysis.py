#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行基本面分析 - 标准多因子Alpha框架
"""

from typing import Hashable


from pandas.core.series import Series


from modules import (
    get_data_fetcher,
    get_fundamental_analyzer,
    get_output_manager
)


def run_fundamental_analysis(top_percent: float = 0.1):
    """运行基本面分析"""
    print("\n" + "=" * 80)
    print("📊 基本面分析 - 寻找被低估的股票")
    print("📈 增强版多因子Alpha框架")
    print("=" * 80)
    
    data_fetcher = get_data_fetcher()
    analyzer = get_fundamental_analyzer()
    output = get_output_manager()
    
    spot_df = data_fetcher.get_stock_spot_data()
    
    if spot_df is None:
        return None
    
    financial_df = data_fetcher.get_financial_data()
    
    result = analyzer.find_undervalued_stocks(
        spot_df=spot_df,
        financial_df=financial_df,
        top_percent=top_percent
    )
    
    if result is not None and not result.empty:
        output.print_fundamental_result(result, top_percent)
        
        # 使用千问分析前20只股票
        print("\n" + "=" * 120)
        print("🤖 千问AI分析".center(80))
        print("=" * 120)
        
        ai_analyses = {}
        top_5 = result.head(5)
        for i, (_, row) in enumerate[tuple[Hashable, Series]](top_5.iterrows(), 1):
            stock_info = {
                '代码': row['代码'],
                '名称': row['名称'],
                '行业': row.get('行业', ''),
                '最新价': row['最新价'],
                '涨跌幅': row['涨跌幅'],
                '市盈率-动态': row.get('市盈率-动态', ''),
                '市净率': row.get('市净率', ''),
                'ROE': row.get('ROE', ''),
                'alpha_score': row['alpha_score'],
                'value': row.get('value', ''),
                'growth': row.get('growth', ''),
                'quality': row.get('quality', '')
            }
            
            print(f"\n{i}. {row['代码']} {row['名称']}")
            print("-" * 60)
            analysis = output.analyze_stock_with_qwen(stock_info)
            print(analysis)
            ai_analyses[row['代码']] = analysis
        
        output.print_fundamental_info(analyzer.factor_weights)
        output.generate_fundamental_html_report(
            result,
            factor_weights=analyzer.factor_weights,
            ai_analyses=ai_analyses
        )
    
    return result


if __name__ == "__main__":
    run_fundamental_analysis(top_percent=0.1)
