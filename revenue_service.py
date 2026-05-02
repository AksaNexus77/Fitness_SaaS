"""
Revenue Forecasting Service for FitZone
Uses historical payment data to predict future revenue.
"""
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from models import db, Payment, RevenueForecast

class RevenueForecaster:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.model_version = "v1.0"
        
    def prepare_features(self):
        """Extract monthly revenue data for training."""
        # Get all payments
        payments = Payment.query.all()
        
        # Aggregate by month
        monthly_data = {}
        for payment in payments:
            month_key = payment.payment_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += payment.amount
        
        # Convert to sorted list
        sorted_months = sorted(monthly_data.keys())
        if len(sorted_months) < 3:
            return None, None
            
        X = []
        y = []
        for i, month_key in enumerate(sorted_months):
            X.append([i])  # Month index (0, 1, 2, ...)
            y.append(monthly_data[month_key])
        
        return np.array(X), np.array(y)
    
    def train_model(self):
        """Train the revenue forecasting model."""
        X, y = self.prepare_features()
        
        if X is None or len(X) < 3:
            print("Not enough data for revenue forecasting")
            return False
        
        # Use polynomial features for better trend capture
        poly = PolynomialFeatures(degree=2, include_bias=False)
        X_poly = poly.fit_transform(X)
        
        self.model = LinearRegression()
        self.model.fit(X_poly, y)
        self.is_trained = True
        print(f"Revenue forecast model trained on {len(X)} months of data")
        return True
    
    def predict_next_months(self, num_months=3):
        """Predict revenue for the next N months."""
        if not self.is_trained:
            self.train_model()
            
        if not self.is_trained:
            return []
        
        # Get feature data to know current month index
        X, y = self.prepare_features()
        if X is None:
            return []
        
        current_index = len(X)
        predictions = []
        
        for i in range(num_months):
            month_index = current_index + i
            X_pred = np.array([[month_index]])
            poly = PolynomialFeatures(degree=2, include_bias=False)
            X_pred_poly = poly.fit_transform(X_pred)
            
            predicted = self.model.predict(X_pred_poly)[0]
            # Ensure non-negative
            predicted = max(0, predicted)
            
            # Calculate confidence interval (wider for further predictions)
            base_std = np.std(y) if len(y) > 1 else 100
            uncertainty = base_std * (1 + i * 0.3)  # 30% more uncertainty per month
            
            # Calculate future month date
            future_date = date.today() + timedelta(days=30 * (i + 1))
            future_month = date(future_date.year, future_date.month, 1)
            
            predictions.append({
                'month': future_month.strftime('%B %Y'),
                'predicted_revenue': round(predicted, 2),
                'confidence_low': round(predicted - uncertainty, 2),
                'confidence_high': round(predicted + uncertainty, 2)
            })
            
            # Save to database
            forecast = RevenueForecast(
                forecast_month=future_month,
                predicted_revenue=predicted,
                confidence_low=predicted - uncertainty,
                confidence_high=predicted + uncertainty,
                model_version=self.model_version
            )
            db.session.add(forecast)
        
        db.session.commit()
        return predictions
    
    def get_historical_trend(self, months=6):
        """Get historical revenue trend for display."""
        payments = Payment.query.all()
        
        # Aggregate by month
        monthly_data = {}
        for payment in payments:
            month_key = payment.payment_date.strftime('%Y-%m')
            if month_key not in monthly_data:
                monthly_data[month_key] = 0
            monthly_data[month_key] += payment.amount
        
        # Sort and get last N months
        sorted_months = sorted(monthly_data.keys())[-months:]
        
        return [{
            'month': m,
            'revenue': round(monthly_data[m], 2)
        } for m in sorted_months]


# Global revenue forecaster
revenue_forecaster = RevenueForecaster()
