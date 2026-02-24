#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
信息获取模块 - 数据获取接口
统一管理所有数据获取功能
"""

import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
import json

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False

try:
    import baostock as bs
    BAOSTOCK_AVAILABLE = True
except ImportError:
    BAOSTOCK_AVAILABLE = False


class DataFetcher:
    """统一数据获取器"""
    
    def __init__(self):
        self.use_real_data = AKSHARE_AVAILABLE or BAOSTOCK_AVAILABLE or True  # 新浪财经API不需要依赖
        self.baostock_logged_in = False
    
    def check_akshare(self) -> bool:
        """检查AKShare是否可用"""
        return AKSHARE_AVAILABLE
    
    def check_baostock(self) -> bool:
        """检查Baostock是否可用"""
        return BAOSTOCK_AVAILABLE
    
    def login_baostock(self) -> bool:
        """登录Baostock"""
        if not BAOSTOCK_AVAILABLE:
            return False
        
        if not self.baostock_logged_in:
            try:
                lg = bs.login()
                if lg.error_code == '0':
                    self.baostock_logged_in = True
                    print("✅ Baostock登录成功")
                    return True
                else:
                    print(f"❌ Baostock登录失败: {lg.error_msg}")
                    return False
            except Exception as e:
                print(f"❌ Baostock登录异常: {e}")
                return False
        return self.baostock_logged_in
    
    def logout_baostock(self) -> None:
        """退出Baostock"""
        if BAOSTOCK_AVAILABLE and self.baostock_logged_in:
            try:
                bs.logout()
                self.baostock_logged_in = False
                print("✅ Baostock退出成功")
            except Exception as e:
                print(f"⚠️ Baostock退出异常: {e}")
    
    def get_all_stock_codes(self) -> Optional[List[str]]:
        """获取所有A股股票代码列表"""
        if not self.use_real_data:
            return None
        
        # 优先使用AKShare
        if AKSHARE_AVAILABLE:
            try:
                stock_list = ak.stock_zh_a_spot_em()
                if stock_list is not None and not stock_list.empty:
                    return stock_list["代码"].tolist()
            except Exception as e:
                print(f"⚠️ AKShare获取股票列表失败: {e}")
        
        # 备选使用Baostock
        if BAOSTOCK_AVAILABLE:
            try:
                if not self.login_baostock():
                    return None
                
                rs = bs.query_stock_basic()
                stock_list = rs.get_data()
                if stock_list is not None and not stock_list.empty:
                    # Baostock代码格式为sh.600000，需要转换为600000
                    codes = []
                    for _, row in stock_list.iterrows():
                        code = row.get('code', '')
                        if code:
                            code = code.split('.')[1]
                            codes.append(code)
                    print(f"✅ Baostock成功获取 {len(codes)} 只股票代码")
                    return codes
            except Exception as e:
                print(f"⚠️ Baostock获取股票列表失败: {e}")
        
        return None
    
    def get_stock_historical_data(
        self, 
        code: str, 
        start_date: str = None, 
        end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据（优先使用东方财富数据）
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
        
        Returns:
            DataFrame包含历史数据
        """
        if not self.use_real_data:
            return None
        
        try:
            if not start_date:
                start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d")
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            
            # 优先使用AKShare的东方财富数据源
            print(f"1️⃣ 尝试使用AKShare获取 {code} 历史数据（东方财富）...")
            stock_data = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if stock_data is not None and not stock_data.empty:
                stock_data["日期"] = pd.to_datetime(stock_data["日期"])
                stock_data = stock_data.sort_values("日期").reset_index(drop=True)
                print(f"✅ 成功获取 {code} 历史数据")
                return stock_data
            
            # 备选：尝试使用东方财富K线API
            print(f"2️⃣ 尝试直接调用东方财富K线API获取 {code} 历史数据...")
            
            # 构建东方财富代码格式
            if code.startswith('6'):
                em_code = f"1.{code}"
            else:
                em_code = f"0.{code}"
            
            url = "http://82.push2his.eastmoney.com/api/qt/stock/kline/get"
            params = {
                'secid': em_code,
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
                'klt': '101',  # 日K线
                'fqt': '1',    # 前复权
                'beg': start_date,
                'end': end_date,
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get('data') and data['data'].get('klines'):
                klines = data['data']['klines']
                historical_data = []
                for kline in klines:
                    parts = kline.split(',')
                    if len(parts) >= 6:
                        historical_data.append({
                            '日期': parts[0],
                            '开盘': float(parts[1]),
                            '收盘': float(parts[2]),
                            '最高': float(parts[3]),
                            '最低': float(parts[4]),
                            '成交量': float(parts[5])
                        })
                
                df = pd.DataFrame(historical_data)
                if not df.empty:
                    df["日期"] = pd.to_datetime(df["日期"])
                    df = df.sort_values("日期").reset_index(drop=True)
                    print(f"✅ 东方财富K线API成功获取 {code} 历史数据")
                    return df
        except Exception as e:
            print(f"获取股票 {code} 历史数据失败: {e}")
            return None
    
    def get_stock_spot_data(self) -> Optional[pd.DataFrame]:
        """获取A股实时行情数据（优先使用雪球数据）"""
        if not self.use_real_data:
            return None
        
        print("📊 开始获取A股数据...")
        
        # 优先使用雪球API
        try:
            print("1️⃣ 尝试使用雪球API...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'https://xueqiu.com/',
                'Accept': 'application/json, text/plain, */*'
            }
            
            # 获取股票列表
            url = "https://xueqiu.com/service/v5/stock/screener/quote/list"
            params = {
                'page': 1,
                'size': 100,
                'order': 'desc',
                'order_by': 'percent',
                'exchange': 'CN',
                'market': 'CN',
                'type': 'stock',
                'country': 'cn'
            }
            
            all_xueqiu_data = []
            page = 1
            while True:
                params['page'] = page
                response = requests.get(url, params=params, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if data and 'data' in data and 'list' in data['data']:
                    stocks = data['data']['list']
                    if not stocks:
                        break
                    
                    for stock in stocks:
                        # 处理股票代码格式，移除市场前缀
                        code = stock.get('symbol', '')
                        # 雪球API的股票代码格式可能是 SZ300164、SH688028 或 SH.600000，需要转换为纯数字格式
                        if '.' in code:
                            code = code.split('.')[1]
                        elif code.startswith('SZ'):
                            code = code[2:]  # 去除SZ前缀
                        elif code.startswith('SH'):
                            code = code[2:]  # 去除SH前缀
                        
                        all_xueqiu_data.append({
                            '代码': code,
                            '名称': stock.get('name', ''),
                            '最新价': stock.get('current', 0),
                            '涨跌幅': stock.get('percent', 0),
                            '市盈率-动态': stock.get('pe_ttm', ''),
                            '市净率': stock.get('pb', ''),
                            '行业': ''
                        })
                    
                    if len(stocks) < 100:
                        break
                    
                    page += 1
                    if page > 100:  # 大幅增加最大页数以获取全部A股
                        break
                else:
                    break
            
            df = pd.DataFrame(all_xueqiu_data)
            if not df.empty:
                print(f"✅ 雪球API成功获取 {len(df)} 只股票数据")
                return df
        except Exception as e:
            print(f"⚠️ 雪球API获取数据失败: {e}")
        
        # 备选：使用AKShare（实际使用的是东方财富数据）
        if AKSHARE_AVAILABLE:
            for attempt in range(3):
                try:
                    print(f"2️⃣ 尝试使用AKShare获取东方财富数据（第{attempt+1}次）...")
                    df = ak.stock_zh_a_spot_em()
                    if df is not None and not df.empty:
                        print(f"✅ 成功获取 {len(df)} 只股票实时数据")
                        return df
                except Exception as e:
                    print(f"⚠️ AKShare获取东方财富数据失败（第{attempt+1}次）: {e}")
                    if attempt < 2:
                        import time
                        time.sleep(2)  # 等待2秒后重试
        
        # 备选：直接调用东方财富API（分页获取所有A股）
        for attempt in range(3):
            try:
                print(f"3️⃣ 尝试直接调用东方财富API（第{attempt+1}次）...")
                
                # 东方财富实时行情API
                url = "http://82.push2.eastmoney.com/api/qt/clist/get"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'http://quote.eastmoney.com/',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9',
                    'Connection': 'keep-alive'
                }
                
                all_spot_data = []
                page_size = 1000
                current_page = 1
                total_pages = 1
                
                print("   开始分页获取所有A股数据...")
                
                while current_page <= total_pages:
                    params = {
                        'pn': current_page,
                        'pz': page_size,
                        'po': 1,
                        'np': 1,
                        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                        'fltt': 2,
                        'invt': 2,
                        'fid': 'f12',
                        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048',
                        'fields': 'f1,f2,f3,f4,f5,f6,f7,f8,f9,f10,f12,f13,f14,f15,f16,f17,f18,f20,f21,f23,f24,f25,f22,f11,f62,f128,f136,f115,f152',
                        '_': int(datetime.now().timestamp() * 1000)
                    }
                    
                    response = requests.get(url, params=params, headers=headers, timeout=20)
                    response.raise_for_status()  # 检查HTTP状态码
                    data = response.json()
                    
                    if data.get('data'):
                        # 获取总页数
                        if 'total' in data['data'] and 'pz' in data['data']:
                            total_count = data['data']['total']
                            total_pages = (total_count + page_size - 1) // page_size
                            print(f"   第{current_page}/{total_pages}页，共{total_count}只股票")
                        
                        # 获取当前页数据
                        if data['data'].get('diff'):
                            items = data['data']['diff']
                            for item in items:
                                all_spot_data.append({
                                    '代码': str(item.get('f12', '')),
                                    '名称': item.get('f14', ''),
                                    '最新价': item.get('f2', 0),
                                    '涨跌幅': item.get('f3', 0),
                                    '市盈率-动态': item.get('f15', ''),
                                    '市净率': item.get('f23', ''),
                                    '行业': ''
                                })
                    
                    current_page += 1
                    import time
                    time.sleep(1)  # 每页之间暂停1秒，避免请求过于频繁
                
                if all_spot_data:
                    df = pd.DataFrame(all_spot_data)
                    print(f"✅ 东方财富API成功获取 {len(df)} 只股票数据（分页获取）")
                    return df
            except Exception as e:
                print(f"⚠️ 东方财富API获取数据失败（第{attempt+1}次）: {e}")
                if attempt < 2:
                    import time
                    time.sleep(3)  # 等待3秒后重试
        
        # 备选：使用新浪财经API（分页获取）
        try:
            print("4️⃣ 尝试使用新浪财经API...")
            
            all_sina_data = []
            page = 1
            while True:
                # 新浪财经A股列表API
                url = "http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/Market_Center.getHQNodeData"
                params = {
                    'page': page,
                    'num': 80,
                    'sort': 'symbol',
                    'asc': 1,
                    'node': 'hs_a',
                    '_s_r_a': 'page'
                }
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Referer': 'http://finance.sina.com.cn/',
                    'Accept': 'application/json, text/javascript, */*; q=0.01'
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                if not data:
                    break
                
                for item in data:
                    # 新浪财经数据格式转换
                    pe = item.get('pe', '')
                    pb = item.get('pb', '')
                    
                    # 确保PE和PB为正数
                    try:
                        pe = float(pe)
                        if pe <= 0:
                            continue
                    except:
                        continue
                    
                    try:
                        pb = float(pb)
                        if pb <= 0:
                            continue
                    except:
                        continue
                    
                    all_sina_data.append({
                        '代码': item.get('symbol', ''),
                        '名称': item.get('name', ''),
                        '最新价': float(item.get('trade', 0)),
                        '涨跌幅': float(item.get('changepercent', 0)),
                        '市盈率-动态': pe,
                        '市净率': pb,
                        '行业': item.get('industry', ''),
                        '总市值': float(item.get('amount', 0)) * float(item.get('trade', 0)) if item.get('amount') else 0
                    })
                
                if len(data) < 80:
                    break
                
                page += 1
                if page > 10:  # 限制最大页数
                    break
            
            df = pd.DataFrame(all_sina_data)
            if not df.empty:
                print(f"✅ 新浪财经API成功获取 {len(df)} 只股票数据")
                return df
        except Exception as e:
            print(f"⚠️ 新浪财经API获取数据失败: {e}")
        
        # 备选：使用同花顺API
        try:
            print("5️⃣ 尝试使用同花顺API...")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # 获取股票列表
            url = "http://61.135.186.83/api/jslist.php"
            params = {
                'type': 'hs_a'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.text
            
            # 解析同花顺数据格式
            if data:
                tonghuashun_data = []
                stocks = data.split(';')
                for stock in stocks:
                    if '=' in stock:
                        parts = stock.split('=')
                        code = parts[0]
                        info = parts[1].strip('"').split(',')
                        if len(info) >= 5:
                            tonghuashun_data.append({
                                '代码': code,
                                '名称': info[0],
                                '最新价': float(info[3]),
                                '涨跌幅': float(info[4]),
                                '市盈率-动态': '',
                                '市净率': '',
                                '行业': ''
                            })
                
                df = pd.DataFrame(tonghuashun_data)
                if not df.empty:
                    print(f"✅ 同花顺API成功获取 {len(df)} 只股票数据")
                    return df
        except Exception as e:
            print(f"⚠️ 同花顺API获取数据失败: {e}")
        
        # 备选：使用证券交易所数据
        try:
            print("6️⃣ 尝试使用证券交易所数据...")
            
            # 上海证券交易所股票列表
            sh_url = "http://www.sse.com.cn/js/common/ssesuggestdata.json"
            # 深圳证券交易所股票列表
            sz_url = "http://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=1110&TABKEY=tab1"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': 'http://www.sse.com.cn/'
            }
            
            exchange_data = []
            
            # 获取上交所数据
            try:
                sh_response = requests.get(sh_url, headers=headers, timeout=15)
                sh_response.raise_for_status()
                sh_data = sh_response.json()
                for item in sh_data:
                    if len(item) >= 2:
                        exchange_data.append({
                            '代码': item[0],
                            '名称': item[1],
                            '最新价': 0,
                            '涨跌幅': 0,
                            '市盈率-动态': '',
                            '市净率': '',
                            '行业': ''
                        })
            except:
                pass
            
            # 获取深交所数据
            try:
                sz_response = requests.get(sz_url, headers=headers, timeout=15)
                sz_response.raise_for_status()
                sz_data = sz_response.json()
                for item in sz_data:
                    if 'data' in item:
                        for stock in item['data']:
                            exchange_data.append({
                                '代码': stock.get('zqdm', ''),
                                '名称': stock.get('zqmc', ''),
                                '最新价': 0,
                                '涨跌幅': 0,
                                '市盈率-动态': '',
                                '市净率': '',
                                '行业': ''
                            })
            except:
                pass
            
            df = pd.DataFrame(exchange_data)
            if not df.empty:
                print(f"✅ 证券交易所数据成功获取 {len(df)} 只股票数据")
                return df
        except Exception as e:
            print(f"⚠️ 证券交易所数据获取失败: {e}")
        
        print("❌ 所有数据获取方法均失败，无法获取股票数据")
        return None
    
    def get_financial_data(self) -> Optional[pd.DataFrame]:
        """获取财务报表数据（优先使用东方财富数据）"""
        if not self.use_real_data:
            return None
        
        # 优先使用AKShare的东方财富数据源
        if AKSHARE_AVAILABLE:
            try:
                print("1️⃣ 尝试使用AKShare获取东方财富财务数据...")
                profit_df = ak.stock_yjbb_em(date="20231231")
                if profit_df is not None and not profit_df.empty:
                    print(f"✅ 成功获取业绩报表数据")
                    financial_df = profit_df.copy()
                    
                    if '股票代码' in financial_df.columns:
                        financial_df = financial_df.rename(columns={'股票代码': '代码'})
                    if '股票简称' in financial_df.columns:
                        financial_df = financial_df.rename(columns={'股票简称': '财务名称'})
                    if '营业总收入-同比增长' in financial_df.columns:
                        financial_df = financial_df.rename(columns={'营业总收入-同比增长': '营收同比'})
                    if '净利润-同比增长' in financial_df.columns:
                        financial_df = financial_df.rename(columns={'净利润-同比增长': '净利润同比'})
                    if '净资产收益率' in financial_df.columns:
                        financial_df = financial_df.rename(columns={'净资产收益率': 'ROE'})
                    if '所处行业' in financial_df.columns:
                        financial_df = financial_df.rename(columns={'所处行业': '行业'})
                    
                    return financial_df
            except Exception as e:
                print(f"⚠️ AKShare获取财务数据失败: {e}")
        
        # 备选：直接调用东方财富财务API
        try:
            print("2️⃣ 尝试直接调用东方财富财务API...")
            
            # 东方财富财务数据API
            url = "http://97.push2.eastmoney.com/api/qt/ulist/get"
            params = {
                'pn': 1,
                'pz': 1000,
                'po': 1,
                'np': 1,
                'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
                'fltt': 2,
                'invt': 2,
                'fid': 'f3',
                'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048',
                'fields': 'f12,f14,f20,f21,f23,f24,f25,f100,f101,f102,f103,f104,f105,f106,f107,f108,f109,f110,f111,f112,f113,f114,f115,f116,f117,f118,f119,f120,f121,f122,f123,f124,f125,f126,f127,f128,f129,f130,f131,f132,f133,f134,f135,f136,f137,f138,f139,f140,f141,f142,f143,f144,f145,f146,f147,f148,f149,f150,f151,f152',
                '_': int(datetime.now().timestamp() * 1000)
            }
            
            response = requests.get(url, params=params, timeout=15)
            data = response.json()
            
            if data.get('data') and data['data'].get('diff'):
                items = data['data']['diff']
                financial_data = []
                for item in items:
                    financial_data.append({
                        '代码': str(item.get('f12', '')),
                        '财务名称': item.get('f14', ''),
                        '行业': '',
                        '营收同比': item.get('f100', ''),  # 营业总收入同比
                        '净利润同比': item.get('f101', ''),  # 净利润同比
                        'ROE': item.get('f106', '')  # 净资产收益率
                    })
                
                df = pd.DataFrame(financial_data)
                if not df.empty:
                    print(f"✅ 东方财富财务API成功获取 {len(df)} 只股票财务数据")
                    return df
        except Exception as e:
            print(f"⚠️ 东方财富财务API获取数据失败: {e}")
        
        # 备选使用Baostock
        if BAOSTOCK_AVAILABLE:
            try:
                print("3️⃣ 尝试使用Baostock获取财务数据...")
                if not self.login_baostock():
                    return None
                
                # 获取所有股票基本信息
                rs = bs.query_stock_basic()
                stock_basic = rs.get_data()
                
                if stock_basic is None or stock_basic.empty:
                    return None
                
                financial_data = []
                for _, row in stock_basic.iterrows():
                    code = row.get('code', '')
                    code_ = code.split('.')[1]
                    name = row.get('code_name', '')
                    industry = row.get('industry', '')
                    
                    # 获取ROE
                    roe = ''
                    rs_roe = bs.query_profit_data(
                        code=code, 
                        year=2023, 
                        quarter=4
                    )
                    roe_data = rs_roe.get_data()
                    if not roe_data.empty:
                        roe = roe_data.get('roeAvg', '').iloc[0] if 'roeAvg' in roe_data.columns else ''
                    
                    financial_data.append({
                        '代码': code_,
                        '财务名称': name,
                        '行业': industry,
                        '营收同比': '',
                        '净利润同比': '',
                        'ROE': roe
                    })
                
                financial_df = pd.DataFrame(financial_data)
                if not financial_df.empty:
                    print(f"✅ Baostock成功获取 {len(financial_df)} 只股票财务数据")
                    return financial_df
            except Exception as e:
                print(f"⚠️ Baostock获取财务数据失败: {e}")
        
        return None
    
    def get_trading_days(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> Optional[List[str]]:
        """获取交易日历"""
        if not self.use_real_data:
            return None
        
        # 优先使用AKShare
        if AKSHARE_AVAILABLE:
            try:
                if not start_date:
                    start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d")
                if not end_date:
                    end_date = datetime.now().strftime("%Y%m%d")
                
                tool_trade_date_hist_sina_df = ak.tool_trade_date_hist_sina()
                if tool_trade_date_hist_sina_df is not None and not tool_trade_date_hist_sina_df.empty:
                    tool_trade_date_hist_sina_df["trade_date"] = pd.to_datetime(
                        tool_trade_date_hist_sina_df["trade_date"]
                    )
                    mask = (
                        (tool_trade_date_hist_sina_df["trade_date"] >= pd.to_datetime(start_date)) &
                        (tool_trade_date_hist_sina_df["trade_date"] <= pd.to_datetime(end_date))
                    )
                    trading_days = tool_trade_date_hist_sina_df[mask]["trade_date"].dt.strftime("%Y%m%d").tolist()
                    return trading_days
            except Exception as e:
                print(f"⚠️ AKShare获取交易日历失败: {e}")
        
        # 备选使用Baostock
        if BAOSTOCK_AVAILABLE:
            try:
                if not self.login_baostock():
                    return None
                
                if not start_date:
                    start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d")
                if not end_date:
                    end_date = datetime.now().strftime("%Y%m%d")
                
                rs = bs.query_trade_dates(start_date=start_date, end_date=end_date)
                trade_dates = rs.get_data()
                if trade_dates is not None and not trade_dates.empty:
                    trading_days = trade_dates[trade_dates['is_trading_day'] == '1']['calendar_date'].tolist()
                    print(f"✅ Baostock成功获取 {len(trading_days)} 个交易日")
                    return trading_days
            except Exception as e:
                print(f"⚠️ Baostock获取交易日历失败: {e}")
        
        return None


def get_data_fetcher():
    """获取数据获取器"""
    return DataFetcher()
