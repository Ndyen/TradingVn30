from vnstock import Quote
import traceback
import sys

# Redirect stdout/stderr
sys.stdout = open("quote_debug.log", "w", encoding="utf-8")
sys.stderr = sys.stdout

symbols = ['ACB', 'HOSE:ACB', 'ACB.VN', 'VN30']

print("Init Quote...")
try:
    quote = Quote(source='vci', show_log=True)
    
    for s in symbols:
        print(f"Testing {s}...")
        try:
            df = quote.history(symbol=s, start='2023-01-01', end='2023-01-10', interval='1D')
            if df is not None:
                print(f"Success for {s}: {len(df)} rows")
            else:
                print(f"Success for {s}: None returned")
        except Exception as e:
            print(f"Failed for {s}: {e}")
            traceback.print_exc()
            
except Exception as e:
    print(f"Init failed: {e}")
    traceback.print_exc()
