#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A股短线交易系统 - 整合版
1. 回测找出最佳策略
2. 用最佳策略推荐今日股票
"""

import sys
from datetime import datetime, timedelta

from short_term_trading import (
    get_data_fetcher,
    get_all_algorithms,
    get_all_advanced_algorithms,
    BacktestEngine
)


def find_best_strategy(
    data_fetcher,
    stock_codes,
    start_date,
    end_date,
    top_n=10
):
    """回测找出最佳策略"""
    print("\n" + "=" * 80)
    print("🔬 第一阶段：回测找出最佳策略")
    print("=" * 80)
    
    basic_algorithms = get_all_algorithms()
    advanced_algorithms = get_all_advanced_algorithms()
    all_algorithms = basic_algorithms + advanced_algorithms
    
    print(f"\n共 {len(all_algorithms)} 种算法:")
    for i, algo in enumerate(all_algorithms, 1):
        print(f"  {i}. {algo.name}")
    
    print(f"\n股票数量: {len(stock_codes)}")
    print(f"回测时段: {start_date} 至 {end_date}")
    
    engine = BacktestEngine(data_fetcher, initial_capital=100000)
    
    results = []
    for algorithm in all_algorithms:
        print(f"\n--- 测试: {algorithm.name} ---")
        try:
            result = engine.run_backtest(
                algorithm=algorithm,
                stock_codes=stock_codes,
                start_date=start_date,
                end_date=end_date,
                top_n=top_n
            )
            results.append(result)
        except Exception as e:
            print(f"❌ 算法 {algorithm.name} 测试失败: {e}")
    
    print("\n" + "=" * 80)
    print("📊 回测结果总结")
    print("=" * 80)
    
    print(f"\n{'算法名称':<25} {'胜率':<10} {'总收益率':<12} {'年化收益':<12} {'交易次数':<10}")
    print("-" * 85)
    
    valid_results = [r for r in results if r.calculate_statistics()]
    
    for result in valid_results:
        stats = result.calculate_statistics()
        if stats:
            print(
                f"{stats['algorithm']:<25} "
                f"{stats['win_rate']*100:>6.2f}%  "
                f"{stats['total_return']*100:>8.2f}%  "
                f"{stats['annual_return']*100:>8.2f}%  "
                f"{stats['total_trades']:>8}"
            )
    
    print("\n" + "=" * 85)
    
    if valid_results:
        best_by_win = max(valid_results, key=lambda r: r.calculate_statistics().get('win_rate', 0))
        best_by_return = max(valid_results, key=lambda r: r.calculate_statistics().get('total_return', 0))
        
        print(f"\n🏅 按胜率最高: {best_by_win.algorithm_name}")
        print(f"🏅 按收益最高: {best_by_return.algorithm_name}")
        
        if best_by_win.algorithm_name == best_by_return.algorithm_name:
            return best_by_win
        else:
            return best_by_return
    
    return None


def recommend_today_stocks(
    data_fetcher,
    best_algorithm,
    stock_codes,
    top_n=10
):
    """用最佳策略推荐今日股票"""
    print("\n" + "=" * 80)
    print("🎯 第二阶段：今日股票推荐")
    print("=" * 80)
    
    print(f"\n使用策略: {best_algorithm.name}")
    
    try:
        import akshare as ak
        stock_list_df = ak.stock_zh_a_spot_em()
        stock_name_map = {}
        if stock_list_df is not None and not stock_list_df.empty:
            for _, row in stock_list_df.iterrows():
                code = row.get("代码", "")
                name = row.get("名称", "")
                stock_name_map[code] = name
    except Exception as e:
        print(f"获取股票名称失败: {e}")
        stock_name_map = {}
    
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=60)).strftime("%Y%m%d")
    
    print(f"\n数据时段: {start_date} 至 {end_date}")
    
    print("\n正在下载股票数据...")
    stock_data = {}
    for i, code in enumerate(stock_codes):
        if i % 50 == 0:
            print(f"  进度: {i}/{len(stock_codes)}")
        df = data_fetcher.get_stock_historical_data(code, start_date, end_date)
        if df is not None and len(df) > 30:
            stock_data[code] = df
    
    print(f"✅ 成功加载 {len(stock_data)} 只股票数据")
    
    print("\n正在计算股票得分...")
    
    latest_date = None
    for code, df in stock_data.items():
        if not df.empty:
            latest_date = df["日期"].max()
            break
    
    if latest_date is None:
        print("❌ 没有可用数据")
        return
    
    latest_date_str = latest_date.strftime("%Y%m%d")
    print(f"最新交易日: {latest_date_str}")
    
    top_stocks = best_algorithm.select_stocks(stock_data, latest_date_str, top_n=top_n)
    
    print("\n" + "=" * 80)
    print("🏆 推荐结果 - Top 10")
    print("=" * 80)
    
    print(f"\n{'排名':<6} {'代码':<10} {'名称':<10} {'最新价':<10} {'涨跌幅':<10}")
    print("-" * 50)
    
    for i, code in enumerate(top_stocks[:3], 1):
        df = stock_data.get(code)
        name = stock_name_map.get(code, "未知")
        
        latest_price = 0
        change_percent = 0
        
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            latest_price = latest.get("收盘", 0)
            if len(df) >= 2:
                prev = df.iloc[-2]
                prev_close = prev.get("收盘", 0)
                if prev_close > 0:
                    change_percent = (latest_price - prev_close) / prev_close * 100
        
        change_str = f"{change_percent:+.2f}%"
        
        print(f"{i:<6} {code:<10} {name:<10} {latest_price:<10.2f} {change_str:<10}")
    
    print("\n" + "=" * 80)
    print("\n📊 完整Top 10列表:")
    for i, code in enumerate(top_stocks, 1):
        name = stock_name_map.get(code, "未知")
        print(f"  {i}. {code} {name}")


def main():
    print("\n" + "=" * 80)
    print("🚀 A股短线交易系统 - 整合版")
    print("   1. 回测找出最佳策略")
    print("   2. 用最佳策略推荐今日股票")
    print("=" * 80)
    
    data_fetcher = get_data_fetcher()
    
    if not data_fetcher.check_akshare():
        print("\n❌ AKShare 不可用")
        print("请运行: pip install akshare pandas numpy")
        return
    
    print("\n✅ AKShare 可用")
    
    print("\n正在获取股票列表...")
    all_codes = data_fetcher.get_all_stock_codes()
    if not all_codes:
        print("❌ 获取股票列表失败")
        return
    
    print(f"✅ 共获取到 {len(all_codes)} 只A股")
    
    test_codes = all_codes[:100]
    print(f"\n使用前100只股票进行回测和推荐")
    
    end_date = datetime.now().strftime("%Y%m%d")
    bt_start_date = (datetime.now() - timedelta(days=180)).strftime("%Y%m%d")
    
    best_result = find_best_strategy(
        data_fetcher=data_fetcher,
        stock_codes=test_codes,
        start_date=bt_start_date,
        end_date=end_date,
        top_n=8
    )
    
    if best_result is None:
        print("\n❌ 没有找到有效策略")
        return
    
    basic_algorithms = get_all_algorithms()
    advanced_algorithms = get_all_advanced_algorithms()
    all_algorithms = basic_algorithms + advanced_algorithms
    
    best_algo = None
    for algo in all_algorithms:
        if algo.name == best_result.algorithm_name:
            best_algo = algo
            break
    
    if best_algo is None:
        print("\n❌ 找不到最佳策略")
        return
    
    recommend_today_stocks(
        data_fetcher=data_fetcher,
        best_algorithm=best_algo,
        stock_codes=test_codes,
        top_n=10
    )
    
    print("\n" + "=" * 80)
    print("⚠️  免责声明: 本系统仅供学习参考，不构成任何投资建议！")
    print("=" * 80)


if __name__ == "__main__":
    main()
