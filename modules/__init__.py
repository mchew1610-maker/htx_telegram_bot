"""HTX Bot 模块包"""

# 安全导入所有模块
modules_loaded = []

try:
    from .account.account import AccountModule
    modules_loaded.append("AccountModule")
except Exception as e:
    print(f"警告: AccountModule 导入失败: {e}")

try:
    from .market.market import MarketModule
    modules_loaded.append("MarketModule")
except Exception as e:
    print(f"警告: MarketModule 导入失败: {e}")

try:
    from .trading.trading import TradingModule
    modules_loaded.append("TradingModule")
except Exception as e:
    print(f"警告: TradingModule 导入失败: {e}")

try:
    from .grid.grid import GridModule
    modules_loaded.append("GridModule")
except Exception as e:
    print(f"警告: GridModule 导入失败: {e}")

try:
    from .monitor.monitor import MonitorModule
    modules_loaded.append("MonitorModule")
except Exception as e:
    print(f"警告: MonitorModule 导入失败: {e}")

try:
    from .charts.charts import ChartsModule
    modules_loaded.append("ChartsModule")
except Exception as e:
    print(f"警告: ChartsModule 导入失败: {e}")

print(f"已加载模块: {', '.join(modules_loaded)}")

__all__ = ['AccountModule', 'MarketModule', 'TradingModule', 'GridModule', 'MonitorModule', 'ChartsModule']
