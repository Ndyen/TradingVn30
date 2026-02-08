from vnstock import Quote

try:
    print("Init Quote...")
    quote = Quote(source='vci', show_log=True)
    print("Fetching History...")
    df = quote.history(symbol='ACB', start='2023-01-01', end='2023-01-10', interval='1D')
    print("Result:")
    print(df)
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
