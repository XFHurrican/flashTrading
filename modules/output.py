#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
输出模块 - 结果展示和报告生成
"""

from datetime import datetime
import pandas as pd
import numpy as np


class OutputManager:
    """输出管理类"""
    
    @staticmethod
    def print_fundamental_result(result_df: pd.DataFrame, top_percent: float = 0.1):
        """打印基本面分析结果"""
        
        if result_df is None or result_df.empty:
            return
        
        print("\n" + "=" * 120)
        print(f"🏆 被低估股票推荐 - 前{top_percent*100:.0f}% (共{len(result_df)}只)")
        print("=" * 120)
        
        print(f"\n{'排名':<6} {'代码':<10} {'名称':<12} {'行业':<15} {'最新价':<10} {'涨跌幅':<10} {'PE':<10} {'PB':<10} {'ROE':<10} {'Alpha分':<10} {'价值分':<10} {'成长分':<10} {'质量分':<10}")
        print("-" * 120)
        
        for i, (_, row) in enumerate(result_df.iterrows(), 1):
            pe = row.get('市盈率-动态', np.nan)
            pb = row.get('市净率', np.nan)
            roe = row.get('ROE', np.nan)
            
            pe_str = f"{pe:.2f}" if pd.notna(pe) and pe < 999 else "-"
            pb_str = f"{pb:.2f}" if pd.notna(pb) and pb < 999 else "-"
            roe_str = f"{roe:.2f}%" if pd.notna(roe) else "-"
            
            industry = row.get('行业', '-')
            
            print(
                f"{i:<6} "
                f"{row['代码']:<10} "
                f"{row['名称']:<12} "
                f"{industry:<15} "
                f"{row['最新价']:<10.2f} "
                f"{row['涨跌幅']:+.2f}%  "
                f"{pe_str:<10} "
                f"{pb_str:<10} "
                f"{roe_str:<10} "
                f"{row['alpha_score']:<10.2f} "
                f"{row['value_score']:<10.2f} "
                f"{row['growth_score']:<10.2f} "
                f"{row['quality_score']:<10.2f}"
            )
        
        print("\n" + "=" * 120)
    
    @staticmethod
    def print_fundamental_info(factor_weights: dict):
        """打印模型信息"""
        print("\n📊 模型框架说明:")
        print("  【标准多因子Alpha框架】")
        print(f"  因子权重: PE={factor_weights['value_pe']:.0%}, PB={factor_weights['value_pb']:.0%}, ")
        print(f"            营收增长={factor_weights['growth_revenue']:.0%}, 利润增长={factor_weights['growth_profit']:.0%}, ")
        print(f"            ROE={factor_weights['quality_roe']:.0%}")
        print("  - 所有因子先做行业内Z-score标准化")
        print("  - 去极值处理（1%-99%分位截尾）")
        print("  - 负增长给予1.5倍惩罚以避免价值陷阱")
        print("  - 过滤成分股<5只的小样本行业")
        print("  - 最终按Alpha评分排序，选取行业中性前10%")
    
    @staticmethod
    def generate_fundamental_html_report(df: pd.DataFrame, filename: str = None, factor_weights: dict = None):
        """生成HTML报告"""
        if df is None or df.empty:
            print("❌ 没有数据可生成报告")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"undervalued_stocks_{timestamp}.html"
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>被低估股票分析报告 - 多因子Alpha框架</title>
    <style>
        body {{
            font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
        }}
        h2 {{
            color: #2980b9;
            margin-top: 40px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #27ae60;
            margin-top: 25px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            font-size: 11px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 6px;
            text-align: center;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        tr:hover {{
            background-color: #e9ecef;
        }}
        .positive {{
            color: #27ae60;
            font-weight: bold;
        }}
        .negative {{
            color: #e74c3c;
            font-weight: bold;
        }}
        .summary {{
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .disclaimer {{
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin-top: 40px;
            color: #856404;
        }}
        .indicator-section {{
            margin: 15px 0;
            padding: 15px;
            background-color: #ffffff;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }}
        .weight-table {{
            font-size: 13px;
        }}
    </style>
</head>
<body>
    <h1>📊 被低估股票分析报告</h1>
    <h2 style="text-align: center; border: none;">标准多因子Alpha框架</h2>
    
    <div class="summary">
        <h3>📋 报告概览</h3>
        <p><strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>推荐股票数:</strong> {len(df)}</p>
        <p>📈 行业内标准化 + 线性加权Alpha模型</p>
    </div>
    
    <h2>🏆 被低估股票推荐</h2>
    <table>
        <thead>
            <tr>
                <th>排名</th>
                <th>代码</th>
                <th>名称</th>
                <th>行业</th>
                <th>最新价</th>
                <th>涨跌幅</th>
                <th>PE</th>
                <th>PB</th>
                <th>ROE</th>
                <th>Alpha分</th>
                <th>价值分</th>
                <th>成长分</th>
                <th>质量分</th>
            </tr>
        </thead>
        <tbody>
"""
        
        for i, (_, row) in enumerate(df.iterrows(), 1):
            pe = row.get('市盈率-动态', np.nan)
            pb = row.get('市净率', np.nan)
            roe = row.get('ROE', np.nan)
            
            pe_str = f"{pe:.2f}" if pd.notna(pe) and pe < 999 else "-"
            pb_str = f"{pb:.2f}" if pd.notna(pb) and pb < 999 else "-"
            roe_str = f"{roe:.2f}%" if pd.notna(roe) else "-"
            
            industry = row.get('行业', '-')
            change_class = 'positive' if row['涨跌幅'] >= 0 else 'negative'
            
            html += f"""
            <tr>
                <td>{i}</td>
                <td>{row['代码']}</td>
                <td>{row['名称']}</td>
                <td>{industry}</td>
                <td>{row['最新价']:.2f}</td>
                <td class="{change_class}">{row['涨跌幅']:+.2f}%</td>
                <td>{pe_str}</td>
                <td>{pb_str}</td>
                <td>{roe_str}</td>
                <td>{row['alpha_score']:.2f}</td>
                <td>{row['value_score']:.2f}</td>
                <td>{row['growth_score']:.2f}</td>
                <td>{row['quality_score']:.2f}</td>
            </tr>
"""
        
        html += """
        </tbody>
    </table>
    
    <h2>📊 模型框架说明</h2>
    
    <div class="summary">
        <div class="indicator-section">
            <h3>🎯 因子权重配置</h3>
            <table class="weight-table">
                <thead>
                    <tr>
                        <th>因子类别</th>
                        <th>因子</th>
                        <th>权重</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td rowspan="2"><strong>价值因子</strong></td>
                        <td>PE (对数)</td>
                        <td>28%</td>
                        <td>行业内分位数标准化，低PE为优</td>
                    </tr>
                    <tr>
                        <td>PB (对数)</td>
                        <td>28%</td>
                        <td>行业内分位数标准化，低PB为优</td>
                    </tr>
                    <tr>
                        <td rowspan="2"><strong>成长因子</strong></td>
                        <td>营收同比增长</td>
                        <td>17%</td>
                        <td>负增长1.5倍惩罚</td>
                    </tr>
                    <tr>
                        <td>净利润同比增长</td>
                        <td>17%</td>
                        <td>负增长1.5倍惩罚</td>
                    </tr>
                    <tr>
                        <td><strong>盈利质量</strong></td>
                        <td>ROE</td>
                        <td>10%</td>
                        <td>行业内标准化</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="indicator-section">
            <h3>🔧 数据预处理</h3>
            <ul>
                <li><strong>去极值:</strong> 1%-99%分位截尾，减少异常值影响</li>
                <li><strong>行业中性化:</strong> 所有因子在行业内做Z-score标准化</li>
                <li><strong>小样本过滤:</strong> 剔除成分股&lt;5只的行业</li>
                <li><strong>价值陷阱防护:</strong> 负增长给予1.5倍惩罚</li>
            </ul>
        </div>
        
        <div class="indicator-section">
            <h3>📊 Alpha评分计算</h3>
            <p>Alpha = 0.28×PE因子 + 0.28×PB因子 + 0.17×营收增长 + 0.17×利润增长 + 0.10×ROE</p>
            <p>最终选取Alpha评分前10%的股票</p>
        </div>
    </div>
    
    <div class="disclaimer">
        <h3>⚠️  免责声明</h3>
        <p>本报告仅供学习参考，不构成任何投资建议！</p>
        <p>股市有风险，投资需谨慎。</p>
    </div>
</body>
</html>
"""
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ HTML报告已生成: {filename}")
        print(f"💡 提示: 请用浏览器打开此HTML文件查看")
        
        return filename


def get_output_manager():
    """获取输出管理器"""
    return OutputManager()
