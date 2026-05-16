"""
main.py
========================================
Interactive menu - Run this file
"""

from config import DATA_FOLDER
from aerosol_analyzer import AerosolDataAnalyzer
import os
import matplotlib.pyplot as plt

def main():
    print("="*70)
    print("🌤️  AEROSOL DATA ANALYZER - MODULAR VERSION")
    print("="*70)
    print("✅ Days managed via config.py (easy to add/remove)")
    print("="*70)
    
    analyzer = AerosolDataAnalyzer()
    
    if len(analyzer.data_cache) == 0:
        print("\n❌ No data loaded! Check your files in config.py")
        return
    
    print("\n" + "="*70)
    print("📊 ANALYSIS MENU")
    print("="*70)
    
    while True:
        print(f"\n📍 CURRENT DAY: {analyzer.current_day}")
        if analyzer.current_time_range:
            print(f"⏱️ TIME RANGE: Profiles {analyzer.current_time_range[0]} to {analyzer.current_time_range[1]}")
        else:
            print(f"⏱️ TIME RANGE: All profiles (1-25)")
        layer_text = {"boundary": "BOUNDARY LAYER ONLY", "aerosol": "AEROSOL LAYER ONLY", "both": "BOTH LAYERS"}
        print(f"🎯 LAYER TYPE: {layer_text[analyzer.current_layer_type]}")
        print("\n" + "-"*50)
        print("  1. 📈 Show detailed plot (using current settings)")
        print("  2. 🔄 Switch to a different day")
        print("  3. ⏱️ Set time range (1-25 profiles)")
        print("  4. 🎯 Select layer type (Boundary/Aerosol/Both)")
        print("  5. 📊 Show layer summary plot (all days)")
        print("  6. 🌍 Compare all days side-by-side")
        print("  7. 💾 Save current day plot to file")
        print("  8. 🚪 Exit")
        print("-"*50)
        
        choice = input("\n👉 Enter choice (1-8): ").strip()
        
        if choice == '1':
            print(f"\n📊 Generating detailed plot for Day {analyzer.current_day}...")
            fig = analyzer.plot_day_profile()
            if fig:
                plt.show()
        elif choice == '2':
            print(f"Available days: {list(analyzer.data_cache.keys())}")
            try:
                day = int(input("Enter day number: "))
                if analyzer.switch_day(day):
                    print(f"✅ Switched to Day {day}")
                    summary = analyzer.get_layer_summary(day)
                    print(f"   🌿 Boundary: {summary['boundary_layer']:.0f}m" if summary['boundary_layer'] else "   🌿 Boundary: Not detected")
                    print(f"   ☁️ Aerosol : {summary['aerosol_layer']:.0f}m" if summary['aerosol_layer'] else "   ☁️ Aerosol : Not detected")
            except ValueError:
                print("❌ Invalid input")
        elif choice == '3':
            # (same time range code as before)
            print("\n⏱️ SET TIME RANGE (Profiles 1-25)")
            time_input = input("Enter start and end (or 0 to reset): ").strip()
            if time_input == '0':
                analyzer.current_time_range = None
                print("✅ Time range reset to ALL profiles")
            else:
                try:
                    start, end = map(int, time_input.split())
                    if 1 <= start <= 25 and 1 <= end <= 25 and start <= end:
                        analyzer.set_time_range(start, end)
                    else:
                        print("❌ Invalid range")
                except:
                    print("❌ Invalid input")
        elif choice == '4':
            # (same layer type code as before)
            print("\n🎯 SELECT LAYER TYPE:")
            print("   1. Boundary Layer ONLY")
            print("   2. Aerosol Layer ONLY")
            print("   3. Both Layers")
            ch = input("Enter 1-3: ").strip()
            if ch == '1': analyzer.set_layer_type('boundary')
            elif ch == '2': analyzer.set_layer_type('aerosol')
            elif ch == '3': analyzer.set_layer_type('both')
        elif choice == '5':
            fig = analyzer.plot_layer_summary()
            if fig: plt.show()
        elif choice == '6':
            fig = analyzer.plot_all_days_comparison()
            if fig: plt.show()
        elif choice == '7':
            fig = analyzer.plot_day_profile(save_fig=True)
            if fig:
                plt.close(fig)
                print(f"✅ Saved as day_{analyzer.current_day}_analysis.png")
        elif choice == '8':
            print("\n👋 Thank you for using Aerosol Data Analyzer!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    if not os.path.exists(DATA_FOLDER):
        print(f"❌ Folder not found: {DATA_FOLDER}")
        print("   Update DATA_FOLDER in config.py")
    else:
        os.chdir(DATA_FOLDER)
        print(f"✅ Working directory: {os.getcwd()}")
        main()