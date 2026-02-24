#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
输出模块 - 结果展示和报告生成
"""

from datetime import datetime
import pandas as pd
import numpy as np
import dashscope
import os

# 初始化千问
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-a9c52673bdb343cd82fa4f1f89e83fc0')  # 设置API密钥


class OutputManager:
    """输出管理类"""
    
    @staticmethod
    def print_fundamental_result(result_df: pd.DataFrame, top_percent: float = 0.1):
        """打印基本面分析结果"""
        
        if result_df is None or result_df.empty:
            return
        
        # 只取前5只
        top_5_df = result_df.head(5)
        
        print("\n" + "=" * 120)
        print(f"🏆 综合股票推荐 - 前5名 (共{len(result_df)}只)")
        print("=" * 120)
        
        print(f"\n{'排名':<6} {'代码':<10} {'名称':<12} {'行业':<15} {'最新价':<10} {'涨跌幅':<10} {'PE':<10} {'PB':<10} {'ROE':<10} {'Alpha分':<10} {'价值分':<10} {'成长分':<10} {'质量分':<10}")
        print("-" * 120)
        
        for i, (_, row) in enumerate(top_5_df.iterrows(), 1):
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
                f"{row.get('value', np.nan):<10.2f} "
                f"{row.get('growth', np.nan):<10.2f} "
                f"{row.get('quality', np.nan):<10.2f}"
            )
        
        print("\n" + "=" * 120)
    
    @staticmethod
    def analyze_stock_with_qwen(stock_info: dict) -> str:
        """
        使用千问分析股票
        """
        if not dashscope.api_key:
            return "⚠️ 千问API密钥未配置，无法提供分析"
        
        try:
            prompt = f"""
            请基于以下信息分析股票：
            股票名称：{stock_info.get('名称', '')}
            股票代码：{stock_info.get('代码', '')}
            所属行业：{stock_info.get('行业', '')}
            最新价格：{stock_info.get('最新价', '')}
            涨跌幅：{stock_info.get('涨跌幅', '')}%
            市盈率（动态）：{stock_info.get('市盈率-动态', '')}
            市净率：{stock_info.get('市净率', '')}
            ROE：{stock_info.get('ROE', '')}%
            Alpha总分：{stock_info.get('alpha_score', '')}
            价值分：{stock_info.get('value', '')}
            成长分：{stock_info.get('growth', '')}
            质量分：{stock_info.get('quality', '')}
            
            请从以下几个方面分析：
            1. 估值分析：基于PE、PB等指标
            2. 盈利能力：基于ROE等指标
            3. 成长性：基于成长分
            4. 投资建议：短期和中长期
            5. 风险提示
            
            分析要简洁明了，直接给出结论，不需要引言。
            """
            
            response = dashscope.Generation.call(
                model="qwen-plus",
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            if response.status_code == 200:
                return response.output.text.strip()
            else:
                return f"⚠️ 千问分析失败：{response.message}"
        except Exception as e:
            return f"⚠️ 千问分析异常：{str(e)}"
    
    @staticmethod
    def print_fundamental_info(factor_weights: dict):
        """打印模型信息"""
        print("\n📊 模型框架说明:")
        print("  【增强版多因子Alpha框架】")
        print(f"  因子权重: 价值={factor_weights.get('value', 0):.0%}, 质量={factor_weights.get('quality', 0):.0%}, 成长={factor_weights.get('growth', 0):.0%}")
        print("  - 所有因子先做行业内Z-score标准化")
        print("  - 去极值处理（1%-99%分位截尾）")
        print("  - 市值中性化：对因子做市值回归取残差")
        print("  - 负增长给予1.5倍惩罚以避免价值陷阱")
        print("  - 过滤成分股<5只的小样本行业")
        print("  - 最终按Alpha评分排序，选取行业中性前10%")
    
    @staticmethod
    def generate_fundamental_html_report(df: pd.DataFrame, filename: str = None, factor_weights: dict = None, ai_analyses: dict = None):
        """生成HTML报告"""
        if df is None or df.empty:
            print("❌ 没有数据可生成报告")
            return None
        
        # 只取前5只股票
        top_5_df = df.head(5)
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"undervalued_stocks_{timestamp}.html"
        
        # 使用普通字符串构建HTML，避免f-string的大括号转义问题
        html = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>被低估股票分析报告 - 增强版多因子Alpha框架</title>
    <style>
        body {
            font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 20px;
        }
        h2 {
            color: #2980b9;
            margin-top: 40px;
            border-left: 5px solid #3498db;
            padding-left: 15px;
        }
        h3 {
            color: #27ae60;
            margin-top: 25px;
        }
        h4 {
            color: #e67e22;
            margin-top: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            font-size: 11px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 6px;
            text-align: center;
        }
        th {
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        tr:hover {
            background-color: #e9ecef;
        }
        .positive {
            color: #27ae60;
            font-weight: bold;
        }
        .negative {
            color: #e74c3c;
            font-weight: bold;
        }
        .summary {
            background-color: #f0f7ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .disclaimer {
            background-color: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin-top: 40px;
            color: #856404;
        }
        .indicator-section {
            margin: 15px 0;
            padding: 15px;
            background-color: #ffffff;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        .weight-table {
            font-size: 13px;
        }
        .ai-analysis {
            background-color: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin: 15px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        .ai-analysis h4 {
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 15px;
        }
        .ai-analysis p {
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <h1>📊 被低估股票分析报告</h1>
    <h2 style="text-align: center; border: none;">增强版多因子Alpha框架</h2>
    
    <div class="summary">
        <h3>📋 报告概览</h3>
        <p><strong>生成时间:</strong> ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
        <p><strong>推荐股票数:</strong> ''' + str(len(df)) + '''</p>
        <p><strong>报告显示:</strong> 排名前5的股票</p>
        <p>📈 行业内标准化 + 市值中性化 + 线性加权Alpha模型</p>
        <p>🤖 千问AI智能分析</p>
    </div>
    
    <h2>🏆 被低估股票推荐 (前5名)</h2>
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
'''
        
        for i, (_, row) in enumerate(top_5_df.iterrows(), 1):
            pe = row.get('市盈率-动态', np.nan)
            pb = row.get('市净率', np.nan)
            roe = row.get('ROE', np.nan)
            
            pe_str = f"{pe:.2f}" if pd.notna(pe) and pe < 999 else "-"
            pb_str = f"{pb:.2f}" if pd.notna(pb) and pb < 999 else "-"
            roe_str = f"{roe:.2f}%" if pd.notna(roe) else "-"
            
            industry = row.get('行业', '-')
            change_class = 'positive' if row['涨跌幅'] >= 0 else 'negative'
            
            value_score = row.get('value', np.nan)
            growth_score = row.get('growth', np.nan)
            quality_score = row.get('quality', np.nan)
            
            html += f'''
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
                <td>{value_score:.2f}</td>
                <td>{growth_score:.2f}</td>
                <td>{quality_score:.2f}</td>
            </tr>
'''
        
        html += '''
        </tbody>
    </table>
    
    <h2>🤖 千问AI智能分析</h2>
    
'''
        
        # 添加千问AI分析结果
        if ai_analyses:
            # 只分析前5只股票
            top_5_codes = [row['代码'] for _, row in top_5_df.iterrows()]
            for stock_code, analysis in ai_analyses.items():
                if stock_code in top_5_codes:
                    stock_name = ""
                    # 查找股票名称
                    for _, row in top_5_df.iterrows():
                        if row['代码'] == stock_code:
                            stock_name = row['名称']
                            break
                    
                    if stock_name:
                        html += f'''
    <div class="ai-analysis">
        <h4>{stock_code} {stock_name}</h4>
        <p>{analysis.replace('\n', '<br>')}</p>
    </div>
'''
        
        # 模型框架说明部分
        html += '''
    <h2>📊 模型框架说明</h2>
    
    <div class="summary">
        <div class="indicator-section">
            <h3>🎯 因子权重配置</h3>
            <table class="weight-table">
                <thead>
                    <tr>
                        <th>因子类别</th>
                        <th>权重</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td><strong>价值因子</strong></td>
                        <td>动态</td>
                        <td>PE、PB、EV/EBITDA、PS、CF yield，正交化降冗余</td>
                    </tr>
                    <tr>
                        <td><strong>质量因子</strong></td>
                        <td>动态</td>
                        <td>ROE+毛利率−资产负债率−ROE波动率</td>
                    </tr>
                    <tr>
                        <td><strong>成长因子</strong></td>
                        <td>动态</td>
                        <td>营收和利润增长，负值做分位截断</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <div class="indicator-section">
            <h3>🔧 数据预处理流程</h3>
            <ul>
                <li><strong>1. 去极值:</strong> 1%-99%分位截尾，减少异常值影响</li>
                <li><strong>2. 市值中性化:</strong> 对因子做市值回归取残差，剥离市值影响</li>
                <li><strong>3. 行业中性化:</strong> 所有因子在行业内做Z-score标准化</li>
                <li><strong>4. 因子正交化:</strong> 价值因子间正交化降冗余</li>
                <li><strong>5. 小样本过滤:</strong> 剔除成分股&lt;5只的行业</li>
            </ul>
        </div>
        
        <div class="indicator-section">
            <h3>📊 动态权重与评分计算</h3>
            <ul>
                <li><strong>滚动IC检验:</strong> 对单因子做滚动IC与IC_IR检验</li>
                <li><strong>动态权重:</strong> 使用滚动IC或风险平价法动态确定权重</li>
                <li><strong>Alpha评分:</strong> 基于动态权重加权计算综合Alpha评分</li>
                <li><strong>选股策略:</strong> 最终选取Alpha评分排名靠前的股票</li>
            </ul>
        </div>
    </div>
    
    <div class="disclaimer">
        <h3>⚠️  免责声明</h3>
        <p>本报告仅供学习参考，不构成任何投资建议！</p>
        <p>股市有风险，投资需谨慎。</p>
    </div>
</body>
</html>
'''
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"\n✅ HTML报告已生成: {filename}")
        print(f"💡 提示: 请用浏览器打开此HTML文件查看")
        
        return filename


def get_output_manager():
    """获取输出管理器"""
    return OutputManager()
