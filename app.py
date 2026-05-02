import os
import numpy as np
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, date, timedelta
from functools import wraps
import pymysql
from sqlalchemy import func, extract
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from config import config
from models import db, User, Member, Trainer, Attendance, ProgressRecord, Invoice, Payment, Class, WorkoutPlan, ChatMessage, PaymentReminder
from ai_services import generate_workout_plan, get_chatbot_response, generate_payment_reminder, is_ai_available
from churn_service import churn_predictor
from revenue_service import revenue_forecaster
from peak_hour_service import peak_hour_predictor

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(config['development'])

# Set instance path for SQLite
import os
app.instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')

# Initialize extensions
bcrypt = Bcrypt(app)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Role-based access control decorator
def role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# Create database tables
def init_db():
    """Initialize database and create tables."""
    with app.app_context():
        # Create database if using MySQL
        if app.config.get('DB_TYPE') == 'mysql':
            try:
                conn = pymysql.connect(
                    host=app.config['DB_HOST'],
                    user=app.config['DB_USER'],
                    password=app.config['DB_PASSWORD']
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS {app.config['DB_NAME']}")
                conn.close()
            except Exception as e:
                print(f"Database connection error: {e}")
        
        # Create all tables
        db.create_all()
        
        # Create default admin if not exists
        if not User.query.filter_by(email='admin@fitness.com').first():
            admin_user = User(
                email='admin@fitness.com',
                first_name='Admin',
                last_name='User',
                role='admin',
                phone='1234567890'
            )
            admin_user.password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin created: admin@fitness.com / admin123")


def seed_data():
    """Seed comprehensive demo data for testing."""
    with app.app_context():
        if Member.query.count() > 0:
            print("Database already has data, skipping seed.")
            return

        from datetime import date, timedelta, time as dt_time
        import random

        # ==================== MEMBERS (10) ====================
        members_data = [
            ('TheAkbarAkiOfficial@gmail.com', 'Ali', 'Akbar', 'member', '5550101', 'male', 'monthly', 175, 78, 'Muscle Gain'),
            ('HuzifaGymOfficial@gmail.com', 'Huzifa', 'Khan', 'member', '5550102', 'male', 'quarterly', 180, 85, 'Weight Loss'),
            ('SaadFitnessPro@gmail.com', 'Saad', 'Malik', 'member', '5550103', 'male', 'yearly', 170, 70, 'General Fitness'),
            ('SaraFitZoneOfficial@gmail.com', 'Sara', 'Ahmed', 'member', '5550104', 'female', 'monthly', 165, 58, 'Weight Loss'),
            ('SanihaWorkoutQueen@gmail.com', 'Saniha', 'Hassan', 'member', '5550105', 'female', 'quarterly', 168, 62, 'Endurance'),
            ('OmarGymLife@gmail.com', 'Omar', 'Farooq', 'member', '5550106', 'male', 'monthly', 178, 82, 'Muscle Gain'),
            ('AishaFitLife@gmail.com', 'Aisha', 'Rahman', 'member', '5550107', 'female', 'yearly', 162, 55, 'Yoga & Flexibility'),
            ('HamzaStrong@gmail.com', 'Hamza', 'Ali', 'member', '5550108', 'male', 'quarterly', 185, 90, 'Strength Training'),
            ('FatimaHealth@gmail.com', 'Fatima', 'Zahra', 'member', '5550109', 'female', 'monthly', 160, 60, 'General Fitness'),
            ('UsmanPower@gmail.com', 'Usman', 'Khalid', 'member', '5550110', 'male', 'yearly', 172, 75, 'Endurance'),
        ]

        member_profiles = []
        for email, fname, lname, role, phone, gender, mtype, height, weight, goal in members_data:
            user = User(
                email=email,
                first_name=fname,
                last_name=lname,
                role=role,
                phone=phone
            )
            user.password_hash = bcrypt.generate_password_hash('demo123').decode('utf-8')
            db.session.add(user)
            db.session.flush()

            start = date.today() - timedelta(days=random.randint(30, 365))
            end = start + timedelta(days=30 if mtype == 'monthly' else 90 if mtype == 'quarterly' else 365)
            member = Member(
                user_id=user.id,
                gender=gender,
                membership_type=mtype,
                membership_start=start,
                membership_end=end,
                height=height,
                weight=weight,
                fitness_goal=goal,
                medical_conditions=random.choice(['None', 'None', 'None', 'Mild asthma', 'Knee injury history'])
            )
            db.session.add(member)
            db.session.flush()
            member_profiles.append(member)

        # ==================== TRAINERS (5) ====================
        trainers_data = [
            ('ZainTrainerPro@gmail.com', 'Zain', 'Hassan', 'Yoga & Pilates', 5, 'ACE Certified Yoga Instructor', 45.0, 'Certified yoga instructor specializing in Vinyasa and Hatha yoga. Helping clients find balance and flexibility.'),
            ('AyeshaFitQueen@gmail.com', 'Ayesha', 'Khan', 'HIIT & Cardio', 3, 'NASM Certified Personal Trainer', 50.0, 'High-energy trainer focused on fat loss and cardiovascular health. Former competitive athlete.'),
            ('BilalGymBeast@gmail.com', 'Bilal', 'Ahmed', 'Weight Training', 7, 'CSCS Strength Coach', 55.0, 'Strength and conditioning specialist with experience training professional athletes. Powerlifting competitor.'),
            ('NadiaWellness@gmail.com', 'Nadia', 'Hussain', 'Nutrition & Wellness', 4, 'Precision Nutrition Certified', 40.0, 'Holistic health coach combining nutrition planning with mindful movement practices.'),
            ('TariqCrossFit@gmail.com', 'Tariq', 'Mehmood', 'CrossFit & Functional', 6, 'CrossFit Level 2 Trainer', 60.0, 'Functional fitness expert specializing in CrossFit-style workouts and mobility training.'),
        ]

        trainer_profiles = []
        for email, fname, lname, spec, exp, cert, rate, bio in trainers_data:
            user = User(
                email=email,
                first_name=fname,
                last_name=lname,
                role='trainer',
                phone=f'55502{len(trainer_profiles)+1:02d}'
            )
            user.password_hash = bcrypt.generate_password_hash('demo123').decode('utf-8')
            db.session.add(user)
            db.session.flush()

            trainer = Trainer(
                user_id=user.id,
                specialization=spec,
                experience_years=exp,
                certification=cert,
                hourly_rate=rate,
                bio=bio
            )
            db.session.add(trainer)
            db.session.flush()
            trainer_profiles.append(trainer)

        # ==================== ATTENDANCE (30 days) ====================
        for i in range(30):
            day = date.today() - timedelta(days=i)
            num_checkins = random.randint(2, 5)
            for member in random.sample(member_profiles, k=min(num_checkins, len(member_profiles))):
                check_in = datetime.combine(day, datetime.min.time()) + timedelta(
                    hours=random.randint(5, 21), minutes=random.randint(0, 59)
                )
                check_out = check_in + timedelta(
                    hours=random.randint(1, 3), minutes=random.randint(0, 59)
                )
                att = Attendance(
                    member_id=member.id,
                    check_in=check_in,
                    check_out=check_out,
                    duration_minutes=int((check_out - check_in).total_seconds() // 60)
                )
                db.session.add(att)

        # ==================== INVOICES & PAYMENTS ====================
        for member in member_profiles:
            # Create 2-3 invoices per member
            for inv_idx in range(random.randint(2, 3)):
                inv_date = date.today() - timedelta(days=random.randint(10, 90))
                due_date = inv_date + timedelta(days=15)
                amount = random.choice([49.99, 79.99, 129.99, 199.99, 399.99])
                
                inv = Invoice(
                    invoice_number=f"INV-{datetime.now().year}-{member.id:04d}-{inv_idx+1}",
                    member_id=member.id,
                    amount=amount,
                    tax=round(amount * 0.1, 2),
                    total_amount=round(amount * 1.1, 2),
                    description=f"{member.membership_type.title()} membership fee - Cycle {inv_idx+1}",
                    due_date=due_date,
                    issued_date=inv_date
                )
                db.session.add(inv)
                db.session.flush()

                # 70% paid, 30% pending (some overdue)
                if random.random() > 0.3:
                    payment = Payment(
                        invoice_id=inv.id,
                        member_id=member.id,
                        amount=inv.total_amount,
                        payment_method=random.choice(['cash', 'card', 'bank_transfer']),
                        payment_date=inv_date + timedelta(days=random.randint(1, 10)),
                        transaction_id=f"TXN-{inv_date.strftime('%Y%m%d')}-{member.id}-{inv_idx}"
                    )
                    db.session.add(payment)
                    inv.status = 'paid'
                elif due_date < date.today():
                    inv.status = 'pending'  # Overdue

        # ==================== PROGRESS RECORDS (6 per member) ====================
        for member in member_profiles:
            base_weight = member.weight
            base_body_fat = random.uniform(15, 22)
            for j in range(6):
                progress_date = date.today() - timedelta(days=j * 14)  # Every 2 weeks
                # Simulate realistic progress
                weight_change = random.uniform(-1.5, 0.5) if member.fitness_goal == 'Weight Loss' else random.uniform(-0.5, 2.0)
                body_fat_change = random.uniform(-0.8, 0.2) if member.fitness_goal == 'Weight Loss' else random.uniform(-0.3, 0.5)
                
                progress = ProgressRecord(
                    member_id=member.id,
                    record_date=progress_date,
                    weight=round(base_weight + weight_change + random.uniform(-0.5, 0.5), 1),
                    body_fat_percentage=round(base_body_fat + body_fat_change + random.uniform(-0.3, 0.3), 1),
                    chest=round(random.uniform(85, 115), 1),
                    waist=round(random.uniform(65, 95), 1),
                    hips=round(random.uniform(85, 110), 1),
                    biceps=round(random.uniform(28, 42), 1),
                    thighs=round(random.uniform(48, 65), 1),
                    notes=random.choice([
                        'Regular check-in, feeling strong!',
                        'Slight improvement in endurance.',
                        'Need to focus on diet this week.',
                        'Great progress on squat form.',
                        'Hit a new PR on bench press!',
                        'Feeling energized and motivated.'
                    ])
                )
                db.session.add(progress)

        # ==================== CLASSES (8 classes) ====================
        class_data = [
            ('Morning Yoga Flow', 'Start your day with energizing Vinyasa yoga', 1, 0, '06:00', '07:00'),
            ('HIIT Blast', 'High intensity interval training for maximum calorie burn', 2, 1, '17:00', '18:00'),
            ('Strength 101', 'Learn proper weight lifting form and technique', 3, 2, '18:00', '19:30'),
            ('Pilates Core', 'Core strengthening and flexibility training', 1, 3, '12:00', '13:00'),
            ('CrossFit WOD', 'Daily workout of the day - functional fitness', 5, 4, '19:00', '20:00'),
            ('Nutrition Workshop', 'Learn meal prep and healthy eating habits', 4, 5, '14:00', '15:30'),
            ('Evening Meditation', 'Guided meditation and breathwork', 1, 6, '20:00', '21:00'),
            ('Powerlifting', 'Heavy compound lifts and strength building', 3, 0, '16:00', '17:30'),
        ]
        for name, desc, trainer_id, dow, start_t, end_t in class_data:
            c = Class(
                name=name,
                description=desc,
                trainer_id=trainer_id,
                day_of_week=dow,
                start_time=dt_time.fromisoformat(start_t),
                end_time=dt_time.fromisoformat(end_t),
                max_participants=random.randint(15, 30)
            )
            db.session.add(c)

        # ==================== WORKOUT PLANS (AI-generated for some members) ====================
        workout_plan_titles = [
            '4-Week Muscle Building Program',
            'Fat Loss Accelerator',
            'Strength & Conditioning Plan',
            'Beginner Fitness Foundation',
            'Endurance Builder'
        ]
        
        for idx, member in enumerate(member_profiles[:5]):  # First 5 members get plans
            plan_content = f"""# {workout_plan_titles[idx]}

## Overview
Personalized {member.fitness_goal} plan for {member.user.first_name} {member.user.last_name}.
Current stats: Height {member.height}cm, Weight {member.weight}kg.

## Weekly Schedule

### Monday - Upper Body Strength
- Bench Press: 4 sets x 8-10 reps
- Overhead Press: 3 sets x 10 reps
- Bent Over Rows: 3 sets x 12 reps
- Bicep Curls: 3 sets x 12 reps
- Tricep Pushdowns: 3 sets x 15 reps

### Tuesday - Cardio & Core
- 30 min treadmill incline walk
- Plank: 3 sets x 45 seconds
- Russian Twists: 3 sets x 20 reps
- Leg Raises: 3 sets x 15 reps

### Wednesday - Lower Body Power
- Squats: 4 sets x 8 reps
- Romanian Deadlifts: 3 sets x 10 reps
- Lunges: 3 sets x 12 reps per leg
- Calf Raises: 4 sets x 15 reps

### Thursday - Active Recovery
- Light yoga or stretching: 30 min
- Foam rolling: 15 min
- Mobility work

### Friday - Full Body Circuit
- Circuit (3 rounds):
  - Kettlebell Swings: 15 reps
  - Push-ups: 12 reps
  - Goblet Squats: 12 reps
  - Mountain Climbers: 20 reps

### Saturday - Optional Cardio
- 45 min outdoor run or cycling

### Sunday - Rest Day
- Complete rest or light walking

## Nutrition Guidelines
- Daily caloric target: ~{2200 if member.gender == 'male' else 1800} kcal
- Protein: 1.6-2.0g per kg bodyweight
- Hydration: 3+ liters water daily
- Focus on whole foods and lean proteins

## Notes
- Warm up 5-10 min before each workout
- Cool down and stretch after each session
- Track progress weekly
- Adjust weights as you get stronger
"""
            plan = WorkoutPlan(
                member_id=member.id,
                title=workout_plan_titles[idx],
                plan_content=plan_content,
                fitness_goal=member.fitness_goal,
                duration_weeks=4,
                ai_model='mock-ai'
            )
            db.session.add(plan)

        # ==================== CHAT MESSAGES ====================
        chat_conversations = [
            (1, 'user', 'Hello! Can you help me with a workout plan?'),
            (1, 'assistant', "Hi there! I'd be happy to help. What are your fitness goals? Weight loss, muscle gain, or general fitness?"),
            (1, 'user', "I want to build muscle. I'm 78kg and 175cm."),
            (1, 'assistant', 'Great goal! For muscle building at your stats, focus on progressive overload with compound lifts. Aim for 1.6-2.2g protein per kg bodyweight. Would you like me to suggest a split?'),
            (2, 'user', 'What classes do you offer?'),
            (2, 'assistant', 'We offer Morning Yoga, HIIT Blast, Strength 101, Pilates Core, CrossFit WOD, and more! Check the Classes page for the full schedule.'),
        ]
        
        for user_id, role, message in chat_conversations:
            msg = ChatMessage(
                user_id=user_id,
                role=role,
                message=message
            )
            db.session.add(msg)

        # ==================== PAYMENT REMINDERS ====================
        # Create some sample reminders for overdue invoices
        overdue_invs = Invoice.query.filter(Invoice.status == 'pending', Invoice.due_date < date.today()).all()
        for inv in overdue_invs[:3]:
            reminder = PaymentReminder(
                member_id=inv.member_id,
                invoice_id=inv.id,
                reminder_message=f"Dear {inv.member.user.first_name}, this is a friendly reminder that invoice {inv.invoice_number} for ${inv.total_amount:.2f} was due on {inv.due_date}. Please settle at your earliest convenience.",
                tone='friendly',
                is_sent=random.choice([True, False])
            )
            db.session.add(reminder)

        db.session.commit()
        print("=" * 60)
        print("COMPREHENSIVE DEMO DATA SEEDED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Members: {Member.query.count()}")
        print(f"Trainers: {Trainer.query.count()}")
        print(f"Attendance Records: {Attendance.query.count()}")
        print(f"Invoices: {Invoice.query.count()}")
        print(f"Payments: {Payment.query.count()}")
        print(f"Progress Records: {ProgressRecord.query.count()}")
        print(f"Classes: {Class.query.count()}")
        print(f"Workout Plans: {WorkoutPlan.query.count()}")
        print(f"Chat Messages: {ChatMessage.query.count()}")
        print(f"Payment Reminders: {PaymentReminder.query.count()}")
        print("=" * 60)
        print("Login credentials:")
        print("  Admin: admin@fitness.com / admin123")
        print("  Members/Trainers: any demo email / demo123")
        print("=" * 60)



# ==================== AUTH ROUTES ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if user.is_active:
                login_user(user, remember=True)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.first_name}!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Your account has been deactivated.', 'warning')
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        role = request.form.get('role', 'member')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        phone = request.form.get('phone', '')
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=hashed_password,
            role=role,
            phone=phone
        )
        db.session.add(user)
        db.session.commit()
        
        # Create member or trainer profile
        if role == 'member':
            member = Member(user_id=user.id)
            db.session.add(member)
        elif role == 'trainer':
            trainer = Trainer(user_id=user.id)
            db.session.add(trainer)
        
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


# ==================== DASHBOARD ROUTES ====================

@app.route('/dashboard')
@login_required
def dashboard():
    # Get statistics for dashboard
    total_members = Member.query.count()
    total_trainers = Trainer.query.count()
    today = date.today()
    
    # Today's attendance
    today_attendance = Attendance.query.filter(
        func.date(Attendance.check_in) == today
    ).count()
    
    # This month's revenue
    month_start = date(today.year, today.month, 1)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= month_start
    ).scalar() or 0
    
    # Recent members
    recent_members = Member.query.order_by(Member.created_at.desc()).limit(5).all()
    
    # Attendance trend (last 7 days)
    attendance_trend = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Attendance.query.filter(func.date(Attendance.check_in) == day).count()
        attendance_trend.append({
            'date': day.strftime('%b %d'),
            'count': count
        })
    
    # Revenue trend (last 6 months)
    revenue_trend = []
    for i in range(5, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)
        revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_start,
            Payment.payment_date < month_end
        ).scalar() or 0
        revenue_trend.append({
            'month': month_start.strftime('%b'),
            'amount': float(revenue)
        })
    
    # Membership distribution
    membership_types = db.session.query(
        Member.membership_type,
        func.count(Member.id)
    ).group_by(Member.membership_type).all()
    membership_dist = [{'type': m[0] or 'None', 'count': m[1]} for m in membership_types]
    
    stats = {
        'total_members': total_members,
        'total_trainers': total_trainers,
        'today_attendance': today_attendance,
        'monthly_revenue': monthly_revenue
    }
    
    return render_template('dashboard.html',
                         stats=stats,
                         recent_members=recent_members,
                         attendance_trend=attendance_trend,
                         revenue_trend=revenue_trend,
                         membership_dist=membership_dist)


# ==================== MEMBER ROUTES ====================

@app.route('/members')
@login_required
@role_required(['admin', 'trainer'])
def members():
    search_query = request.args.get('search', '')
    filter_type = request.args.get('filter', 'all')
    
    query = Member.query.join(User).filter(User.is_active == True)
    
    if search_query:
        query = query.filter(
            (User.first_name.ilike(f'%{search_query}%')) |
            (User.last_name.ilike(f'%{search_query}%')) |
            (User.email.ilike(f'%{search_query}%'))
        )
    
    if filter_type == 'active':
        query = query.filter(Member.is_active == True)
    elif filter_type == 'inactive':
        query = query.filter(Member.is_active == False)
    elif filter_type == 'expired':
        query = query.filter(Member.membership_end < date.today())
    
    members_list = query.order_by(Member.created_at.desc()).all()
    
    return render_template('members.html', members=members_list, search=search_query, filter_type=filter_type, today=date.today())


@app.route('/members/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_member():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('add_member'))
        
        # Create user
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='member'
        )
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.add(user)
        db.session.commit()
        
        # Create member profile
        member = Member(
            user_id=user.id,
            date_of_birth=datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None,
            gender=request.form.get('gender'),
            address=request.form.get('address'),
            emergency_contact=request.form.get('emergency_contact'),
            emergency_phone=request.form.get('emergency_phone'),
            membership_type=request.form.get('membership_type'),
            membership_start=datetime.strptime(request.form.get('membership_start'), '%Y-%m-%d').date() if request.form.get('membership_start') else None,
            membership_end=datetime.strptime(request.form.get('membership_end'), '%Y-%m-%d').date() if request.form.get('membership_end') else None,
            height=float(request.form.get('height')) if request.form.get('height') else None,
            weight=float(request.form.get('weight')) if request.form.get('weight') else None,
            fitness_goal=request.form.get('fitness_goal'),
            medical_conditions=request.form.get('medical_conditions')
        )
        db.session.add(member)
        db.session.commit()
        
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))
    
    return render_template('member_form.html', member=None)


@app.route('/members/<int:member_id>')
@login_required
def member_detail(member_id):
    member = Member.query.get_or_404(member_id)
    progress = ProgressRecord.query.filter_by(member_id=member_id).order_by(ProgressRecord.record_date.desc()).limit(10).all()
    attendance = Attendance.query.filter_by(member_id=member_id).order_by(Attendance.check_in.desc()).limit(10).all()
    payments = Payment.query.filter_by(member_id=member_id).order_by(Payment.payment_date.desc()).limit(10).all()
    invoices = Invoice.query.filter_by(member_id=member_id).order_by(Invoice.created_at.desc()).limit(10).all()
    
    return render_template('member_detail.html',
                         member=member,
                         progress=progress,
                         attendance=attendance,
                         payments=payments,
                         invoices=invoices)


@app.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_member(member_id):
    member = Member.query.get_or_404(member_id)
    user = member.user
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        member.date_of_birth = datetime.strptime(request.form.get('date_of_birth'), '%Y-%m-%d').date() if request.form.get('date_of_birth') else None
        member.gender = request.form.get('gender')
        member.address = request.form.get('address')
        member.emergency_contact = request.form.get('emergency_contact')
        member.emergency_phone = request.form.get('emergency_phone')
        member.membership_type = request.form.get('membership_type')
        member.membership_start = datetime.strptime(request.form.get('membership_start'), '%Y-%m-%d').date() if request.form.get('membership_start') else None
        member.membership_end = datetime.strptime(request.form.get('membership_end'), '%Y-%m-%d').date() if request.form.get('membership_end') else None
        member.height = float(request.form.get('height')) if request.form.get('height') else None
        member.weight = float(request.form.get('weight')) if request.form.get('weight') else None
        member.fitness_goal = request.form.get('fitness_goal')
        member.medical_conditions = request.form.get('medical_conditions')
        
        db.session.commit()
        flash('Member updated successfully!', 'success')
        return redirect(url_for('member_detail', member_id=member_id))
    
    return render_template('member_form.html', member=member)


@app.route('/members/<int:member_id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_member(member_id):
    member = Member.query.get_or_404(member_id)
    user = member.user
    
    # Soft delete - deactivate user
    user.is_active = False
    member.is_active = False
    db.session.commit()
    
    flash('Member has been deactivated.', 'success')
    return redirect(url_for('members'))


# ==================== TRAINER ROUTES ====================

@app.route('/trainers')
@login_required
@role_required(['admin'])
def trainers():
    trainers_list = Trainer.query.join(User).filter(User.is_active == True).all()
    return render_template('trainers.html', trainers=trainers_list)


@app.route('/trainers/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_trainer():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        phone = request.form.get('phone')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'danger')
            return redirect(url_for('add_trainer'))
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            role='trainer'
        )
        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        db.session.add(user)
        db.session.commit()
        
        trainer = Trainer(
            user_id=user.id,
            specialization=request.form.get('specialization'),
            experience_years=int(request.form.get('experience_years')) if request.form.get('experience_years') else 0,
            certification=request.form.get('certification'),
            bio=request.form.get('bio'),
            hourly_rate=float(request.form.get('hourly_rate')) if request.form.get('hourly_rate') else 0
        )
        db.session.add(trainer)
        db.session.commit()
        
        flash('Trainer added successfully!', 'success')
        return redirect(url_for('trainers'))
    
    return render_template('trainer_form.html', trainer=None)


@app.route('/trainers/<int:trainer_id>')
@login_required
def trainer_detail(trainer_id):
    trainer = Trainer.query.get_or_404(trainer_id)
    classes = Class.query.filter_by(trainer_id=trainer_id).all()
    return render_template('trainer_detail.html', trainer=trainer, classes=classes)


@app.route('/trainers/<int:trainer_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_trainer(trainer_id):
    trainer = Trainer.query.get_or_404(trainer_id)
    user = trainer.user
    
    if request.method == 'POST':
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        trainer.specialization = request.form.get('specialization')
        trainer.experience_years = int(request.form.get('experience_years')) if request.form.get('experience_years') else 0
        trainer.certification = request.form.get('certification')
        trainer.bio = request.form.get('bio')
        trainer.hourly_rate = float(request.form.get('hourly_rate')) if request.form.get('hourly_rate') else 0
        
        db.session.commit()
        flash('Trainer updated successfully!', 'success')
        return redirect(url_for('trainer_detail', trainer_id=trainer_id))
    
    return render_template('trainer_form.html', trainer=trainer)


@app.route('/trainers/<int:trainer_id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_trainer(trainer_id):
    trainer = Trainer.query.get_or_404(trainer_id)
    user = trainer.user
    
    # Soft delete - deactivate user
    user.is_active = False
    db.session.commit()
    
    flash('Trainer has been deactivated.', 'success')
    return redirect(url_for('trainers'))


# ==================== CLASS ROUTES ====================

@app.route('/classes')
@login_required
@role_required(['admin', 'trainer'])
def classes_list():
    classes = Class.query.join(Trainer).join(User).filter(User.is_active == True).all()
    return render_template('classes.html', classes=classes)


@app.route('/classes/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def add_class():
    if request.method == 'POST':
        from datetime import time as dt_time
        name = request.form.get('name')
        description = request.form.get('description')
        trainer_id = request.form.get('trainer_id')
        day_of_week = int(request.form.get('day_of_week')) if request.form.get('day_of_week') else 0
        start_time = dt_time.fromisoformat(request.form.get('start_time')) if request.form.get('start_time') else None
        end_time = dt_time.fromisoformat(request.form.get('end_time')) if request.form.get('end_time') else None
        max_participants = int(request.form.get('max_participants', 20))
        
        new_class = Class(
            name=name,
            description=description,
            trainer_id=trainer_id,
            day_of_week=day_of_week,
            start_time=start_time,
            end_time=end_time,
            max_participants=max_participants
        )
        db.session.add(new_class)
        db.session.commit()
        
        flash('Class added successfully!', 'success')
        return redirect(url_for('classes_list'))
    
    trainers = Trainer.query.join(User).filter(User.is_active == True).all()
    return render_template('class_form.html', class_obj=None, trainers=trainers)


@app.route('/classes/<int:class_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def edit_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    
    if request.method == 'POST':
        from datetime import time as dt_time
        class_obj.name = request.form.get('name')
        class_obj.description = request.form.get('description')
        class_obj.trainer_id = request.form.get('trainer_id')
        class_obj.day_of_week = int(request.form.get('day_of_week')) if request.form.get('day_of_week') else 0
        class_obj.start_time = dt_time.fromisoformat(request.form.get('start_time')) if request.form.get('start_time') else None
        class_obj.end_time = dt_time.fromisoformat(request.form.get('end_time')) if request.form.get('end_time') else None
        class_obj.max_participants = int(request.form.get('max_participants', 20))
        
        db.session.commit()
        flash('Class updated successfully!', 'success')
        return redirect(url_for('classes_list'))
    
    trainers = Trainer.query.join(User).filter(User.is_active == True).all()
    return render_template('class_form.html', class_obj=class_obj, trainers=trainers)


@app.route('/classes/<int:class_id>/delete', methods=['POST'])
@login_required
@role_required(['admin'])
def delete_class(class_id):
    class_obj = Class.query.get_or_404(class_id)
    db.session.delete(class_obj)
    db.session.commit()
    
    flash('Class has been deleted.', 'success')
    return redirect(url_for('classes_list'))


# ==================== ATTENDANCE ROUTES ====================

@app.route('/attendance')
@login_required
def attendance():
    date_filter = request.args.get('date', date.today().isoformat())
    filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
    
    attendance_records = Attendance.query.filter(
        func.date(Attendance.check_in) == filter_date
    ).order_by(Attendance.check_in.desc()).all()
    
    # Calculate statistics
    total_checked_in = len([a for a in attendance_records if not a.check_out])
    total_checked_out = len([a for a in attendance_records if a.check_out])
    
    return render_template('attendance.html',
                         attendance=attendance_records,
                         selected_date=filter_date,
                         total_checked_in=total_checked_in,
                         total_checked_out=total_checked_out)


@app.route('/attendance/check-in', methods=['POST'])
@login_required
def check_in():
    member_id = request.form.get('member_id')
    
    # Check if already checked in today
    today = date.today()
    existing = Attendance.query.filter(
        Attendance.member_id == member_id,
        func.date(Attendance.check_in) == today
    ).first()
    
    if existing and not existing.check_out:
        flash('Member is already checked in.', 'warning')
        return redirect(url_for('attendance'))
    
    attendance = Attendance(member_id=member_id)
    db.session.add(attendance)
    db.session.commit()
    
    flash('Check-in successful!', 'success')
    return redirect(url_for('attendance'))


@app.route('/attendance/check-out/<int:attendance_id>', methods=['POST'])
@login_required
def check_out(attendance_id):
    attendance = Attendance.query.get_or_404(attendance_id)
    
    if attendance.check_out:
        flash('Already checked out.', 'warning')
        return redirect(url_for('attendance'))
    
    attendance.check_out = datetime.utcnow()
    duration = attendance.check_out - attendance.check_in
    attendance.duration_minutes = int(duration.total_seconds() / 60)
    db.session.commit()
    
    flash('Check-out successful!', 'success')
    return redirect(url_for('attendance'))


# ==================== INVOICES & PAYMENTS ROUTES ====================

@app.route('/invoices')
@login_required
@role_required(['admin', 'member'])
def invoices():
    if current_user.role == 'admin':
        invoices_list = Invoice.query.order_by(Invoice.created_at.desc()).all()
    else:
        member = current_user.member
        invoices_list = Invoice.query.filter_by(member_id=member.id).order_by(Invoice.created_at.desc()).all()
    
    return render_template('invoices.html', invoices=invoices_list)


@app.route('/invoices/create', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def create_invoice():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        due_date = datetime.strptime(request.form.get('due_date'), '%Y-%m-%d').date() if request.form.get('due_date') else None
        
        # Generate invoice number
        invoice_count = Invoice.query.count()
        invoice_number = f'INV-{datetime.now().year}-{invoice_count + 1:04d}'
        
        tax = amount * 0.1  # 10% tax
        total = amount + tax
        
        invoice = Invoice(
            invoice_number=invoice_number,
            member_id=member_id,
            amount=amount,
            tax=tax,
            total_amount=total,
            description=description,
            due_date=due_date
        )
        db.session.add(invoice)
        db.session.commit()
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('invoices'))
    
    members = Member.query.join(User).filter(User.is_active == True).all()
    return render_template('invoice_form.html', invoice=None, members=members)


@app.route('/invoices/<int:invoice_id>/pay', methods=['POST'])
@login_required
def pay_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    
    if invoice.status == 'paid':
        flash('Invoice already paid.', 'warning')
        return redirect(url_for('invoices'))
    
    # Create payment
    payment = Payment(
        invoice_id=invoice.id,
        member_id=invoice.member_id,
        amount=invoice.total_amount,
        payment_method=request.form.get('payment_method'),
        transaction_id=f'TXN-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    )
    db.session.add(payment)
    
    invoice.status = 'paid'
    db.session.commit()
    
    flash('Payment successful!', 'success')
    return redirect(url_for('invoices'))


# ==================== PROGRESS ROUTES ====================

@app.route('/progress')
@login_required
def progress():
    if current_user.role == 'member':
        member = current_user.member
        if member:
            progress_records = ProgressRecord.query.filter_by(
                member_id=member.id
            ).order_by(ProgressRecord.record_date.desc()).all()
            return render_template('progress.html', progress=progress_records, member=member)
    
    # For admin/trainer, show all members' progress
    members = Member.query.join(User).filter(User.is_active == True).all()
    return render_template('progress_select.html', members=members)


@app.route('/progress/<int:member_id>')
@login_required
def member_progress(member_id):
    member = Member.query.get_or_404(member_id)
    progress_records = ProgressRecord.query.filter_by(
        member_id=member_id
    ).order_by(ProgressRecord.record_date.desc()).all()
    
    return render_template('progress.html', progress=progress_records, member=member)


@app.route('/progress/add', methods=['GET', 'POST'])
@login_required
@role_required(['admin', 'trainer'])
def add_progress():
    if request.method == 'POST':
        member_id = request.form.get('member_id')
        
        progress = ProgressRecord(
            member_id=member_id,
            record_date=datetime.strptime(request.form.get('record_date'), '%Y-%m-%d').date(),
            weight=float(request.form.get('weight')) if request.form.get('weight') else None,
            body_fat_percentage=float(request.form.get('body_fat_percentage')) if request.form.get('body_fat_percentage') else None,
            chest=float(request.form.get('chest')) if request.form.get('chest') else None,
            waist=float(request.form.get('waist')) if request.form.get('waist') else None,
            hips=float(request.form.get('hips')) if request.form.get('hips') else None,
            biceps=float(request.form.get('biceps')) if request.form.get('biceps') else None,
            thighs=float(request.form.get('thighs')) if request.form.get('thighs') else None,
            notes=request.form.get('notes')
        )
        db.session.add(progress)
        db.session.commit()
        
        flash('Progress record added!', 'success')
        return redirect(url_for('member_progress', member_id=member_id))
    
    members = Member.query.join(User).filter(User.is_active == True).all()
    return render_template('progress_form.html', progress=None, members=members, today=date.today().isoformat())


# ==================== CHURN PREDICTION ROUTES ====================

@app.route('/churn')
@login_required
@role_required(['admin'])
def churn_prediction():
    """Show churn prediction dashboard for at-risk members."""
    high_risk_members = churn_predictor.get_high_risk_members(threshold=0.6)
    
    # Prepare data for template
    members_data = []
    for item in high_risk_members:
        member = item['member']
        members_data.append({
            'id': member.id,
            'name': member.user.get_full_name(),
            'email': member.user.email,
            'membership_type': member.membership_type,
            'days_since_last_visit': (date.today() - 
                (Attendance.query.filter_by(member_id=member.id)
                 .order_by(Attendance.check_in.desc())
                 .first().check_in.date() 
                 if Attendance.query.filter_by(member_id=member.id).first() 
                 else date.today())).days if Attendance.query.filter_by(member_id=member.id).first() else 999,
            'churn_probability': round(item['churn_probability'] * 100, 1)
        })
    
    return render_template('churn.html', 
                         members=members_data,
                         total_high_risk=len(high_risk_members))

@app.route('/churn/retrain')
@login_required
@role_required(['admin'])
def retrain_churn_model():
    """Retrain the churn prediction model."""
    success = churn_predictor.train_model()
    if success:
        flash('Churn prediction model retrained successfully!', 'success')
    else:
        flash('Failed to retrain churn prediction model.', 'danger')
    return redirect(url_for('churn_prediction'))

@app.route('/churn/<int:member_id>')
@login_required
@role_required(['admin'])
def member_churn_details(member_id):
    """Show detailed churn prediction for a specific member."""
    member = Member.query.get_or_404(member_id)
    churn_prob = churn_predictor.predict_churn_probability(member_id)
    
    # Get member stats for display
    thirty_days_ago = date.today() - timedelta(days=30)
    recent_attendance = Attendance.query.filter(
        Attendance.member_id == member.id,
        Attendance.check_in >= thirty_days_ago
    ).count()
    
    last_attendance = Attendance.query.filter_by(
        member_id=member.id
    ).order_by(Attendance.check_in.desc()).first()
    
    days_since_last_visit = (date.today() - last_attendance.check_in.date()).days if last_attendance else 999
    
    three_months_ago = date.today() - timedelta(days=90)
    recent_payments = Payment.query.filter(
        Payment.member_id == member.id,
        Payment.payment_date >= three_months_ago
    ).all()
    
    avg_payment = 0
    if recent_payments:
        avg_payment = sum(p.amount for p in recent_payments) / len(recent_payments)
    
    overdue_invoices = Invoice.query.filter(
        Invoice.member_id == member.id,
        Invoice.status == 'pending',
        Invoice.due_date < date.today()
    ).count()
    
    progress_count = ProgressRecord.query.filter_by(member_id=member.id).count()
    
    return render_template('churn_details.html',
                         member=member,
                         churn_probability=round(churn_prob * 100, 1),
                         recent_attendance=recent_attendance,
                         days_since_last_visit=days_since_last_visit,
                         avg_payment=round(avg_payment, 2),
                         overdue_invoices=overdue_invoices,
                         progress_count=progress_count)

# ==================== ANALYTICS ROUTES ====================

@app.route('/analytics')
@login_required
@role_required(['admin'])
def analytics():
    today = date.today()
    
    # Member growth (last 12 months)
    member_growth = []
    for i in range(11, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)
        count = Member.query.filter(
            Member.created_at >= month_start,
            Member.created_at < month_end
        ).count()
        member_growth.append({
            'month': month_start.strftime('%b'),
            'count': count
        })
    
    # Revenue by month
    revenue_by_month = []
    for i in range(11, -1, -1):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        month_start = date(year, month, 1)
        if month == 12:
            month_end = date(year + 1, 1, 1)
        else:
            month_end = date(year, month + 1, 1)
        revenue = db.session.query(func.sum(Payment.amount)).filter(
            Payment.payment_date >= month_start,
            Payment.payment_date < month_end
        ).scalar() or 0
        revenue_by_month.append({
            'month': month_start.strftime('%b'),
            'revenue': float(revenue)
        })
    
    # Top members by attendance
    top_attendance = db.session.query(
        Member.id,
        User.first_name,
        User.last_name,
        func.count(Attendance.id).label('attendance_count')
    ).join(User).join(Attendance).group_by(Member.id).order_by(func.count(Attendance.id).desc()).limit(10).all()
    
    # Membership type distribution
    membership_dist = db.session.query(
        Member.membership_type,
        func.count(Member.id)
    ).group_by(Member.membership_type).all()
    membership_dist = [[m[0], m[1]] for m in membership_dist]
    
    # Payment status
    pending_invoices = Invoice.query.filter_by(status='pending').count()
    paid_invoices = Invoice.query.filter_by(status='paid').count()
    overdue_invoices = Invoice.query.filter(Invoice.status == 'pending', Invoice.due_date < today).count()
    
    return render_template('analytics.html',
                         member_growth=member_growth,
                         revenue_by_month=revenue_by_month,
                         top_attendance=top_attendance,
                         membership_dist=membership_dist,
                         pending_invoices=pending_invoices,
                         paid_invoices=paid_invoices,
                         overdue_invoices=overdue_invoices)


# ==================== API ROUTES ====================

@app.route('/api/members/search')
@login_required
def api_members_search():
    query = request.args.get('q', '')
    members = Member.query.join(User).filter(
        (User.first_name.ilike(f'%{query}%')) |
        (User.last_name.ilike(f'%{query}%')) |
        (User.email.ilike(f'%{query}%'))
    ).limit(10).all()
    
    results = [{
        'id': m.id,
        'name': f"{m.user.first_name} {m.user.last_name}",
        'email': m.user.email,
        'membership': m.membership_type
    } for m in members]
    
    return jsonify(results)


@app.route('/api/attendance/today')
@login_required
def api_attendance_today():
    today = date.today()
    attendance = Attendance.query.filter(
        func.date(Attendance.check_in) == today
    ).all()
    
    results = [{
        'id': a.id,
        'member': f"{a.member.user.first_name} {a.member.user.last_name}",
        'check_in': a.check_in.strftime('%H:%M'),
        'check_out': a.check_out.strftime('%H:%M') if a.check_out else None,
        'duration': a.duration_minutes
    } for a in attendance]
    
    return jsonify(results)


@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    total_members = Member.query.count()
    total_trainers = Trainer.query.count()
    today = date.today()
    today_attendance = Attendance.query.filter(func.date(Attendance.check_in) == today).count()
    
    month_start = date(today.year, today.month, 1)
    monthly_revenue = db.session.query(func.sum(Payment.amount)).filter(
        Payment.payment_date >= month_start
    ).scalar() or 0
    
    return jsonify({
        'total_members': total_members,
        'total_trainers': total_trainers,
        'today_attendance': today_attendance,
        'monthly_revenue': float(monthly_revenue)
    })


# ==================== AI / LLM ROUTES ====================

@app.route('/ai/workout-plan')
@login_required
def workout_plans():
    """List workout plans for current user or all members (admin/trainer)."""
    if current_user.role == 'member':
        member = current_user.member
        if not member:
            flash('Member profile not found.', 'danger')
            return redirect(url_for('dashboard'))
        plans = WorkoutPlan.query.filter_by(member_id=member.id).order_by(WorkoutPlan.created_at.desc()).all()
        members = []
    else:
        plans = WorkoutPlan.query.order_by(WorkoutPlan.created_at.desc()).all()
        members = Member.query.join(User).filter(User.is_active == True).all()
    
    return render_template('workout_plan.html', plans=plans, members=members, ai_available=is_ai_available())


@app.route('/ai/workout-plan/generate', methods=['POST'])
@login_required
def generate_workout_plan_route():
    """Generate a new AI workout plan."""
    member_id = request.form.get('member_id')
    duration_weeks = int(request.form.get('duration_weeks', 4))
    
    # Members can only generate for themselves
    if current_user.role == 'member':
        member = current_user.member
        if not member:
            flash('Member profile not found.', 'danger')
            return redirect(url_for('dashboard'))
        member_id = member.id
    
    member = Member.query.get_or_404(member_id)
    
    member_data = {
        'fitness_goal': member.fitness_goal or 'General Fitness',
        'height': member.height or 170,
        'weight': member.weight or 70,
        'gender': member.gender or 'N/A',
        'medical_conditions': member.medical_conditions or 'None'
    }
    
    try:
        result = generate_workout_plan(member_data, duration_weeks)
        
        plan = WorkoutPlan(
            member_id=member.id,
            title=result['title'],
            plan_content=result['plan_content'],
            fitness_goal=member_data['fitness_goal'],
            duration_weeks=duration_weeks,
            ai_model=result['ai_model']
        )
        db.session.add(plan)
        db.session.commit()
        
        flash(f'AI workout plan generated successfully using {result["ai_model"]}!', 'success')
        return redirect(url_for('workout_plan_detail', plan_id=plan.id))
    except Exception as e:
        flash(f'Error generating workout plan: {str(e)}', 'danger')
        return redirect(url_for('workout_plans'))


@app.route('/ai/workout-plan/<int:plan_id>')
@login_required
def workout_plan_detail(plan_id):
    """View a specific workout plan."""
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    # Members can only view their own plans
    if current_user.role == 'member' and plan.member_id != current_user.member.id:
        flash('You do not have permission to view this plan.', 'danger')
        return redirect(url_for('workout_plans'))
    
    return render_template('workout_plan.html', plan=plan, view_mode=True)


@app.route('/ai/workout-plan/<int:plan_id>/delete', methods=['POST'])
@login_required
def delete_workout_plan(plan_id):
    """Delete a workout plan."""
    plan = WorkoutPlan.query.get_or_404(plan_id)
    
    if current_user.role == 'member' and plan.member_id != current_user.member.id:
        flash('You do not have permission to delete this plan.', 'danger')
        return redirect(url_for('workout_plans'))
    
    db.session.delete(plan)
    db.session.commit()
    flash('Workout plan deleted.', 'success')
    return redirect(url_for('workout_plans'))


# ==================== CHATBOT ROUTES ====================

@app.route('/ai/chatbot')
@login_required
def chatbot_page():
    """Render the chatbot interface."""
    # Load recent chat history for this user
    messages = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.desc()).limit(50).all()
    messages = list(reversed(messages))
    return render_template('chatbot.html', messages=messages, ai_available=is_ai_available())


@app.route('/api/chatbot', methods=['POST'])
@login_required
def api_chatbot():
    """API endpoint for chatbot messages."""
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Save user message
    user_msg = ChatMessage(
        user_id=current_user.id,
        role='user',
        message=user_message
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Build user context
    user_context = {
        'first_name': current_user.first_name,
        'role': current_user.role,
        'fitness_goal': current_user.member.fitness_goal if current_user.member else 'N/A'
    }
    
    try:
        response_text = get_chatbot_response(user_message, user_context)
    except Exception as e:
        response_text = "I'm having trouble thinking right now. Please try again in a moment!"
        print(f"[Chatbot Error] {e}")
    
    # Save assistant message
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role='assistant',
        message=response_text
    )
    db.session.add(assistant_msg)
    db.session.commit()
    
    return jsonify({
        'response': response_text,
        'timestamp': assistant_msg.created_at.isoformat()
    })


@app.route('/api/chatbot/clear', methods=['POST'])
@login_required
def clear_chat_history():
    """Clear chat history for current user."""
    ChatMessage.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'success': True})


# ==================== SMART PAYMENT REMINDERS ====================

@app.route('/ai/payment-reminders')
@login_required
@role_required(['admin'])
def payment_reminders():
    """Admin dashboard for AI-generated payment reminders."""
    today = date.today()
    
    # Get pending and overdue invoices
    pending_invoices = Invoice.query.filter_by(status='pending').order_by(Invoice.due_date.asc()).all()
    overdue_invoices = Invoice.query.filter(
        Invoice.status == 'pending',
        Invoice.due_date < today
    ).order_by(Invoice.due_date.asc()).all()
    
    # Get existing reminders
    existing_reminders = PaymentReminder.query.order_by(PaymentReminder.created_at.desc()).limit(20).all()
    
    overdue_invoice_ids = {inv.id for inv in overdue_invoices}
    
    return render_template('payment_reminders.html',
                         pending_invoices=pending_invoices,
                         overdue_invoices=overdue_invoices,
                         overdue_invoice_ids=overdue_invoice_ids,
                         existing_reminders=existing_reminders,
                         today=today,
                         ai_available=is_ai_available())


@app.route('/api/generate-reminder', methods=['POST'])
@login_required
@role_required(['admin'])
def api_generate_reminder():
    """Generate an AI payment reminder for a specific invoice."""
    data = request.get_json()
    invoice_id = data.get('invoice_id')
    tone = data.get('tone', 'professional')
    
    if not invoice_id:
        return jsonify({'error': 'Invoice ID is required'}), 400
    
    invoice = Invoice.query.get_or_404(invoice_id)
    member = invoice.member
    
    member_data = {
        'first_name': member.user.first_name,
        'last_name': member.user.last_name
    }
    
    invoice_data = {
        'invoice_number': invoice.invoice_number,
        'total_amount': invoice.total_amount,
        'due_date': invoice.due_date.strftime('%Y-%m-%d') if invoice.due_date else 'N/A',
        'days_overdue': (date.today() - invoice.due_date).days if invoice.due_date and invoice.due_date < date.today() else 0
    }
    
    try:
        reminder_message = generate_payment_reminder(member_data, invoice_data, tone)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Save reminder
    reminder = PaymentReminder(
        member_id=member.id,
        invoice_id=invoice.id,
        reminder_message=reminder_message,
        tone=tone
    )
    db.session.add(reminder)
    db.session.commit()
    
    return jsonify({
        'reminder_id': reminder.id,
        'message': reminder_message,
        'tone': tone
    })


@app.route('/api/send-reminder/<int:reminder_id>', methods=['POST'])
@login_required
@role_required(['admin'])
def api_send_reminder(reminder_id):
    """Mark a reminder as sent."""
    reminder = PaymentReminder.query.get_or_404(reminder_id)
    reminder.is_sent = True
    reminder.sent_at = datetime.utcnow()
    db.session.commit()
    
    flash(f'Reminder sent to {reminder.member.user.first_name} {reminder.member.user.last_name}!', 'success')
    return jsonify({'success': True})


# ==================== REVENUE FORECASTING ROUTES ====================

@app.route('/ai/revenue-forecast')
@login_required
@role_required(['admin'])
def revenue_forecast_page():
    """Show revenue forecasting dashboard."""
    # Get historical data
    historical = revenue_forecaster.get_historical_trend(months=6)
    
    # Get predictions
    predictions = revenue_forecaster.predict_next_months(num_months=3)
    
    return render_template('analytics.html',
                         revenue_forecast=predictions,
                         historical_revenue=historical,
                         show_forecast=True)


@app.route('/api/revenue-forecast', methods=['POST'])
@login_required
@role_required(['admin'])
def api_revenue_forecast():
    """API endpoint to generate revenue forecasts."""
    try:
        predictions = revenue_forecaster.predict_next_months(num_months=3)
        return jsonify({
            'success': True,
            'predictions': predictions
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PEAK HOUR PREDICTION ROUTES ====================

@app.route('/ai/peak-hours')
@login_required
def peak_hours_page():
    """Show peak hours prediction page."""
    hourly_pattern = peak_hour_predictor.get_hourly_pattern()
    suggestions = peak_hour_predictor.suggest_schedule()
    
    return render_template('attendance.html',
                         hourly_pattern=hourly_pattern,
                         suggestions=suggestions,
                         show_peak_hours=True)


@app.route('/api/peak-hours', methods=['GET'])
@login_required
def api_peak_hours():
    """API endpoint for peak hour predictions."""
    try:
        peak_data = peak_hour_predictor.get_peak_hours_today()
        hourly = peak_hour_predictor.get_hourly_pattern()
        
        return jsonify({
            'success': True,
            'peak_hours': peak_data,
            'hourly_pattern': hourly
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def error_404(error):
    return render_template('error.html', code=404, message='Page not found'), 404


@app.errorhandler(500)
def error_500(error):
    db.session.rollback()
    return render_template('error.html', code=500, message='Internal server error'), 500


# Main entry point
if __name__ == '__main__':
    init_db()
    seed_data()  # Auto-seed demo data on startup
    app.run(debug=True, host='0.0.0.0', port=5000)
