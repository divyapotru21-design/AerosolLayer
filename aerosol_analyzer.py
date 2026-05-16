"""
aerosol_analyzer.py
========================================
CORE ANALYSIS CLASS - DO NOT EDIT
(Only edit config.py to add/remove days)
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os
import warnings
warnings.filterwarnings('ignore')

from config import day_files, stats_files


class AerosolDataAnalyzer:
    """Complete aerosol data analysis tool with time range selection"""
    
    def __init__(self):
        self.day_files = day_files
        self.stats_files = stats_files
        self.data_cache = {}
        self.stats_cache = {}
        self.current_day = 1
        self.current_time_range = None
        self.current_layer_type = 'both'
        self.load_all_data()
    
    def load_all_data(self):
        """Load all data files with error handling"""
        loaded_count = 0
        total_days = len(self.day_files)
        
        for day, filepath in self.day_files.items():
            try:
                if not os.path.exists(filepath):
                    print(f"⚠️ File not found: {filepath}")
                    continue
                
                df = pd.read_excel(filepath)
                x_values = df.iloc[:, 0].values
                y_values = df.iloc[:, 1:].values
                
                self.data_cache[day] = {'x': x_values, 'y': y_values}
                
                if day in self.stats_files and os.path.exists(self.stats_files[day]):
                    stats = pd.read_csv(self.stats_files[day], sep="\t", header=None)
                    stats = stats.apply(pd.to_numeric, errors='coerce')
                    stats_mean = stats.iloc[:, 0].values[:len(x_values)]
                    stats_std = stats.iloc[:, 1].values[:len(x_values)]
                    self.stats_cache[day] = {'mean': stats_mean, 'std': stats_std}
                    print(f"✅ Loaded Day {day} (with stats file)")
                else:
                    self.stats_cache[day] = {
                        'mean': np.nanmean(y_values, axis=1),
                        'std': np.nanstd(y_values, axis=1)
                    }
                    print(f"✅ Loaded Day {day} (calculated stats)")
                loaded_count += 1
            except Exception as e:
                print(f"❌ Error loading Day {day}: {str(e)}")
        
        print(f"\n✅ Successfully loaded {loaded_count}/{total_days} days\n")
    
    def get_data(self, day=None):
        if day is None:
            day = self.current_day
        return self.data_cache.get(day), self.stats_cache.get(day)
    
    def switch_day(self, day):
        if day in self.data_cache:
            self.current_day = day
            return True
        return False
    
    def set_time_range(self, start_profile, end_profile):
        self.current_time_range = (start_profile, end_profile)
        print(f"✅ Time range set: Profiles {start_profile} to {end_profile}")
    
    def set_layer_type(self, layer_type):
        if layer_type in ['boundary', 'aerosol', 'both']:
            self.current_layer_type = layer_type
            msg = {"boundary": "BOUNDARY LAYER ONLY", "aerosol": "AEROSOL LAYER ONLY", "both": "BOTH LAYERS"}
            print(f"✅ Layer type set to: {msg[layer_type]}")
            return True
        return False
    
    def get_profiles_in_range(self, day=None):
        if day is None:
            day = self.current_day
        data = self.data_cache.get(day)
        if data is None:
            return None, None
        y_data = data['y']
        if self.current_time_range is None:
            return data['x'], y_data
        start, end = self.current_time_range
        start_idx = max(0, start - 1)
        end_idx = min(y_data.shape[1], end)
        if start_idx >= end_idx:
            return data['x'], y_data
        selected_profiles = y_data[:, start_idx:end_idx]
        print(f"📊 Selected profiles {start} to {end} (Total: {selected_profiles.shape[1]} profiles)")
        return data['x'], selected_profiles
    
    def detect_boundary_layer(self, day=None, profiles=None):
        if profiles is not None:
            mean_profile = np.nanmean(profiles, axis=1)
        else:
            _, stats = self.get_data(day)
            mean_profile = stats['mean'] if stats else None
        if mean_profile is None:
            return None
        data = self.data_cache.get(day or self.current_day)
        if data is None:
            return None
        x = data['x']
        valid_idx = ~np.isnan(mean_profile)
        x_valid = x[valid_idx]
        mean_valid = mean_profile[valid_idx]
        if len(x_valid) == 0:
            return None
        lower_mask = (x_valid >= 0) & (x_valid <= 2000)
        if not np.any(lower_mask):
            return None
        x_lower = x_valid[lower_mask]
        mean_lower = mean_valid[lower_mask]
        gradient = np.gradient(mean_lower, x_lower)
        grad_abs = np.abs(gradient)
        if len(grad_abs) > 0:
            max_grad_idx = np.argmax(grad_abs)
            return x_lower[max_grad_idx]
        return None
    
    def detect_aerosol_layer(self, day=None, profiles=None):
        if profiles is not None:
            mean_profile = np.nanmean(profiles, axis=1)
        else:
            _, stats = self.get_data(day)
            mean_profile = stats['mean'] if stats else None
        if mean_profile is None:
            return None
        data = self.data_cache.get(day or self.current_day)
        if data is None:
            return None
        x = data['x']
        valid_idx = ~np.isnan(mean_profile)
        x_valid = x[valid_idx]
        mean_valid = mean_profile[valid_idx]
        if len(x_valid) == 0:
            return None
        positive_mask = x_valid >= 300
        x_pos = x_valid[positive_mask]
        mean_pos = mean_valid[positive_mask]
        if len(mean_pos) == 0:
            return None
        max_signal = np.max(mean_pos)
        threshold = max_signal * 0.65
        above_threshold = mean_pos > threshold
        if np.any(above_threshold):
            return x_pos[above_threshold][0]
        return None
    
    def get_layer_summary(self, day=None):
        if day is None:
            day = self.current_day
        _, y_selected = self.get_profiles_in_range(day)
        bl = self.detect_boundary_layer(day, y_selected)
        al = self.detect_aerosol_layer(day, y_selected)
        summary = {'day': day, 'boundary_layer': bl, 'aerosol_layer': al}
        summary['separation'] = al - bl if bl is not None and al is not None else None
        return summary
    
    # ===================================================================
    # PLOTTING METHODS
    # ===================================================================
    def plot_day_profile(self, day=None, height_range=(0, 6000), save_fig=False):
        if day is None:
            day = self.current_day
        data, _ = self.get_data(day)
        if data is None:
            print(f"❌ No data for Day {day}")
            return None
        x, y_selected = self.get_profiles_in_range(day)
        if x is None:
            return None
        mean_profile = np.nanmean(y_selected, axis=1)
        std_profile = np.nanstd(y_selected, axis=1)
        valid_mask = ~np.isnan(mean_profile)
        x_clean = x[valid_mask]
        mean_clean = mean_profile[valid_mask]
        std_clean = std_profile[valid_mask]
        if height_range:
            range_mask = (x_clean >= height_range[0]) & (x_clean <= height_range[1])
            x_filt = x_clean[range_mask]
            mean_filt = mean_clean[range_mask]
            std_filt = std_clean[range_mask]
            y_filt = y_selected[valid_mask, :][range_mask, :]
        else:
            x_filt = x_clean
            mean_filt = mean_clean
            std_filt = std_clean
            y_filt = y_selected[valid_mask, :]
        if len(x_filt) == 0:
            print(f"❌ No data in selected height range for Day {day}")
            return None
        bl = self.detect_boundary_layer(day, y_selected) if self.current_layer_type in ['boundary', 'both'] else None
        al = self.detect_aerosol_layer(day, y_selected) if self.current_layer_type in ['aerosol', 'both'] else None
        fig = plt.figure(figsize=(18, 10))
        # Panel 1
        ax1 = plt.subplot(2, 3, 1)
        n_profiles = min(y_filt.shape[1], 20)
        for i in range(n_profiles):
            ax1.plot(x_filt, y_filt[:, i], 'lightblue', alpha=0.25, linewidth=0.7)
        ax1.plot(x_filt, mean_filt, 'red', linewidth=2.5, label='Mean Profile')
        ax1.set_xlabel('Height (m)')
        ax1.set_ylabel('Signal (m)')
        title = f'Day {day} - Profiles {self.current_time_range[0]}-{self.current_time_range[1]}' if self.current_time_range else f'Day {day} - All Profiles'
        ax1.set_title(title, fontweight='bold')
        ax1.grid(True, alpha=0.3, linestyle='--')
        ax1.set_xlim(0, 6000)
        ax1.legend(loc='upper right')
        # Panel 2
        ax2 = plt.subplot(2, 3, 2)
        ax2.plot(x_filt, mean_filt, 'red', linewidth=2.5, label='Mean Profile')
        step = max(1, len(mean_filt) // 35)
        sample_idx = np.arange(0, len(mean_filt), step)
        if len(sample_idx) > 0:
            ax2.errorbar(x_filt[sample_idx], mean_filt[sample_idx], yerr=std_filt[sample_idx], fmt='ro', capsize=3, markersize=3, alpha=0.5, label='±1 Std Dev')
        if self.current_layer_type in ['boundary', 'both'] and bl and bl > 0:
            ax2.axvline(bl, color='green', linestyle='--', linewidth=2, label=f'Boundary Layer: {bl:.0f}m')
            ax2.axvspan(bl-50, bl+50, alpha=0.2, color='green')
        if self.current_layer_type in ['aerosol', 'both'] and al and al > 0:
            ax2.axvline(al, color='orange', linestyle='--', linewidth=2, label=f'Aerosol Layer: {al:.0f}m')
            ax2.axvspan(al-50, al+50, alpha=0.2, color='orange')
        ax2.set_xlabel('Height (m)')
        ax2.set_ylabel('Signal (m)')
        layer_title = "BOUNDARY LAYER ONLY" if self.current_layer_type == 'boundary' else "AEROSOL LAYER ONLY" if self.current_layer_type == 'aerosol' else "BOTH LAYERS"
        ax2.set_title(f'Day {day} - Mean Profile ({layer_title})', fontweight='bold')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.set_xlim(0, 6000)
        ax2.legend(loc='upper right')
        # Panel 3
        ax3 = plt.subplot(2, 3, 3)
        gradient = np.gradient(mean_filt, x_filt)
        ax3.plot(x_filt, np.abs(gradient), 'purple', linewidth=2)
        if bl:
            ax3.axvline(bl, color='green', linestyle='--', linewidth=2, alpha=0.7)
        ax3.set_xlabel('Height (m)')
        ax3.set_ylabel('|d(Signal)/d(Height)|')
        ax3.set_title('Signal Gradient - Boundary Layer Dropoff Point', fontweight='bold')
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.set_xlim(0, 6000)
        # Panel 4
        ax4 = plt.subplot(2, 3, 4)
        max_height = 3000
        ax4.add_patch(Rectangle((0, 0), max_height, 1, facecolor='lightblue', alpha=0.3))
        ax4.add_patch(Rectangle((0, 0), 80, 1, facecolor='#8B4513', alpha=0.8))
        ax4.text(40, 0.5, 'GROUND', ha='center', va='center', fontsize=8, color='white', fontweight='bold', rotation=90)
        if self.current_layer_type in ['boundary', 'both'] and bl and bl > 0 and bl <= max_height:
            bl_h = min(bl, max_height)
            ax4.add_patch(Rectangle((80, 0), bl_h - 80, 1, facecolor='lightgreen', alpha=0.6))
            ax4.text(80 + (bl_h - 80)/2, 0.5, f'BOUNDARY LAYER\n(0 to {bl:.0f}m)', ha='center', va='center', fontsize=8, fontweight='bold')
            ax4.axvline(bl, color='green', linewidth=2, linestyle='--')
            ax4.text(bl + 10, 0.5, f'BL: {bl:.0f}m', fontsize=7, color='green')
        if self.current_layer_type in ['aerosol', 'both'] and al and al > 0 and al <= max_height:
            al_center = min(al, max_height)
            al_start = max(0, al_center - 60)
            al_end = min(max_height, al_center + 60)
            ax4.add_patch(Rectangle((al_start, 0), al_end - al_start, 1, facecolor='orange', alpha=0.6))
            ax4.text(al_center, 0.5, f'AEROSOL LAYER\n({al-60:.0f}-{al+60:.0f}m)', ha='center', va='center', fontsize=8, fontweight='bold')
            ax4.axvline(al, color='orange', linewidth=2, linestyle='--')
            ax4.text(al + 10, 0.5, f'AL: {al:.0f}m', fontsize=7, color='orange')
        ax4.set_xlim(0, max_height)
        ax4.set_ylim(0, 1)
        ax4.set_xlabel('Height (m)')
        ax4.set_title('Atmospheric Layer Structure', fontweight='bold')
        ax4.set_yticks([])
        # Panel 5
        ax5 = plt.subplot(2, 3, 5)
        valid_percentage = 100 * np.sum(~np.isnan(y_filt)) / y_filt.size if y_filt.size > 0 else 100
        missing_percentage = 100 - valid_percentage
        ax5.pie([valid_percentage, missing_percentage], labels=['Valid Data', 'Missing/NaN'], colors=['#4CAF50', '#FF5722'], autopct='%1.1f%%', startangle=90)
        ax5.set_title('Data Quality Check', fontweight='bold')
        # Panel 6
        ax6 = plt.subplot(2, 3, 6)
        ax6.axis('off')
        bl_str = f"{bl:.0f} m" if bl else "Not detected"
        al_str = f"{al:.0f} m" if al else "Not detected"
        sep_str = f"{al - bl:.0f} m" if (bl and al) else "N/A"
        time_info = f"Profiles: {self.current_time_range[0]}-{self.current_time_range[1]}" if self.current_time_range else "All profiles"
        selected_info = "BOUNDARY LAYER ONLY" if self.current_layer_type == 'boundary' else "AEROSOL LAYER ONLY" if self.current_layer_type == 'aerosol' else "BOTH LAYERS"
        info_text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
         LAYER INFORMATION - DAY {day}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏱️ TIME RANGE:
   • {time_info}

🌿 BOUNDARY LAYER:
   • Height: {bl_str}

☁️ AEROSOL LAYER:
   • Height: {al_str}

📏 SEPARATION:
   • Distance: {sep_str}

📊 SELECTED VIEW: {selected_info}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        """
        ax6.text(0.5, 0.5, info_text, transform=ax6.transAxes, fontsize=9, va='center', ha='center', fontfamily='monospace', linespacing=1.4,
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9))
        plt.suptitle(f'🌤️ AEROSOL DATA ANALYSIS - DAY {day}', fontsize=18, fontweight='bold', y=0.98)
        plt.tight_layout()
        if save_fig:
            filename = f'day_{day}_analysis.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            print(f"✅ Saved: {filename}")
        return fig
    
    def plot_all_days_comparison(self, save_fig=False):
        """Create accurate comparison plot for all days (uses full data)"""
        days = sorted(self.data_cache.keys())
        n_days = len(days)
        
        fig, axes = plt.subplots(n_days, 2, figsize=(16, 4*n_days))
        if n_days == 1:
            axes = axes.reshape(1, -1)
        
        print("\n📊 Generating comparison for all days:")
        for idx, day in enumerate(days):
            data, stats = self.get_data(day)
            if data is None:
                continue
            x = data['x']
            mean_profile = stats['mean'][:len(x)]
            valid = ~np.isnan(mean_profile)
            x_valid = x[valid]
            mean_valid = mean_profile[valid]
            
            bl = self.detect_boundary_layer(day)
            al = self.detect_aerosol_layer(day)
            print(f"   Day {day}: BL={bl if bl else 'None'} m, AL={al if al else 'None'} m")
            
            # Left column: Mean Profile
            ax1 = axes[idx, 0]
            ax1.plot(x_valid, mean_valid, 'b-', linewidth=2)
            if bl is not None:
                ax1.axvline(x=bl, color='green', linestyle='--', linewidth=2)
                ax1.text(bl, max(mean_valid)*0.9, f'BL: {bl:.0f}m', fontsize=9, color='green', ha='center', fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
            if al is not None:
                ax1.axvline(x=al, color='orange', linestyle='--', linewidth=2)
                ax1.text(al, max(mean_valid)*0.8, f'AL: {al:.0f}m', fontsize=9, color='orange', ha='center', fontweight='bold',
                         bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7))
            
            ax1.set_xlabel('Height (m)', fontsize=10)
            ax1.set_ylabel('Signal (m)', fontsize=10)
            ax1.set_title(f'Day {day} - Mean Profile', fontsize=11, fontweight='bold')
            ax1.grid(True, alpha=0.3)
            ax1.set_xlim(0, 6000)
            
            # Right column: Layer Heights Bar Chart
            ax2 = axes[idx, 1]
            layers_data = []
            labels = []
            colors = []
            if bl is not None:
                layers_data.append(bl)
                labels.append('Boundary Layer')
                colors.append('green')
            if al is not None:
                layers_data.append(al)
                labels.append('Aerosol Layer')
                colors.append('orange')
            
            if layers_data:
                bars = ax2.bar(labels, layers_data, color=colors, alpha=0.7, edgecolor='black', linewidth=1)
                ax2.set_ylabel('Height (m)', fontsize=10)
                ax2.set_title(f'Day {day} - Layer Heights', fontsize=11, fontweight='bold')
                ax2.grid(True, alpha=0.3, axis='y')
                for bar, val in zip(bars, layers_data):
                    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 10,
                            f'{val:.0f}m', ha='center', va='bottom', fontsize=10, fontweight='bold')
            else:
                ax2.text(0.5, 0.5, 'No layers detected', ha='center', va='center', fontsize=12)
                ax2.set_title(f'Day {day} - No Layers Detected', fontsize=11)
        
        plt.suptitle('🌍 COMPARISON ACROSS ALL DAYS', fontsize=14, fontweight='bold')
        plt.tight_layout()
        
        if save_fig:
            plt.savefig('all_days_comparison.png', dpi=150, bbox_inches='tight')
            print("✅ Saved: all_days_comparison.png")
        
        return fig
    
    def plot_layer_summary(self, save_fig=False):
        """Create accurate layer summary plot for all days"""
        days = sorted(self.data_cache.keys())
        
        bl_heights = []
        al_heights = []
        valid_days = []
        
        print("\n📊 Detecting layers for each day:")
        for day in days:
            bl = self.detect_boundary_layer(day)
            al = self.detect_aerosol_layer(day)
            print(f"   Day {day}: BL={bl if bl else 'None'} m, AL={al if al else 'None'} m")
            
            bl_heights.append(bl if bl is not None else 0)
            al_heights.append(al if al is not None else 0)
            valid_days.append(day)
        
        fig = plt.figure(figsize=(16, 12))
        
        if len(valid_days) > 0:
            ax1 = plt.subplot(3, 2, 1)
            x_pos = np.arange(len(valid_days))
            width = 0.35
            
            bars1 = ax1.bar(x_pos - width/2, bl_heights, width, 
                           label='Boundary Layer (Dropoff)', color='green', alpha=0.7, edgecolor='darkgreen')
            bars2 = ax1.bar(x_pos + width/2, al_heights, width, 
                           label='Aerosol Layer', color='orange', alpha=0.7, edgecolor='darkorange')
            
            ax1.set_xlabel('Day', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Height (m)', fontsize=12, fontweight='bold')
            ax1.set_title('Layer Heights by Day', fontsize=14, fontweight='bold')
            ax1.set_xticks(x_pos)
            ax1.set_xticklabels([f'Day {d}' for d in valid_days])
            ax1.legend(fontsize=10)
            ax1.grid(True, alpha=0.3, axis='y')
            ax1.set_ylim(0, max(max(bl_heights, default=0), max(al_heights, default=0)) + 200)
            
            for i, (b, a) in enumerate(zip(bl_heights, al_heights)):
                if b > 0:
                    ax1.text(x_pos[i] - width/2, b + 15, f'{b:.0f}m', ha='center', va='bottom', fontsize=9, fontweight='bold')
                else:
                    ax1.text(x_pos[i] - width/2, 20, 'N/A', ha='center', va='bottom', fontsize=9, color='gray')
                if a > 0:
                    ax1.text(x_pos[i] + width/2, a + 15, f'{a:.0f}m', ha='center', va='bottom', fontsize=9, fontweight='bold')
                else:
                    ax1.text(x_pos[i] + width/2, 20, 'N/A', ha='center', va='bottom', fontsize=9, color='gray')
            
            ax2 = plt.subplot(3, 2, 2)
            ax2.plot(valid_days, bl_heights, 'go-', linewidth=2.5, markersize=10, 
                    label='Boundary Layer', markerfacecolor='green', markeredgecolor='darkgreen')
            ax2.plot(valid_days, al_heights, 'o-', color='orange', linewidth=2.5, markersize=10,
                    label='Aerosol Layer', markerfacecolor='orange', markeredgecolor='darkorange')
            
            ax2.set_xlabel('Day', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Height (m)', fontsize=12, fontweight='bold')
            ax2.set_title('Layer Height Trends', fontsize=14, fontweight='bold')
            ax2.set_xticks(valid_days)
            ax2.set_xticklabels([f'Day {d}' for d in valid_days])
            ax2.legend(fontsize=10)
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(0, max(max(bl_heights, default=0), max(al_heights, default=0)) + 200)
            
            ax3 = plt.subplot(3, 2, (3, 4))
            ax3.axis('off')
            
            table_data = []
            for i, day in enumerate(valid_days):
                bl = bl_heights[i]
                al = al_heights[i]
                sep = (al - bl) if (bl > 0 and al > 0) else 'N/A'
                table_data.append([f'Day {day}', 
                                  f'{bl:.0f}' if bl > 0 else 'N/A', 
                                  f'{al:.0f}' if al > 0 else 'N/A', 
                                  str(sep)])
            
            headers = ['Day', 'Boundary Layer (m)', 'Aerosol Layer (m)', 'Separation (m)']
            table = ax3.table(cellText=table_data, colLabels=headers,
                             cellLoc='center', loc='center', colWidths=[0.2, 0.3, 0.3, 0.2])
            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1, 2)
            
            for i in range(len(headers)):
                table[(0, i)].set_facecolor('#4CAF50')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            ax3.set_title('Detailed Layer Statistics', fontsize=14, fontweight='bold', pad=20)
            
            ax4 = plt.subplot(3, 1, 3)
            colors_profile = ['blue', 'red', 'green', 'purple', 'orange', 'brown']
            for idx, day in enumerate(days):
                data, stats = self.get_data(day)
                if data is None:
                    continue
                x = data['x']
                mean_profile = stats['mean'][:len(x)]
                valid = ~np.isnan(mean_profile)
                ax4.plot(x[valid], mean_profile[valid], 
                        color=colors_profile[idx % len(colors_profile)], 
                        linewidth=2, label=f'Day {day}')
            
            ax4.set_xlabel('Height (m)', fontsize=12, fontweight='bold')
            ax4.set_ylabel('Signal (m)', fontsize=12, fontweight='bold')
            ax4.set_title('Mean Profiles - All Days', fontsize=14, fontweight='bold')
            ax4.grid(True, alpha=0.3)
            ax4.set_xlim(0, 6000)
            ax4.legend(fontsize=10)
        
        else:
            ax1 = plt.subplot(1, 1, 1)
            ax1.text(0.5, 0.5, 'No layer data available for comparison', 
                    ha='center', va='center', fontsize=14)
            ax1.set_title('Layer Summary - No Data', fontsize=14, fontweight='bold')
        
        plt.suptitle('📊 AEROSOL LAYER SUMMARY - ALL DAYS', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        if save_fig:
            plt.savefig('layer_summary.png', dpi=150, bbox_inches='tight')
            print("✅ Saved: layer_summary.png")
        
        return fig