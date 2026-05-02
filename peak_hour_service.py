"""
Peak Hour Predictor for FitZone
Uses attendance data to predict busy vs quiet gym times.
"""
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from models import db, Attendance, Member

class PeakHourPredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.busy_hours = []
        self.quiet_hours = []
        
    def prepare_features(self):
        """Extract hour-of-day features from attendance data."""
        attendances = Attendance.query.filter(
            Attendance.check_in.isnot(None)
        ).all()
        
        if len(attendances) < 10:
            return None, None
        
        features_list = []
        labels_list = []  # 1 = busy, 0 = quiet
        
        # Calculate average attendance per hour
        hourly_counts = {}
        for att in attendances:
            hour = att.check_in.hour
            if hour not in hourly_counts:
                hourly_counts[hour] = 0
            hourly_counts[hour] += 1
        
        # Determine busy vs quiet thresholds
        if not hourly_counts:
            return None, None
            
        avg_per_hour = np.mean(list(hourly_counts.values()))
        
        # Create hourly binary labels
        for hour, count in hourly_counts.items():
            # Feature: hour, day of week (simplified)
            features = [hour, hour // 6]  # hour, time period (morning/afternoon/evening/night)
            label = 1 if count > avg_per_hour * 1.2 else 0  # 20% above average = busy
            features_list.append(features)
            labels_list.append(label)
        
        # Use all 24 hours even if no data
        for hour in range(24):
            if hour not in hourly_counts:
                features = [hour, hour // 6]
                features_list.append(features)
                labels_list.append(0)  # No data = assume quiet
        
        return np.array(features_list), np.array(labels_list)
    
    def train_model(self):
        """Train the peak hour prediction model."""
        X, y = self.prepare_features()
        
        if X is None or len(X) < 10:
            print("Not enough attendance data for peak hour prediction")
            return False
        
        # Use Random Forest for better pattern recognition
        self.model = make_pipeline(
            StandardScaler(),
            RandomForestClassifier(n_estimators=50, random_state=42)
        )
        
        self.model.fit(X, y)
        self.is_trained = True
        
        # Determine busy/quiet hours
        self._calculate_hour_patterns()
        
        print(f"Peak hour model trained on {len(X)} data points")
        return True
    
    def _calculate_hour_patterns(self):
        """Calculate which hours are typically busy vs quiet."""
        if not self.model:
            return
        
        # Predict for all 24 hours
        all_hours = np.array([[h, h // 6] for h in range(24)])
        predictions = self.model.predict(all_hours)
        
        self.busy_hours = [h for h, p in zip(range(24), predictions) if p == 1]
        self.quiet_hours = [h for h, p in zip(range(24), predictions) if p == 0]
    
    def get_peak_hours_today(self):
        """Get predicted peak hours for today."""
        if not self.is_trained:
            self.train_model()
            
        if not self.is_trained:
            return {'busy': [], 'quiet': []}
        
        return {
            'busy': self.busy_hours,
            'quiet': self.quiet_hours
        }
    
    def get_hourly_pattern(self):
        """Get detailed hourly pattern for the week."""
        # Get actual attendance data
        attendances = Attendance.query.all()
        
        hourly_stats = {}
        for att in attendances:
            hour = att.check_in.hour
            if hour not in hourly_stats:
                hourly_stats[hour] = {'count': 0, 'total_duration': 0}
            hourly_stats[hour]['count'] += 1
            if att.duration_minutes:
                hourly_stats[hour]['total_duration'] += att.duration_minutes
        
        # Format for display
        result = []
        for hour in range(24):
            stats = hourly_stats.get(hour, {'count': 0, 'total_duration': 0})
            avg_duration = stats['total_duration'] / stats['count'] if stats['count'] > 0 else 0
            
            # Classify the hour
            if stats['count'] == 0:
                classification = 'no-data'
            elif stats['count'] < 3:
                classification = 'quiet'
            elif stats['count'] < 8:
                classification = 'moderate'
            else:
                classification = 'busy'
            
            result.append({
                'hour': hour,
                'label': f"{hour:02d}:00",
                'checkins': stats['count'],
                'avg_duration': round(avg_duration, 1),
                'classification': classification
            })
        
        return result
    
    def suggest_schedule(self, class_duration=60):
        """Suggest optimal class times based on historical patterns."""
        hourly_pattern = self.get_hourly_pattern()
        
        # Find moderate hours (not too busy, not empty)
        moderate_hours = [
            h['hour'] for h in hourly_pattern 
            if h['classification'] == 'moderate'
        ]
        
        suggestions = []
        
        # Suggest morning slot
        if 6 in moderate_hours or 7 in moderate_hours:
            suggestions.append({
                'time': '06:00 - 07:00',
                'reason': 'Morning members arriving, moderate crowd',
                'optimal': True
            })
        
        # Suggest midday
        if 12 in moderate_hours or 13 in moderate_hours:
            suggestions.append({
                'time': '12:00 - 13:00', 
                'reason': 'Lunch break rush passed',
                'optimal': True
            })
        
        # Suggest evening
        if 18 in moderate_hours or 19 in moderate_hours:
            suggestions.append({
                'time': '18:00 - 19:00',
                'reason': 'Evening peak ending',
                'optimal': True
            })
        
        # Add warning for busy times
        busy = [h for h in hourly_pattern if h['classification'] == 'busy']
        if busy:
            warnings = [f"Avoid {h['label']} - typically busy" for h in busy[:3]]
            for s in suggestions:
                s['warnings'] = warnings
        
        return suggestions


# Global predictor
peak_hour_predictor = PeakHourPredictor()
