#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行基本面分析 - 标准多因子Alpha框架
"""

from modules import (
    get_data_fetcher,
    get_fundamental_analyzer,
    get_output_manager
)


def run_fundamental_analysis(top_percent: float = 0.1):
    """运行基本面分析"""
    print("\n" + "=" * 80)
    print("📊 基本面分析 - 寻找被低估的股票")
    print("📈 标准多因子Alpha框架")
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
        output.print_fundamental_info(analyzer.factor_weights)
        output.generate_fundamental_html_report(
            result,
            factor_weights=analyzer.factor_weights
        )
    
    return result


if __name__ == "__main__":
    run_fundamental_analysis(top_percent=0.1)
