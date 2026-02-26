"""
Economy v0.2 - 动态经济系统
供需驱动价格，AI自动交易
"""

from typing import Dict, List
from collections import defaultdict
import random

class Market:
    """市场 - 供需决定价格"""
    
    def __init__(self):
        # 供给：每个AI提供的商品
        self.supply: Dict[str, List[Dict]] = defaultdict(list)
        # 需求：每个AI想要的商品
        self.demand: Dict[str, List[Dict]] = defaultdict(list)
        # 当前价格
        self.prices: Dict[str, float] = {
            'food': 10.0,
            'wood': 5.0,
            'stone': 8.0,
            'tool': 50.0,
            'medicine': 100.0,
        }
        # 基础价格
        self.base_prices = self.prices.copy()
        # 交易历史
        self.transactions: List[Dict] = []
    
    def update_prices(self):
        """根据供需更新价格"""
        for item in self.prices:
            supply_amount = sum(s['amount'] for s in self.supply[item])
            demand_amount = sum(d['amount'] for d in self.demand[item])
            
            # 供需比
            ratio = demand_amount / (supply_amount + 1)
            
            # 价格调整（平滑）
            target_price = self.base_prices[item] * ratio
            current_price = self.prices[item]
            
            # 每次调整不超过10%
            if target_price > current_price:
                self.prices[item] = min(target_price, current_price * 1.1)
            else:
                self.prices[item] = max(target_price, current_price * 0.9)
            
            # 限制价格范围
            self.prices[item] = max(self.base_prices[item] * 0.3,
                                   min(self.prices[item], self.base_prices[item] * 3))
    
    def list_item(self, agent_id: str, item: str, amount: float, price: float):
        """上架商品"""
        self.supply[item].append({
            'seller': agent_id,
            'amount': amount,
            'price': price
        })
    
    def request_item(self, agent_id: str, item: str, amount: float, max_price: float):
        """发布需求"""
        self.demand[item].append({
            'buyer': agent_id,
            'amount': amount,
            'max_price': max_price
        })
    
    def match_trades(self) -> List[Dict]:
        """撮合交易"""
        trades = []
        
        for item in self.prices:
            # 按价格排序：卖家低价优先，买家高价优先
            sellers = sorted(self.supply[item], key=lambda x: x['price'])
            buyers = sorted(self.demand[item], key=lambda x: x['max_price'], reverse=True)
            
            for seller in sellers:
                for buyer in buyers:
                    if seller['price'] <= buyer['max_price']:
                        # 成交
                        amount = min(seller['amount'], buyer['amount'])
                        price = (seller['price'] + buyer['max_price']) / 2  # 中间价
                        
                        trades.append({
                            'item': item,
                            'amount': amount,
                            'price': price,
                            'buyer': buyer['buyer'],
                            'seller': seller['seller']
                        })
                        
                        # 更新剩余
                        seller['amount'] -= amount
                        buyer['amount'] -= amount
                        
                        if seller['amount'] <= 0:
                            break
                        if buyer['amount'] <= 0:
                            buyers.remove(buyer)
        
        # 清理已完成的订单
        for item in self.supply:
            self.supply[item] = [s for s in self.supply[item] if s['amount'] > 0]
        for item in self.demand:
            self.demand[item] = [d for d in self.demand[item] if d['amount'] > 0]
        
        # 记录交易
        self.transactions.extend(trades)
        
        return trades
    
    def get_price_report(self) -> str:
        """获取价格报告"""
        lines = ["📈 市场价格:"]
        for item, price in sorted(self.prices.items()):
            base = self.base_prices[item]
            change = (price - base) / base * 100
            arrow = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            lines.append(f"  {item}: {price:.1f} ({change:+.0f}%) {arrow}")
        return "\n".join(lines)


class Farm:
    """农场系统 - 种植、生长、收获"""
    
    def __init__(self, x: int, y: int, owner_id: str):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        
        # 作物状态
        self.crop = None  # 当前种植作物
        self.growth = 0.0  # 生长进度 0-100
        self.planted_at = None
        
        # 土壤肥力
        self.fertility = 1.0
    
    def plant(self, crop_type: str) -> bool:
        """种植作物"""
        if self.crop is not None:
            return False
        
        self.crop = crop_type
        self.growth = 0.0
        self.planted_at = None  # 由世界时间系统设置
        return True
    
    def grow(self, hours: float, weather: str):
        """生长"""
        if self.crop is None:
            return
        
        # 基础生长速度
        base_growth = 5.0  # 每小时5%
        
        # 天气影响
        weather_mod = {
            'sunny': 1.2,
            'rainy': 1.0,
            'cloudy': 0.8,
            'drought': 0.3
        }.get(weather, 1.0)
        
        # 土壤肥力影响
        growth_rate = base_growth * weather_mod * self.fertility
        
        self.growth += growth_rate * hours
        self.fertility *= 0.999  # 土壤逐渐贫瘠
        
        # 成熟
        if self.growth >= 100:
            self.growth = 100
    
    def harvest(self) -> float:
        """收获"""
        if self.crop is None or self.growth < 100:
            return 0
        
        # 产量
        base_yield = {
            'wheat': 10,
            'vegetable': 8,
            'fruit': 12
        }.get(self.crop, 5)
        
        amount = base_yield * self.fertility
        
        # 重置农场
        self.crop = None
        self.growth = 0
        
        return amount
    
    def get_status(self) -> str:
        """获取状态"""
        if self.crop is None:
            return "空地"
        elif self.growth < 100:
            stages = ['🌱幼苗', '🌿生长', '🌾快熟']
            stage = stages[int(self.growth / 33)]
            return f"{self.crop} {stage} ({self.growth:.0f}%)"
        else:
            return f"{self.crop} ✅可收获"
