from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Base user model for authentication."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # admin, trainer, member
    phone = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    profile_image = db.Column(db.String(255), default='default-avatar.png')
    
    # Relationships
    member = db.relationship('Member', backref='user', uselist=False, lazy=True)
    trainer = db.relationship('Trainer', backref='user', uselist=False, lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class Member(db.Model):
    """Member profile and details."""
    __tablename__ = 'members'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    membership_type = db.Column(db.String(50))  # monthly, quarterly, yearly
    membership_start = db.Column(db.Date)
    membership_end = db.Column(db.Date)
    height = db.Column(db.Float)  # in cm
    weight = db.Column(db.Float)  # in kg
    fitness_goal = db.Column(db.String(100))
    medical_conditions = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    progress_records = db.relationship('ProgressRecord', backref='member', lazy=True, cascade='all, delete-orphan')
    attendance = db.relationship('Attendance', backref='member', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='member', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Member {self.user_id}>'


class Trainer(db.Model):
    """Trainer profile and details."""
    __tablename__ = 'trainers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialization = db.Column(db.String(100))  # yoga, cardio, weight training, etc.
    experience_years = db.Column(db.Integer)
    certification = db.Column(db.String(255))
    bio = db.Column(db.Text)
    hourly_rate = db.Column(db.Float)
    is_available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    classes = db.relationship('Class', backref='trainer', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Trainer {self.user_id}>'


class Attendance(db.Model):
    """Track member attendance."""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    check_out = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Attendance {self.id} - Member {self.member_id}>'


class ProgressRecord(db.Model):
    """Track member fitness progress."""
    __tablename__ = 'progress_records'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    record_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    weight = db.Column(db.Float)
    body_fat_percentage = db.Column(db.Float)
    chest = db.Column(db.Float)
    waist = db.Column(db.Float)
    hips = db.Column(db.Float)
    biceps = db.Column(db.Float)
    thighs = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProgressRecord {self.id} - Member {self.member_id}>'


class Invoice(db.Model):
    """Generate and track invoices."""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, paid, overdue, cancelled
    due_date = db.Column(db.Date)
    issued_date = db.Column(db.Date, default=datetime.utcnow().date())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    member = db.relationship('Member', backref='invoices', lazy=True)
    payments = db.relationship('Payment', backref='invoice', lazy=True)
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'


class Payment(db.Model):
    """Track payments."""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'))
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50))  # cash, card, bank_transfer
    payment_date = db.Column(db.Date, default=datetime.utcnow().date())
    transaction_id = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Payment {self.id}>'


class Class(db.Model):
    """Fitness classes."""
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainers.id'))
    day_of_week = db.Column(db.Integer)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    max_participants = db.Column(db.Integer, default=20)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Class {self.name}>'


class WorkoutPlan(db.Model):
    """AI-generated workout plans for members."""
    __tablename__ = 'workout_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    plan_content = db.Column(db.Text, nullable=False)
    fitness_goal = db.Column(db.String(100))
    duration_weeks = db.Column(db.Integer, default=4)
    ai_model = db.Column(db.String(50), default='gemini')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='workout_plans', lazy=True)
    
    def __repr__(self):
        return f'<WorkoutPlan {self.title}>'


class ChatMessage(db.Model):
    """Store chatbot conversations."""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='chat_messages', lazy=True)
    
    def __repr__(self):
        return f'<ChatMessage {self.role}>'


class PaymentReminder(db.Model):
    """AI-generated payment reminders."""
    __tablename__ = 'payment_reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    reminder_message = db.Column(db.Text, nullable=False)
    tone = db.Column(db.String(20), default='professional')  # friendly, firm, professional
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='payment_reminders', lazy=True)
    invoice = db.relationship('Invoice', backref='payment_reminders', lazy=True)
    
    def __repr__(self):
        return f'<PaymentReminder {self.id}>'


class NutritionLog(db.Model):
    """Track member nutrition from food photos (AI-analyzed)."""
    __tablename__ = 'nutrition_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    photo_url = db.Column(db.String(500))  # URL to uploaded photo
    food_description = db.Column(db.Text)  # AI-detected food items
    calories = db.Column(db.Integer)  # Estimated calories
    protein = db.Column(db.Float)  # grams
    carbs = db.Column(db.Float)  # grams
    fat = db.Column(db.Float)  # grams
    meal_type = db.Column(db.String(20))  # breakfast, lunch, dinner, snack
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='nutrition_logs', lazy=True)
    
    def __repr__(self):
        return f'<NutritionLog {self.id} - {self.food_description[:30]}>'


class GoalSuggestion(db.Model):
    """AI-generated smart goal suggestions based on progress."""
    __tablename__ = 'goal_suggestions'
    
    id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer, db.ForeignKey('members.id'), nullable=False)
    current_goal = db.Column(db.String(100))  # Current fitness goal
    suggested_goal = db.Column(db.String(100))  # AI-suggested new goal
    reasoning = db.Column(db.Text)  # Why this suggestion
    progress_summary = db.Column(db.Text)  # Based on recent progress
    is_accepted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    member = db.relationship('Member', backref='goal_suggestions', lazy=True)
    
    def __repr__(self):
        return f'<GoalSuggestion {self.id} - {self.suggested_goal}>'


class RevenueForecast(db.Model):
    """Revenue forecasts from ML model."""
    __tablename__ = 'revenue_forecasts'
    
    id = db.Column(db.Integer, primary_key=True)
    forecast_month = db.Column(db.Date, nullable=False)  # Month being forecasted
    predicted_revenue = db.Column(db.Float, nullable=False)
    confidence_low = db.Column(db.Float)  # Lower bound
    confidence_high = db.Column(db.Float)  # Upper bound
    model_version = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<RevenueForecast {self.forecast_month}>'
