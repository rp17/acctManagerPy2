"""
CRITICAL: Centralized Currency Management System

This module provides thread-safe currency conversion, exchange rate management,
and currency symbol handling for all views in the account management system.

MANDATORY: All currency operations must be thread-safe and accurate.
"""

import threading
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass


@dataclass
class CurrencyInfo:
    """Currency information container"""
    code: str
    symbol: str
    name: str
    exchange_rate: Decimal
    precision: int = 2


class CurrencyManager:
    """
    CRITICAL: Centralized currency management for all views
    MANDATORY: Thread-safe currency operations and rate updates
    """
    
    def __init__(self):
        self._currencies: Dict[str, CurrencyInfo] = {
            "USD": CurrencyInfo("USD", "$", "US Dollar", Decimal("1.0"), 2),
            "EUR": CurrencyInfo("EUR", "€", "Euro", Decimal("0.85"), 2),
            "JPY": CurrencyInfo("JPY", "¥", "Japanese Yen", Decimal("110.0"), 0),
            "GBP": CurrencyInfo("GBP", "£", "British Pound", Decimal("0.73"), 2),
            "CAD": CurrencyInfo("CAD", "C$", "Canadian Dollar", Decimal("1.25"), 2),
            "AUD": CurrencyInfo("AUD", "A$", "Australian Dollar", Decimal("1.35"), 2),
            "CHF": CurrencyInfo("CHF", "CHF", "Swiss Franc", Decimal("0.92"), 2),
            "CNY": CurrencyInfo("CNY", "¥", "Chinese Yuan", Decimal("6.45"), 2),
        }
        self._observers: List[Callable] = []
        self._lock = threading.Lock()
        self._default_currency = "USD"
    
    def register_observer(self, observer: Callable) -> None:
        """
        MANDATORY: Register for rate updates
        CRITICAL: Thread-safe observer registration
        """
        with self._lock:
            if observer not in self._observers:
                self._observers.append(observer)
    
    def unregister_observer(self, observer: Callable) -> None:
        """
        MANDATORY: Unregister from rate updates
        CRITICAL: Thread-safe observer unregistration
        """
        with self._lock:
            if observer in self._observers:
                self._observers.remove(observer)
    
    def update_exchange_rate(self, currency: str, rate: Decimal) -> None:
        """
        CRITICAL: Update rates and notify all views
        MANDATORY: Thread-safe rate updates
        """
        if currency not in self._currencies:
            raise ValueError(f"Unknown currency: {currency}")
        
        with self._lock:
            self._currencies[currency].exchange_rate = rate
        
        # Notify observers
        self._notify_observers(currency, rate)
    
    def _notify_observers(self, currency: str, rate: Decimal) -> None:
        """Notify all registered observers of rate changes"""
        with self._lock:
            observers = self._observers.copy()
        
        for observer in observers:
            try:
                if hasattr(observer, 'on_currency_rate_changed'):
                    observer.on_currency_rate_changed(currency, rate)
            except Exception as e:
                print(f"Error notifying observer of rate change: {e}")
    
    def convert_amount(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """
        MANDATORY: Thread-safe currency conversion
        CRITICAL: Accurate conversion using cross-rates
        """
        if from_currency == to_currency:
            return amount
        
        with self._lock:
            if from_currency not in self._currencies or to_currency not in self._currencies:
                raise ValueError(f"Unsupported currency pair: {from_currency} to {to_currency}")
            
            # Convert to USD first, then to target currency
            from_info = self._currencies[from_currency]
            to_info = self._currencies[to_currency]
            
            # Convert to USD
            usd_amount = amount / from_info.exchange_rate
            
            # Convert from USD to target currency
            result = usd_amount * to_info.exchange_rate
            
            # Round to appropriate precision
            return result.quantize(Decimal('0.01') if to_info.precision == 2 else Decimal('1'), 
                                 rounding=ROUND_HALF_UP)
    
    def format_amount(self, amount: Decimal, currency: str) -> str:
        """
        MANDATORY: Format amount with currency symbol
        CRITICAL: Consistent formatting across all views
        """
        with self._lock:
            if currency not in self._currencies:
                currency = self._default_currency
            
            currency_info = self._currencies[currency]
        
        # Format based on currency precision
        if currency_info.precision == 0:
            formatted_amount = f"{int(amount):,}"
        else:
            formatted_amount = f"{amount:,.2f}"
        
        return f"{currency_info.symbol}{formatted_amount}"
    
    def get_currency_symbol(self, currency: str) -> str:
        """Get currency symbol"""
        with self._lock:
            if currency in self._currencies:
                return self._currencies[currency].symbol
            return "$"  # Default to USD symbol
    
    def get_currency_name(self, currency: str) -> str:
        """Get currency name"""
        with self._lock:
            if currency in self._currencies:
                return self._currencies[currency].name
            return "Unknown Currency"
    
    def get_exchange_rate(self, currency: str) -> Decimal:
        """Get current exchange rate"""
        with self._lock:
            if currency in self._currencies:
                return self._currencies[currency].exchange_rate
            return Decimal("1.0")
    
    def get_supported_currencies(self) -> List[str]:
        """Get list of supported currencies"""
        with self._lock:
            return list(self._currencies.keys())
    
    def get_currency_info(self, currency: str) -> Optional[CurrencyInfo]:
        """Get complete currency information"""
        with self._lock:
            return self._currencies.get(currency)
    
    def set_default_currency(self, currency: str) -> None:
        """Set default currency for the application"""
        with self._lock:
            if currency in self._currencies:
                self._default_currency = currency
    
    def get_default_currency(self) -> str:
        """Get default currency"""
        with self._lock:
            return self._default_currency
    
    def add_currency(self, currency_info: CurrencyInfo) -> None:
        """
        MANDATORY: Add new currency to the system
        CRITICAL: Thread-safe currency addition
        """
        with self._lock:
            self._currencies[currency_info.code] = currency_info
    
    def remove_currency(self, currency: str) -> None:
        """
        MANDATORY: Remove currency from the system
        CRITICAL: Thread-safe currency removal
        """
        if currency == self._default_currency:
            raise ValueError("Cannot remove default currency")
        
        with self._lock:
            if currency in self._currencies:
                del self._currencies[currency]
    
    def get_conversion_matrix(self) -> Dict[str, Dict[str, Decimal]]:
        """
        CRITICAL: Get complete conversion matrix
        MANDATORY: Thread-safe matrix generation
        """
        with self._lock:
            currencies = list(self._currencies.keys())
            matrix = {}
            
            for from_curr in currencies:
                matrix[from_curr] = {}
                for to_curr in currencies:
                    if from_curr == to_curr:
                        matrix[from_curr][to_curr] = Decimal("1.0")
                    else:
                        try:
                            matrix[from_curr][to_curr] = self.convert_amount(
                                Decimal("1.0"), from_curr, to_curr
                            )
                        except ValueError:
                            matrix[from_curr][to_curr] = Decimal("0.0")
            
            return matrix
    
    def validate_currency(self, currency: str) -> bool:
        """Validate if currency is supported"""
        with self._lock:
            return currency in self._currencies
    
    def get_currency_statistics(self) -> Dict[str, Any]:
        """Get statistics about currency usage"""
        with self._lock:
            return {
                'total_currencies': len(self._currencies),
                'supported_currencies': list(self._currencies.keys()),
                'default_currency': self._default_currency,
                'observers_count': len(self._observers)
            }


# CRITICAL: Global instance for application-wide access
currency_manager = CurrencyManager() 