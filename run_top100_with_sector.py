#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
运行基本面分析 - 前100只股票并按板块分类
"""

from modules import get_data_fetcher, get_fundamental_analyzer, get_output_manager
import dashscope
import os
from datetime import datetime

dashscope.api_key = os.getenv('DASHSCOPE_API_KEY', 'sk-a9c52673bdb343cd82fa4f1f89e83fc0')


def infer_stock_sector(stock_info):
    """使用千问推测股票所属板块"""
    if not dashscope.api_key:
        return "其他"
    try:
        prompt = "请基于以下信息推测该股票所属的板块：\n"
        prompt += "股票名称：" + stock_info.get('名称', '') + "\n"
        prompt += "股票代码：" + stock_info.get('代码', '') + "\n\n"

        prompt += "请直接返回一个板块名称，不要有其他说明。\n"
        prompt += "板块名称可以是：半导体、稀土、人工智能、新能源、医药、银行、房地产、消费、科技、金融、周期、电子、计算机、通信、传媒、汽车、军工、农林牧渔、化工、钢铁、有色金属、建筑材料、建筑装饰、电气设备、机械设备、家用电器、纺织服装、轻工制造、食品饮料、医药生物、公用事业、交通运输、商业贸易、非银金融、综合、其他\n\n"
        prompt += "请只返回一个板块名称。"
        
        response = dashscope.Generation.call(
            model="qwen-plus",
            prompt=prompt,
            temperature=0.1,
            max_tokens=20
        )
        
        if response.status_code == 200:
            sector = response.output.text.strip()
            return sector
        else:
            return "其他"
    except Exception:
        return "其他"


def analyze_stock_with_qwen(stock_info):
    """使用千问分析股票"""
    if not dashscope.api_key:
        return "API key not available"
    try:
        prompt = "请基于以下信息对该股票进行分析，限制在200字以内：\n"
        prompt += f"股票代码：{stock_info.get('代码', '')}\n"
        prompt += f"股票名称：{stock_info.get('名称', '')}\n"
        prompt += f"最新价：{stock_info.get('最新价', '')}\n"
        prompt += f"涨跌幅：{stock_info.get('涨跌幅', '')}%\n"
        prompt += f"Alpha分：{stock_info.get('alpha_score', '')}\n"
        prompt += f"行业：{stock_info.get('行业', '未知')}\n"
        prompt += f"市盈率-动态：{stock_info.get('市盈率-动态', '未知')}\n"
        prompt += f"市净率：{stock_info.get('市净率', '未知')}\n"
        prompt += f"ROE：{stock_info.get('ROE', '未知')}%\n\n"
        
        prompt += "请从估值、盈利、成长、投资建议和风险提示等方面进行简要分析，语言专业简洁，控制在200字以内。"
        
        response = dashscope.Generation.call(
            model="qwen-plus",
            prompt=prompt,
            temperature=0.3,
            max_tokens=300
        )
        
        if response.status_code == 200:
            analysis = response.output.text.strip()
            return analysis
        else:
            return "分析失败"
    except Exception as e:
        return f"分析异常：{str(e)}"


def run_top100_with_sector(top_percent=0.1):
    """运行基本面分析，获取前100只股票并按板块分类"""
    print("\n" + "=" * 80)
    print("基本面分析 - 前100只股票板块分类")
    print("增强版多因子Alpha框架")
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
    
    if result is None or result.empty:
        return None
    
    top_100 = result.head(100)
    print(f"\n共获取前 {len(top_100)} 只股票")
    
    print("\n开始用千问推测股票板块...")
    stock_sectors = {}
    
    for i, (_, row) in enumerate(top_100.iterrows(), 1):
        stock_info = {'代码': row['代码'], '名称': row['名称']}
        print(f"  [{i}/100] {row['代码']} {row['名称']}...", end='\r')
        sector = infer_stock_sector(stock_info)
        stock_sectors[row['代码']] = sector
    
    print("\n板块推测完成")
    
    print("\n按板块分类股票...")
    sector_stocks = {}
    
    for _, row in top_100.iterrows():
        code = row['代码']
        sector = stock_sectors.get(code, '其他')
        if sector not in sector_stocks:
            sector_stocks[sector] = []
        sector_stocks[sector].append(row)
    
    # 对每个板块的top1股票进行千问分析
    print("\n开始分析每个板块的top1股票...")
    sector_analyses = {}
    
    for sector in sorted(sector_stocks.keys()):
        stocks = sector_stocks[sector]
        if stocks:
            top_stock = stocks[0]
            stock_info = {
                '代码': top_stock['代码'],
                '名称': top_stock['名称'],
                '最新价': top_stock['最新价'],
                '涨跌幅': top_stock['涨跌幅'],
                'alpha_score': top_stock['alpha_score'],
                '行业': sector,
                '市盈率-动态': top_stock.get('市盈率-动态', '未知'),
                '市净率': top_stock.get('市净率', '未知'),
                'ROE': top_stock.get('ROE', '未知')
            }
            print(f"  分析 {sector} 板块 top1: {top_stock['代码']} {top_stock['名称']}...")
            analysis = analyze_stock_with_qwen(stock_info)
            sector_analyses[sector] = analysis
    
    print("\n" + "=" * 120)
    print("前100只股票板块分类".center(100))
    print("=" * 120)
    
    for sector in sorted(sector_stocks.keys()):
        stocks = sector_stocks[sector]
        print(f"\n{sector} (共{len(stocks)}只)")
        print("-" * 120)
        for i, stock in enumerate(stocks, 1):
            print(f"  {i:2d}. {stock['代码']:10s} {stock['名称']:12s} 最新价:{stock['最新价']:8.2f} 涨跌幅:{stock['涨跌幅']:+8.2f}% Alpha分:{stock['alpha_score']:6.2f}")
    
    print("\n" + "=" * 120)
    print(f"\n板块分类完成，共 {len(sector_stocks)} 个板块")
    
    # 生成HTML报告
    generate_html_report(top_100, sector_stocks, sector_analyses, analyzer.factor_weights)
    
    return result


def generate_html_report(top_100, sector_stocks, sector_analyses, factor_weights):
    """生成HTML报告"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"top100_stocks_by_sector_{timestamp}.html"
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>前100只股票板块分类分析报告</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #333;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e0e0e0;
        }}
        .summary {{ 
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        .sector {{ 
            margin-bottom: 40px;
            padding: 20px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }}
        .sector h3 {{ 
            color: #0066cc;
            margin-top: 0;
        }}
        table {{ 
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{ 
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{ 
            background-color: #f2f2f2;
            font-weight: bold;
        }}
        .analysis {{ 
            margin-top: 20px;
            padding: 15px;
            background-color: #f0f8ff;
            border-left: 4px solid #0066cc;
            white-space: pre-wrap;
        }}
        .factor-info {{ 
            margin-top: 40px;
            padding: 20px;
            background-color: #f9f9f9;
            border-radius: 5px;
        }}
        .footer {{ 
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>前100只股票板块分类分析报告</h1>
            <p>生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
            <p>基于增强版多因子Alpha框架</p>
        </div>
        
        <div class="summary">
            <h2>📊 分析概要</h2>
            <p>共分析了5000只A股股票，筛选出前100只被低估的股票</p>
            <p>按板块分类：共{len(sector_stocks)}个板块</p>
            <p>因子权重：价值={factor_weights.get('value', 0)*100}%，质量={factor_weights.get('quality', 0)*100}%，成长={factor_weights.get('growth', 0)*100}%</p>
        </div>
    """
    
    # 添加每个板块的内容
    for sector in sorted(sector_stocks.keys()):
        stocks = sector_stocks[sector]
        analysis = sector_analyses.get(sector, "暂无分析")
        
        html_content += f"""
        <div class="sector">
            <h3>{sector} (共{len(stocks)}只)</h3>
            <table>
                <tr>
                    <th>排名</th>
                    <th>代码</th>
                    <th>名称</th>
                    <th>最新价</th>
                    <th>涨跌幅</th>
                    <th>Alpha分</th>
                </tr>
        """
        
        for i, stock in enumerate(stocks, 1):
            html_content += f"""
                <tr>
                    <td>{i}</td>
                    <td>{stock['代码']}</td>
                    <td>{stock['名称']}</td>
                    <td>{stock['最新价']:.2f}</td>
                    <td>{stock['涨跌幅']:+.2f}%</td>
                    <td>{stock['alpha_score']:.2f}</td>
                </tr>
            """
        
        html_content += f"""
            </table>
            <div class="analysis">
                <h4>🤖 千问AI分析（{stocks[0]['代码']} {stocks[0]['名称']}）</h4>
                <p>{analysis}</p>
            </div>
        </div>
        """
    
    # 添加因子信息和页脚
    html_content += f"""
        <div class="factor-info">
            <h2>🔧 模型框架说明</h2>
            <p><strong>增强版多因子Alpha框架</strong></p>
            <ul>
                <li>因子权重: 价值={factor_weights.get('value', 0)*100}%, 质量={factor_weights.get('quality', 0)*100}%, 成长={factor_weights.get('growth', 0)*100}%</li>
                <li>所有因子先做行业内Z-score标准化</li>
                <li>去极值处理（1%-99%分位截尾）</li>
                <li>市值中性化：对因子做市值回归取残差</li>
                <li>负增长给予1.5倍惩罚以避免价值陷阱</li>
                <li>过滤成分股&lt;5只的小样本行业</li>
                <li>最终按Alpha评分排序，选取行业中性前10%</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>报告生成时间：{datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}</p>
            <p>基于多因子Alpha框架分析</p>
        </div>
    </div>
</body>
</html>
        """
    
    # 写入HTML文件
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n✅ HTML报告已生成: {filename}")
    print("💡 提示: 请用浏览器打开此HTML文件查看")


if __name__ == "__main__":
    run_top100_with_sector(top_percent=0.1)
