try:
    import vnstock
    print(f"vnstock file: {vnstock.__file__}")
    print(dir(vnstock))
except ImportError as e:
    print(f"ImportError: {e}")

try:
    from vnstock import stock_historical_data
    print("stock_historical_data imported successfully")
except ImportError as e:
    print(f"Failed to import stock_historical_data: {e}")

try:
    from vnstock import listing_companies
    print("listing_companies imported successfully")
except ImportError as e:
    print(f"Failed to import listing_companies: {e}")
