"""Financial Trading Agent implementation."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd

from langchain_core.callbacks import BaseCallbackManager
from langchain_core.language_models import BaseLanguageModel
from langchain_core.tools import BaseTool, tool

from langchain_community.agent_toolkits.ai_mega_agents_factory.base import (
    AgentCategory,
    BaseMegaAgent,
    MegaAgentConfig,
    MegaAgentManifest,
    MonetizationTier,
)


class TradingMetrics:
    """Trading operation metrics."""
    
    def __init__(self):
        """Initialize metrics."""
        self.reset()
    
    def reset(self) -> None:
        """Reset metrics."""
        self.total_trades = 0
        self.profitable_trades = 0
        self.losing_trades = 0
        self.total_profit_loss = 0.0
        self.win_rate = 0.0
        self.sharpe_ratio = 0.0
        self.max_drawdown = 0.0
        self.execution_time = 0.0


@tool
def analyze_market_data(symbol: str, timeframe: str, indicators: List[str]) -> Dict[str, Any]:
    """Analyze market data with technical indicators.
    
    Args:
        symbol: Trading symbol (e.g., AAPL, TSLA)
        timeframe: Timeframe for analysis (1m, 5m, 1h, 1d)
        indicators: List of technical indicators to calculate
        
    Returns:
        Market analysis results
    """
    try:
        # Simulate market data (in production, would connect to real data feeds)
        np.random.seed(hash(symbol) % 2**32)
        
        # Generate sample OHLCV data
        periods = 100
        base_price = np.random.uniform(50, 200)
        
        dates = pd.date_range(start=datetime.now() - timedelta(days=periods), periods=periods, freq='D')
        
        # Generate realistic price movements
        returns = np.random.normal(0.001, 0.02, periods)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        data = pd.DataFrame({
            'timestamp': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 10000000, periods),
        })
        
        analysis_results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": prices[-1],
            "price_change_24h": ((prices[-1] - prices[-2]) / prices[-2]) * 100,
            "volume_24h": int(data['volume'].iloc[-1]),
            "technical_indicators": {},
        }
        
        # Calculate requested technical indicators
        for indicator in indicators:
            if indicator == "SMA_20":
                analysis_results["technical_indicators"]["SMA_20"] = data['close'].rolling(20).mean().iloc[-1]
            elif indicator == "EMA_12":
                analysis_results["technical_indicators"]["EMA_12"] = data['close'].ewm(span=12).mean().iloc[-1]
            elif indicator == "RSI":
                delta = data['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                analysis_results["technical_indicators"]["RSI"] = rsi.iloc[-1]
            elif indicator == "MACD":
                ema12 = data['close'].ewm(span=12).mean()
                ema26 = data['close'].ewm(span=26).mean()
                macd = ema12 - ema26
                signal = macd.ewm(span=9).mean()
                analysis_results["technical_indicators"]["MACD"] = {
                    "macd": macd.iloc[-1],
                    "signal": signal.iloc[-1],
                    "histogram": (macd - signal).iloc[-1],
                }
            elif indicator == "Bollinger_Bands":
                sma20 = data['close'].rolling(20).mean()
                std20 = data['close'].rolling(20).std()
                analysis_results["technical_indicators"]["Bollinger_Bands"] = {
                    "upper": (sma20 + 2 * std20).iloc[-1],
                    "middle": sma20.iloc[-1],
                    "lower": (sma20 - 2 * std20).iloc[-1],
                }
        
        return {
            "status": "success",
            "analysis": analysis_results,
            "market_data": data.tail(10).to_dict('records'),
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def generate_trading_signals(analysis: Dict[str, Any], strategy: str) -> Dict[str, Any]:
    """Generate trading signals based on market analysis.
    
    Args:
        analysis: Market analysis data
        strategy: Trading strategy to use
        
    Returns:
        Trading signals and recommendations
    """
    try:
        indicators = analysis.get("technical_indicators", {})
        current_price = analysis.get("current_price", 0)
        
        signals = {
            "timestamp": datetime.now().isoformat(),
            "symbol": analysis.get("symbol"),
            "current_price": current_price,
            "signals": [],
            "strategy": strategy,
        }
        
        if strategy == "RSI_OVERSOLD_OVERBOUGHT":
            rsi = indicators.get("RSI", 50)
            if rsi < 30:
                signals["signals"].append({
                    "action": "BUY",
                    "strength": "STRONG",
                    "reason": f"RSI oversold at {rsi:.2f}",
                    "entry_price": current_price,
                    "stop_loss": current_price * 0.95,
                    "take_profit": current_price * 1.10,
                })
            elif rsi > 70:
                signals["signals"].append({
                    "action": "SELL",
                    "strength": "STRONG", 
                    "reason": f"RSI overbought at {rsi:.2f}",
                    "entry_price": current_price,
                    "stop_loss": current_price * 1.05,
                    "take_profit": current_price * 0.90,
                })
            else:
                signals["signals"].append({
                    "action": "HOLD",
                    "strength": "NEUTRAL",
                    "reason": f"RSI neutral at {rsi:.2f}",
                })
        
        elif strategy == "MOVING_AVERAGE_CROSSOVER":
            sma20 = indicators.get("SMA_20", current_price)
            ema12 = indicators.get("EMA_12", current_price)
            
            if ema12 > sma20:
                signals["signals"].append({
                    "action": "BUY",
                    "strength": "MEDIUM",
                    "reason": "EMA12 above SMA20 - uptrend",
                    "entry_price": current_price,
                    "stop_loss": current_price * 0.96,
                    "take_profit": current_price * 1.08,
                })
            else:
                signals["signals"].append({
                    "action": "SELL",
                    "strength": "MEDIUM",
                    "reason": "EMA12 below SMA20 - downtrend",
                    "entry_price": current_price,
                    "stop_loss": current_price * 1.04,
                    "take_profit": current_price * 0.92,
                })
        
        elif strategy == "BOLLINGER_BOUNCE":
            bb = indicators.get("Bollinger_Bands", {})
            upper = bb.get("upper", current_price * 1.02)
            lower = bb.get("lower", current_price * 0.98)
            middle = bb.get("middle", current_price)
            
            if current_price <= lower:
                signals["signals"].append({
                    "action": "BUY",
                    "strength": "STRONG",
                    "reason": "Price at lower Bollinger Band",
                    "entry_price": current_price,
                    "stop_loss": lower * 0.98,
                    "take_profit": middle,
                })
            elif current_price >= upper:
                signals["signals"].append({
                    "action": "SELL",
                    "strength": "STRONG",
                    "reason": "Price at upper Bollinger Band",
                    "entry_price": current_price,
                    "stop_loss": upper * 1.02,
                    "take_profit": middle,
                })
        
        return {
            "status": "success",
            "signals": signals,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def execute_trade(
    order: Dict[str, Any],
    account_balance: float,
    position_size: float,
) -> Dict[str, Any]:
    """Execute a trading order.
    
    Args:
        order: Trading order details
        account_balance: Available account balance
        position_size: Position size as percentage of balance
        
    Returns:
        Trade execution results
    """
    try:
        action = order.get("action")
        symbol = order.get("symbol")
        entry_price = order.get("entry_price", 0)
        quantity = order.get("quantity", 0)
        
        # Calculate trade value
        if quantity == 0:
            # Calculate quantity based on position size
            trade_value = account_balance * (position_size / 100)
            quantity = int(trade_value / entry_price)
        else:
            trade_value = quantity * entry_price
        
        # Check if sufficient balance
        if trade_value > account_balance:
            return {
                "status": "error",
                "error": "Insufficient account balance",
                "required": trade_value,
                "available": account_balance,
            }
        
        # Simulate trade execution with small slippage
        slippage = np.random.uniform(-0.001, 0.001)
        execution_price = entry_price * (1 + slippage)
        
        # Generate trade ID
        trade_id = f"TRADE_{int(time.time())}_{hash(symbol) % 10000}"
        
        execution_result = {
            "status": "success",
            "trade_id": trade_id,
            "symbol": symbol,
            "action": action,
            "quantity": quantity,
            "entry_price": entry_price,
            "execution_price": execution_price,
            "slippage": slippage,
            "trade_value": quantity * execution_price,
            "commission": quantity * execution_price * 0.001,  # 0.1% commission
            "timestamp": datetime.now().isoformat(),
            "stop_loss": order.get("stop_loss"),
            "take_profit": order.get("take_profit"),
        }
        
        return execution_result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def calculate_portfolio_metrics(trades: List[Dict[str, Any]], initial_balance: float) -> Dict[str, Any]:
    """Calculate portfolio performance metrics.
    
    Args:
        trades: List of executed trades
        initial_balance: Initial portfolio balance
        
    Returns:
        Portfolio performance metrics
    """
    try:
        if not trades:
            return {
                "status": "success",
                "metrics": {
                    "total_trades": 0,
                    "total_return": 0.0,
                    "win_rate": 0.0,
                    "profit_factor": 0.0,
                    "sharpe_ratio": 0.0,
                    "max_drawdown": 0.0,
                },
            }
        
        total_pnl = 0.0
        winning_trades = 0
        losing_trades = 0
        gross_profit = 0.0
        gross_loss = 0.0
        returns = []
        
        current_balance = initial_balance
        peak_balance = initial_balance
        max_drawdown = 0.0
        
        for trade in trades:
            if trade.get("status") != "success":
                continue
            
            # Calculate P&L (simplified - assumes all trades are closed)
            trade_pnl = 0.0
            action = trade.get("action")
            quantity = trade.get("quantity", 0)
            entry_price = trade.get("execution_price", 0)
            commission = trade.get("commission", 0)
            
            # Simulate exit price (in production, this would be actual exit data)
            exit_price = entry_price * (1 + np.random.normal(0, 0.02))
            
            if action == "BUY":
                trade_pnl = (exit_price - entry_price) * quantity - commission * 2
            else:  # SELL
                trade_pnl = (entry_price - exit_price) * quantity - commission * 2
            
            total_pnl += trade_pnl
            current_balance += trade_pnl
            
            if trade_pnl > 0:
                winning_trades += 1
                gross_profit += trade_pnl
            else:
                losing_trades += 1
                gross_loss += abs(trade_pnl)
            
            # Calculate return for this trade
            trade_return = trade_pnl / initial_balance
            returns.append(trade_return)
            
            # Update drawdown
            if current_balance > peak_balance:
                peak_balance = current_balance
            
            drawdown = (peak_balance - current_balance) / peak_balance
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        total_trades = len(trades)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        total_return = (current_balance - initial_balance) / initial_balance
        
        # Calculate Sharpe ratio (simplified)
        if returns:
            avg_return = np.mean(returns)
            return_std = np.std(returns)
            sharpe_ratio = avg_return / return_std if return_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        metrics = {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_return": total_return,
            "total_pnl": total_pnl,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe_ratio,
            "max_drawdown": max_drawdown,
            "initial_balance": initial_balance,
            "final_balance": current_balance,
        }
        
        return {
            "status": "success",
            "metrics": metrics,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@tool
def risk_management_check(
    trade_order: Dict[str, Any],
    portfolio: Dict[str, Any],
    risk_params: Dict[str, Any],
) -> Dict[str, Any]:
    """Perform risk management checks before trade execution.
    
    Args:
        trade_order: Proposed trade order
        portfolio: Current portfolio state
        risk_params: Risk management parameters
        
    Returns:
        Risk check results
    """
    try:
        checks = []
        approved = True
        
        account_balance = portfolio.get("balance", 0)
        trade_value = trade_order.get("quantity", 0) * trade_order.get("entry_price", 0)
        
        # Position size check
        max_position_size = risk_params.get("max_position_size_percent", 5)
        position_size_percent = (trade_value / account_balance) * 100
        
        if position_size_percent > max_position_size:
            checks.append({
                "check": "position_size",
                "status": "FAIL",
                "message": f"Position size {position_size_percent:.2f}% exceeds limit of {max_position_size}%",
            })
            approved = False
        else:
            checks.append({
                "check": "position_size",
                "status": "PASS",
                "message": f"Position size {position_size_percent:.2f}% within limit",
            })
        
        # Daily loss limit check
        daily_pnl = portfolio.get("daily_pnl", 0)
        max_daily_loss = risk_params.get("max_daily_loss_percent", 2)
        max_daily_loss_amount = account_balance * (max_daily_loss / 100)
        
        if daily_pnl < -max_daily_loss_amount:
            checks.append({
                "check": "daily_loss_limit",
                "status": "FAIL",
                "message": f"Daily loss limit exceeded: ${daily_pnl:.2f} < ${-max_daily_loss_amount:.2f}",
            })
            approved = False
        else:
            checks.append({
                "check": "daily_loss_limit",
                "status": "PASS",
                "message": f"Daily P&L within limit: ${daily_pnl:.2f}",
            })
        
        # Stop loss check
        stop_loss = trade_order.get("stop_loss")
        entry_price = trade_order.get("entry_price", 0)
        max_stop_loss_percent = risk_params.get("max_stop_loss_percent", 3)
        
        if stop_loss:
            action = trade_order.get("action")
            if action == "BUY":
                stop_loss_percent = ((entry_price - stop_loss) / entry_price) * 100
            else:
                stop_loss_percent = ((stop_loss - entry_price) / entry_price) * 100
            
            if stop_loss_percent > max_stop_loss_percent:
                checks.append({
                    "check": "stop_loss",
                    "status": "FAIL",
                    "message": f"Stop loss {stop_loss_percent:.2f}% exceeds limit of {max_stop_loss_percent}%",
                })
                approved = False
            else:
                checks.append({
                    "check": "stop_loss",
                    "status": "PASS",
                    "message": f"Stop loss {stop_loss_percent:.2f}% within limit",
                })
        
        return {
            "status": "success",
            "approved": approved,
            "checks": checks,
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


class FinancialTradingAgent(BaseMegaAgent):
    """Financial Trading Agent for automated trading strategies."""
    
    def __init__(
        self,
        config: Optional[MegaAgentConfig] = None,
        llm: Optional[BaseLanguageModel] = None,
        callback_manager: Optional[BaseCallbackManager] = None,
        **kwargs: Any,
    ):
        """Initialize Financial Trading Agent.
        
        Args:
            config: Agent configuration
            llm: Language model
            callback_manager: Callback manager
            **kwargs: Additional arguments
        """
        if config is None:
            manifest = MegaAgentManifest(
                name="Financial Trading Agent",
                version="1.0.0",
                category=AgentCategory.SPECIALIST,
                description="Enterprise financial trading agent for automated investment strategies",
                author="AI Mega Agents Factory",
                tags=["trading", "finance", "investment", "quant", "risk"],
                min_langchain_version="0.1.0",
                supported_llm_types=["openai", "anthropic", "huggingface"],
                required_tools=["numpy", "pandas", "financial_data"],
                monetization_tier=MonetizationTier.PROFESSIONAL,
                pricing_model="usage_based",
            )
            config = MegaAgentConfig(manifest=manifest)
        
        super().__init__(config, llm, callback_manager, **kwargs)
        self.metrics = TradingMetrics()
        
    def initialize(self) -> None:
        """Initialize the trading agent."""
        if self._initialized:
            return
            
        self._tools = self.get_tools()
        self._initialized = True
    
    def get_tools(self) -> List[BaseTool]:
        """Get trading tools.
        
        Returns:
            List of trading tools
        """
        return [
            analyze_market_data,
            generate_trading_signals,
            execute_trade,
            calculate_portfolio_metrics,
            risk_management_check,
        ]
    
    async def execute(
        self,
        input_data: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute trading operation.
        
        Args:
            input_data: Trading operation configuration
            **kwargs: Additional execution parameters
            
        Returns:
            Trading operation results
        """
        start_time = time.time()
        self.metrics.reset()
        
        try:
            if not self.validate_input(input_data):
                return {
                    "status": "error",
                    "error": "Invalid input data",
                    "required_fields": ["operation"],
                }
            
            operation = input_data.get("operation")
            
            if operation == "analyze_market":
                result = await self._analyze_market(input_data)
            elif operation == "generate_signals":
                result = await self._generate_signals(input_data)
            elif operation == "execute_trade":
                result = await self._execute_trade(input_data)
            elif operation == "portfolio_analysis":
                result = await self._analyze_portfolio(input_data)
            elif operation == "full_trading_cycle":
                result = await self._full_trading_cycle(input_data)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown operation: {operation}",
                    "supported_operations": [
                        "analyze_market", "generate_signals", "execute_trade", 
                        "portfolio_analysis", "full_trading_cycle"
                    ],
                }
            
            self.metrics.execution_time = time.time() - start_time
            
            result.update({
                "execution_time": self.metrics.execution_time,
                "metrics": self.get_metrics(),
            })
            
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time,
            }
    
    async def _analyze_market(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market data."""
        return analyze_market_data.invoke({
            "symbol": input_data.get("symbol", ""),
            "timeframe": input_data.get("timeframe", "1d"),
            "indicators": input_data.get("indicators", []),
        })
    
    async def _generate_signals(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate trading signals."""
        return generate_trading_signals.invoke({
            "analysis": input_data.get("analysis", {}),
            "strategy": input_data.get("strategy", ""),
        })
    
    async def _execute_trade(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute trade order."""
        # Perform risk check first
        risk_check = risk_management_check.invoke({
            "trade_order": input_data.get("order", {}),
            "portfolio": input_data.get("portfolio", {}),
            "risk_params": input_data.get("risk_params", {}),
        })
        
        if not risk_check.get("approved", False):
            return {
                "status": "rejected",
                "reason": "Risk management check failed",
                "risk_checks": risk_check.get("checks", []),
            }
        
        # Execute the trade
        result = execute_trade.invoke({
            "order": input_data.get("order", {}),
            "account_balance": input_data.get("account_balance", 0),
            "position_size": input_data.get("position_size", 5),
        })
        
        if result.get("status") == "success":
            self.metrics.total_trades += 1
        
        return result
    
    async def _analyze_portfolio(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze portfolio performance."""
        return calculate_portfolio_metrics.invoke({
            "trades": input_data.get("trades", []),
            "initial_balance": input_data.get("initial_balance", 10000),
        })
    
    async def _full_trading_cycle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute full trading cycle: analyze -> signal -> risk check -> trade."""
        symbol = input_data.get("symbol", "")
        strategy = input_data.get("strategy", "RSI_OVERSOLD_OVERBOUGHT")
        indicators = input_data.get("indicators", ["RSI", "SMA_20", "EMA_12"])
        
        # Step 1: Analyze market
        analysis_result = await self._analyze_market({
            "symbol": symbol,
            "timeframe": input_data.get("timeframe", "1d"),
            "indicators": indicators,
        })
        
        if analysis_result.get("status") != "success":
            return analysis_result
        
        # Step 2: Generate signals
        signals_result = await self._generate_signals({
            "analysis": analysis_result["analysis"],
            "strategy": strategy,
        })
        
        if signals_result.get("status") != "success":
            return signals_result
        
        signals = signals_result["signals"]["signals"]
        
        # Step 3: Execute trades for actionable signals
        trade_results = []
        
        for signal in signals:
            if signal.get("action") in ["BUY", "SELL"]:
                order = {
                    "action": signal["action"],
                    "symbol": symbol,
                    "entry_price": signal["entry_price"],
                    "stop_loss": signal.get("stop_loss"),
                    "take_profit": signal.get("take_profit"),
                    "quantity": 0,  # Will be calculated based on position size
                }
                
                trade_result = await self._execute_trade({
                    "order": order,
                    "account_balance": input_data.get("account_balance", 10000),
                    "position_size": input_data.get("position_size", 5),
                    "portfolio": input_data.get("portfolio", {}),
                    "risk_params": input_data.get("risk_params", {}),
                })
                
                trade_results.append(trade_result)
        
        return {
            "status": "success",
            "symbol": symbol,
            "strategy": strategy,
            "market_analysis": analysis_result["analysis"],
            "trading_signals": signals,
            "trade_executions": trade_results,
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate trading input data.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        if "operation" not in input_data:
            return False
        
        operation = input_data["operation"]
        
        if operation == "analyze_market":
            return "symbol" in input_data
        elif operation == "generate_signals":
            return "analysis" in input_data and "strategy" in input_data
        elif operation == "execute_trade":
            return "order" in input_data and "account_balance" in input_data
        elif operation == "portfolio_analysis":
            return "trades" in input_data
        elif operation == "full_trading_cycle":
            return "symbol" in input_data
        
        return True
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get trading metrics.
        
        Returns:
            Current metrics
        """
        return {
            "total_trades": self.metrics.total_trades,
            "profitable_trades": self.metrics.profitable_trades,
            "losing_trades": self.metrics.losing_trades,
            "win_rate": self.metrics.win_rate,
            "total_profit_loss": self.metrics.total_profit_loss,
            "sharpe_ratio": self.metrics.sharpe_ratio,
            "max_drawdown": self.metrics.max_drawdown,
            "execution_time": self.metrics.execution_time,
        }