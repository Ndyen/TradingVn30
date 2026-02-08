import sys
import os

try:
    import vnstock
    with open("vnstock_info.txt", "w", encoding="utf-8") as f:
        f.write(f"File: {vnstock.__file__}\n")
        f.write(f"Dir: {dir(vnstock)}\n")
        
        # Check for specific functions
        has_stock_hist = hasattr(vnstock, 'stock_historical_data')
        f.write(f"Has stock_historical_data: {has_stock_hist}\n")
        
        has_listing = hasattr(vnstock, 'listing_companies')
        f.write(f"Has listing_companies: {has_listing}\n")
        
        if not has_stock_hist:
            # Check submodules
            f.write("Checking submodules...\n")
            # Try some common ones
            try: 
                from vnstock import stock
                f.write(f"vnstock.stock dir: {dir(stock)}\n")
            except ImportError:
                f.write("No vnstock.stock\n")

except Exception as e:
    with open("vnstock_info.txt", "w", encoding="utf-8") as f:
        f.write(f"Error: {e}")
