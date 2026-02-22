#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
短线交易回测系统 - 数据获取模块
获取A股历史数据用于回测
"""

import sys
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd

try:
    import akshare as ak
    AKSHARE_AVAILABLE = True
except ImportError:
    AKSHARE_AVAILABLE = False


class ShortTermDataFetcher:
    """短线交易数据获取器"""
    
    def __init__(self):
        self.use_real_data = AKSHARE_AVAILABLE
    
    def check_akshare(self) -> bool:
        """检查AKShare是否可用"""
        return AKSHARE_AVAILABLE
    
    def get_all_stock_codes(self) -> Optional[List[str]]:
        """获取所有A股股票代码列表"""
        if not self.use_real_data:
            return None
        
        try:
            stock_list = ak.stock_zh_a_spot_em()
            if stock_list is not None and not stock_list.empty:
                return stock_list["代码"].tolist()
            return None
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return None
    
    def get_stock_historical_data(
        self, 
        code: str, 
        start_date: str = None, 
        end_date: str = None
    ) -> Optional[pd.DataFrame]:
        """
        获取单只股票历史数据
        
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
                return stock_data
            return None
        except Exception as e:
            print(f"获取股票 {code} 历史数据失败: {e}")
            return None
    
    def get_trading_days(
        self, 
        start_date: str = None, 
        end_date: str = None
    ) -> Optional[List[str]]:
        """获取交易日历"""
        if not self.use_real_data:
            return None
        
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
            return None
        except Exception as e:
            print(f"获取交易日历失败: {e}")
            return None


def get_data_fetcher():
    """获取数据获取器"""
    return ShortTermDataFetcher()
