"""
Churn Prediction Service for FitZone
Uses scikit-learn to predict member churn based on attendance, payment, and membership data.
"""
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from models import db, Member, Attendance, Payment, Invoice, ProgressRecord

class ChurnPredictor:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def prepare_features(self):
        """Extract features for each member for churn prediction."""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Get all active members
        members = Member.query.filter_by(is_active=True).all()
        
        features_list = []
        labels_list = []
        churn_count = 0
        
        for member in members:
            # Feature 1: Attendance frequency (last 30 days)
            recent_attendance = Attendance.query.filter(
                Attendance.member_id == member.id,
                Attendance.check_in >= thirty_days_ago
            ).count()
            
            # Feature 2: Days since last visit
            last_attendance = Attendance.query.filter_by(
                member_id=member.id
            ).order_by(Attendance.check_in.desc()).first()
            
            if last_attendance:
                days_since_last_visit = (today - last_attendance.check_in.date()).days
            else:
                days_since_last_visit = 999  # Large number if never attended
            
            # Feature 3: Payment history (average payment amount over last 3 months)
            three_months_ago = today - timedelta(days=90)
            recent_payments = Payment.query.filter(
                Payment.member_id == member.id,
                Payment.payment_date >= three_months_ago
            ).all()
            
            if recent_payments:
                avg_payment_amount = np.mean([p.amount for p in recent_payments])
                payment_count = len(recent_payments)
            else:
                avg_payment_amount = 0
                payment_count = 0
            
            # Feature 4: Membership type (encoded)
            membership_type_map = {'monthly': 0, 'quarterly': 1, 'yearly': 2}
            membership_encoded = membership_type_map.get(member.membership_type, 0)
            
            # Feature 5: Membership duration (days since start)
            if member.membership_start:
                membership_duration = (today - member.membership_start).days
            else:
                membership_duration = 0
                
            # Feature 6: Overdue invoices count
            overdue_invoices = Invoice.query.filter(
                Invoice.member_id == member.id,
                Invoice.status == 'pending',
                Invoice.due_date < today
            ).count()
            
            # Feature 7: Has progress records (indicates engagement)
            progress_count = ProgressRecord.query.filter_by(member_id=member.id).count()
            
            # Create feature vector
            features = [
                recent_attendance,
                days_since_last_visit,
                avg_payment_amount,
                payment_count,
                membership_encoded,
                membership_duration,
                overdue_invoices,
                progress_count
            ]
            
            # Label: 1 if churned (no visit in last 30 days AND overdue invoice OR membership ended)
            # This is a simplified label for training - in practice you'd use historical churn data
            is_churned = 0
            if days_since_last_visit > 30:
                if overdue_invoices > 0 or (member.membership_end and member.membership_end < today):
                    is_churned = 1
                    churn_count += 1
                # Additionally, if no payment in last 3 months and no visit in over 45 days, consider at risk
                elif payment_count == 0 and days_since_last_visit > 45:
                    is_churned = 1
                    churn_count += 1
                # For testing: if attendance is zero in last 30 days and no progress records, consider at risk
                elif recent_attendance == 0 and progress_count == 0 and days_since_last_visit > 15:
                    is_churned = 1
                    churn_count += 1
            
            features_list.append(features)
            labels_list.append(is_churned)
         
        # If we have no churned examples, we need to create some for the model to train (for demo purposes)
        if churn_count == 0 and len(labels_list) >= 2:
            # Label the first two members as churned to ensure we have two classes
            labels_list[0] = 1
            labels_list[1] = 1
            churn_count = 2
            print("Warning: No natural churn cases found. Labeling first two members as churned for training.")
         
        print(f"Churn prediction: Total members: {len(members)}, Churned (label=1): {churn_count}")
         
        if not features_list:
            return None, None
            
        return np.array(features_list), np.array(labels_list)
    
    def train_model(self):
        """Train the churn prediction model."""
        X, y = self.prepare_features()
        
        if X is None or len(X) < 10:  # Need minimum samples
            print("Not enough data to train churn model")
            return False
            
        # Create and train pipeline
        self.model = make_pipeline(
            StandardScaler(),
            LogisticRegression(random_state=42, max_iter=1000)
        )
        
        self.model.fit(X, y)
        self.is_trained = True
        print(f"Churn model trained on {len(X)} members")
        return True
    
    def predict_churn_probability(self, member_id):
        """Predict churn probability for a specific member."""
        if not self.is_trained:
            self.train_model()
            
        if not self.is_trained:
            return 0.5  # Default if model not trained
        
        # Get member data
        member = Member.query.get(member_id)
        if not member:
            return 0.5
            
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)
        
        # Extract same features as in training
        recent_attendance = Attendance.query.filter(
            Attendance.member_id == member.id,
            Attendance.check_in >= thirty_days_ago
        ).count()
        
        last_attendance = Attendance.query.filter_by(
            member_id=member.id
        ).order_by(Attendance.check_in.desc()).first()
        
        if last_attendance:
            days_since_last_visit = (today - last_attendance.check_in.date()).days
        else:
            days_since_last_visit = 999
        
        three_months_ago = today - timedelta(days=90)
        recent_payments = Payment.query.filter(
            Payment.member_id == member.id,
            Payment.payment_date >= three_months_ago
        ).all()
        
        if recent_payments:
            avg_payment_amount = np.mean([p.amount for p in recent_payments])
            payment_count = len(recent_payments)
        else:
            avg_payment_amount = 0
            payment_count = 0
        
        membership_type_map = {'monthly': 0, 'quarterly': 1, 'yearly': 2}
        membership_encoded = membership_type_map.get(member.membership_type, 0)
        
        if member.membership_start:
            membership_duration = (today - member.membership_start).days
        else:
            membership_duration = 0
            
        overdue_invoices = Invoice.query.filter(
            Invoice.member_id == member.id,
            Invoice.status == 'pending',
            Invoice.due_date < today
        ).count()
        
        progress_count = ProgressRecord.query.filter_by(member_id=member.id).count()
        
        features = np.array([[
            recent_attendance,
            days_since_last_visit,
            avg_payment_amount,
            payment_count,
            membership_encoded,
            membership_duration,
            overdue_invoices,
            progress_count
        ]])
        
        # Get probability of churn (class 1)
        churn_prob = self.model.predict_proba(features)[0][1]
        return churn_prob
    
    def get_high_risk_members(self, threshold=0.7):
        """Get list of members with churn probability above threshold."""
        if not self.is_trained:
            self.train_model()
            
        members = Member.query.filter_by(is_active=True).all()
        high_risk = []
        
        for member in members:
            prob = self.predict_churn_probability(member.id)
            if prob >= threshold:
                high_risk.append({
                    'member': member,
                    'churn_probability': prob
                })
        
        # Sort by probability descending
        high_risk.sort(key=lambda x: x['churn_probability'], reverse=True)
        return high_risk

# Global predictor instance
churn_predictor = ChurnPredictor()