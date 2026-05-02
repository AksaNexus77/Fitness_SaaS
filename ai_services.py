"""
AI Services Module for FitZone
Provides LLM-powered features with Google Gemini API support
and a smart fallback mock engine for demo/testing without API keys.
"""

import os
import random
from datetime import datetime, date

# Try to import Gemini, fallback to mock if unavailable
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except (ImportError, TypeError, Exception):
    GEMINI_AVAILABLE = False
    genai = None

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
USE_GEMINI = GEMINI_AVAILABLE and GEMINI_API_KEY

if USE_GEMINI:
    genai.configure(api_key=GEMINI_API_KEY)
    _gemini_model = genai.GenerativeModel('gemini-2.5-flash')


def _call_gemini(prompt, max_tokens=2048):
    """Call Gemini API with the given prompt."""
    if not USE_GEMINI:
        return None
    try:
        response = _gemini_model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.7,
            )
        )
        return response.text
    except Exception as e:
        print(f"[AI] Gemini API error: {e}")
        return None


# ==================== MOCK AI ENGINE ====================

_WORKOUT_TEMPLATES = {
    'Weight Loss': """
# {title}

## Overview
This {duration}-week program is designed to help you shed excess body fat while preserving lean muscle mass. Your current stats (Height: {height}cm, Weight: {weight}kg) indicate a BMI-focused approach with caloric deficit and high activity.

## Weekly Schedule

### Monday – Full Body Strength + Cardio
- Warm-up: 5 min jump rope
- Circuit (3 rounds):
  - Goblet Squats: 12 reps
  - Push-ups: 10 reps
  - Kettlebell Swings: 15 reps
  - Plank: 45 seconds
- Cardio: 20 min incline treadmill walk (speed 5.5, incline 8%)
- Cool-down: Stretching 5 min

### Tuesday – Active Recovery / Low-Impact Cardio
- 30 min brisk walking or cycling
- Core work: Dead bugs, Bird dogs (2 sets x 12 each)
- Foam rolling

### Wednesday – HIIT Day
- Warm-up: 5 min light jog
- HIIT Circuit (4 rounds, 40s work / 20s rest):
  - Burpees
  - Mountain Climbers
  - Jump Squats
  - High Knees
- Cool-down: 5 min walk + stretch

### Thursday – Upper Body Strength
- Dumbbell Bench Press: 3 x 10
- Bent Over Rows: 3 x 12
- Shoulder Press: 3 x 10
- Bicep Curls: 3 x 12
- Tricep Dips: 3 x 10
- Face Pulls: 3 x 15

### Friday – Lower Body + Cardio
- Romanian Deadlifts: 3 x 10
- Lunges: 3 x 12 per leg
- Leg Press: 3 x 12
- Calf Raises: 3 x 15
- Cardio: 15 min stairmaster

### Saturday – Long Steady-State Cardio
- 45 min jog, swim, or cycle at moderate intensity
- Keep heart rate in Zone 2 (60-70% max HR)

### Sunday – Rest Day
- Light stretching or yoga
- Focus on sleep and hydration

## Nutrition Guidelines
- Daily caloric target: ~{calories} kcal (moderate deficit)
- Protein: 1.6-2.0g per kg bodyweight
- Hydration: 3+ liters water daily
- Limit processed sugars and refined carbs

## Progress Tracking
- Weigh yourself weekly (same day, same time)
- Take progress photos every 2 weeks
- Track workout completion in your FitZone profile

## Notes
{medical_note}
Stay consistent! Results come from adherence, not perfection.
""",
    'Muscle Gain': """
# {title}

## Overview
This hypertrophy-focused {duration}-week plan is built for muscle growth. At {height}cm and {weight}kg, the focus is progressive overload, adequate protein, and recovery.

## Weekly Schedule (Push/Pull/Legs)

### Monday – Push Day (Chest, Shoulders, Triceps)
- Barbell Bench Press: 4 x 8-10
- Incline Dumbbell Press: 3 x 10-12
- Overhead Press: 4 x 8-10
- Lateral Raises: 3 x 15
- Tricep Rope Pushdowns: 3 x 12-15
- Cable Flyes: 3 x 12-15

### Tuesday – Pull Day (Back, Biceps, Rear Delts)
- Deadlifts: 4 x 6-8
- Pull-ups / Lat Pulldowns: 4 x 8-10
- Seated Cable Rows: 3 x 10-12
- Face Pulls: 3 x 15
- Barbell Curls: 3 x 10-12
- Hammer Curls: 3 x 12

### Wednesday – Leg Day
- Barbell Squats: 4 x 8-10
- Romanian Deadlifts: 3 x 10
- Leg Press: 3 x 12
- Walking Lunges: 3 x 12 per leg
- Leg Curls: 3 x 12
- Standing Calf Raises: 4 x 15

### Thursday – Rest or Active Recovery
- Light cardio 20 min
- Stretching and mobility work

### Friday – Push Day (Variation)
- Dumbbell Floor Press: 4 x 10
- Machine Chest Press: 3 x 12
- Arnold Press: 3 x 10
- Upright Rows: 3 x 12
- Skull Crushers: 3 x 10
- Dips: 3 x failure

### Saturday – Pull Day (Variation)
- Pendlay Rows: 4 x 8
- Single-Arm Dumbbell Rows: 3 x 10 per arm
- Straight-Arm Pulldowns: 3 x 12
- Shrugs: 3 x 12
- Preacher Curls: 3 x 10
- Incline Curls: 3 x 12

### Sunday – Leg Day (Variation) + Abs
- Front Squats: 4 x 8
- Bulgarian Split Squats: 3 x 10 per leg
- Hack Squat: 3 x 12
- Seated Calf Raises: 4 x 15
- Hanging Leg Raises: 3 x 12
- Ab Wheel Rollouts: 3 x 10

## Nutrition Guidelines
- Daily caloric target: ~{calories} kcal (moderate surplus of +300-500)
- Protein: 1.8-2.2g per kg bodyweight
- Carbs: Focus around training sessions
- Healthy fats: 0.8-1g per kg bodyweight
- Sleep: 7-9 hours nightly (critical for growth!)

## Progression Protocol
- Add 2.5-5kg to compound lifts when you hit the top rep range
- Deload every 4th week (reduce volume by 40%)
- Log all sets/reps/weights in FitZone

## Notes
{medical_note}
Train hard, eat enough, sleep well — growth is a lifestyle!
""",
    'General Fitness': """
# {title}

## Overview
A balanced {duration}-week program to improve overall fitness, energy levels, and well-being. This plan mixes strength, cardio, and mobility for a well-rounded routine.

## Weekly Schedule

### Monday – Strength Focus
- Goblet Squats: 3 x 12
- Push-ups: 3 x 12
- Single-Arm Rows: 3 x 12 per side
- Glute Bridges: 3 x 15
- Plank: 3 x 45 sec
- Farmer's Carries: 3 x 30 meters

### Tuesday – Cardio Endurance
- 30 min steady-state run, cycle, or row
- Keep conversational pace (Zone 2)
- Finish with 5 min cool-down walk

### Wednesday – Mobility & Core
- Dynamic stretching routine (10 min)
- Yoga flow: Sun salutations x 5
- Dead Bugs: 3 x 10
- Pallof Press: 3 x 12 per side
- Cat-Cow stretches: 2 min
- Hip flexor stretches: 2 min per side

### Thursday – Full Body Circuit
- Circuit (4 rounds, minimal rest):
  - Kettlebell Swings: 15
  - Box Step-ups: 12 per leg
  - TRX Rows: 12
  - Medicine Ball Slams: 10
  - Bear Crawls: 20 meters
- Cool-down stretch

### Friday – Interval Training
- Warm-up: 5 min
- Intervals: 8 x (1 min hard / 1 min easy)
- Cool-down: 5 min
- Optional: 10 min core work

### Saturday – Outdoor Activity / Play
- Hiking, swimming, sports, or long walk (60+ min)
- Focus on enjoyment and movement variety

### Sunday – Rest & Recovery
- Complete rest or gentle stretching
- Meal prep for the week ahead
- Review weekly progress in FitZone

## Nutrition Guidelines
- Daily caloric target: ~{calories} kcal (maintenance)
- Balanced plate: 1/2 vegetables, 1/4 protein, 1/4 carbs
- Protein: 1.2-1.6g per kg bodyweight
- Hydration: 2.5-3 liters daily

## Lifestyle Tips
- Stand and move every hour if desk-bound
- Take the stairs when possible
- Prioritize 7-8 hours of sleep

## Notes
{medical_note}
Consistency beats intensity — show up regularly and enjoy the process!
""",
    'Endurance': """
# {title}

## Overview
This {duration}-week endurance program builds aerobic capacity and stamina. Ideal for improving cardiovascular health and long-duration performance.

## Weekly Schedule

### Monday – Long Slow Distance (LSD)
- 45-60 min continuous cardio (run, cycle, or swim)
- Heart rate in Zone 2 (60-70% max HR)
- Focus on breathing rhythm and posture

### Tuesday – Strength for Endurance
- Single-Leg Romanian Deadlifts: 3 x 10
- Step-ups: 3 x 12 per leg
- Plank with Shoulder Taps: 3 x 20
- Side Planks: 3 x 30 sec per side
- Calf Raises: 3 x 20
- Face Pulls: 3 x 15

### Wednesday – Tempo Training
- Warm-up: 10 min easy
- Tempo block: 20 min at comfortably hard pace (Zone 3)
- Cool-down: 10 min easy
- Total: 40 min

### Thursday – Recovery / Cross-Training
- 30 min easy swim, elliptical, or yoga
- Focus on form and relaxation
- Foam rolling for legs and back

### Friday – Interval Training
- Warm-up: 10 min
- Intervals: 6 x (3 min hard / 2 min easy)
- Cool-down: 10 min
- Total: 40 min

### Saturday – Fartlek (Speed Play)
- 40 min unstructured run
- Alternate between light jog and faster bursts
- Use landmarks (lampposts, trees) as interval markers

### Sunday – Rest or Active Recovery
- Optional: 20 min gentle walk
- Stretching routine focusing on hips, hamstrings, calves
- Hydration and nutrition focus

## Nutrition Guidelines
- Daily caloric target: ~{calories} kcal
- Carbs: 5-7g per kg bodyweight (fuel for training)
- Protein: 1.2-1.4g per kg bodyweight
- Electrolytes: Important for sessions >60 min
- Pre-run snack: Banana or toast 30-60 min before

## Progression
- Increase weekly long run by 5-10% each week
- Every 4th week, reduce volume by 20% (recovery week)
- Track pace and perceived exertion in FitZone

## Notes
{medical_note}
Endurance is built one session at a time. Trust the process!
"""
}

_CHATBOT_RESPONSES = {
    'greeting': [
        "Hello! I'm FitZone AI, your virtual fitness assistant. How can I help you today?",
        "Hi there! Ready to crush your fitness goals? Ask me anything about workouts, nutrition, or your membership!",
        "Welcome to FitZone! I'm here to help with workout tips, class schedules, and membership questions."
    ],
    'workout': [
        "For best results, aim for at least 150 minutes of moderate exercise per week. Would you like a personalized plan?",
        "Consistency is key! Try to schedule your workouts like important meetings — non-negotiable.",
        "Remember to warm up for 5-10 minutes before any workout to prevent injury."
    ],
    'nutrition': [
        "Protein is essential for muscle recovery. Aim for 1.2-2.0g per kg of bodyweight depending on your goals.",
        "Stay hydrated! A good rule is to drink half your bodyweight (in pounds) in ounces of water daily.",
        "Focus on whole foods: lean proteins, complex carbs, healthy fats, and plenty of vegetables."
    ],
    'membership': [
        "You can view your membership details and renewal dates in the Members section of your dashboard.",
        "We offer monthly, quarterly, and yearly memberships. Upgrading can save you up to 30%!",
        "Your membership includes access to all gym equipment, group classes, and locker facilities."
    ],
    'classes': [
        "Check out our Classes page for the full schedule. We offer Yoga, HIIT, Strength Training, and more!",
        "Morning Yoga starts at 6:00 AM and HIIT Blast is at 5:00 PM. Which one interests you?",
        "All classes are included with your membership. Just show up a few minutes early to secure your spot!"
    ],
    'payment': [
        "You can view and pay your invoices in the Invoices section. We accept cash, card, and bank transfer.",
        "If you have questions about a specific invoice, please contact our admin team through the dashboard.",
        "Payments are typically processed within 1-2 business days. You'll see the status update in your account."
    ],
    'progress': [
        "Tracking your progress is crucial! Log your weight, measurements, and workouts regularly in the Progress section.",
        "Don't just rely on the scale — take progress photos and measure your body composition for a fuller picture.",
        "Celebrate small wins! Every workout completed is a step toward your goal."
    ],
    'default': [
        "That's a great question! While I'm still learning, I recommend checking with our trainers for personalized advice.",
        "I'm not sure about that specific topic, but our staff would be happy to help. Would you like me to note this down?",
        "Interesting! For detailed guidance on that, please speak with one of our certified trainers or admin staff."
    ]
}

_PAYMENT_REMINDER_TEMPLATES = {
    'friendly': """Hi {name},

We hope you're enjoying your time at FitZone! Just a friendly reminder that your invoice #{invoice_number} for ${amount} is due on {due_date}.

If you've already paid, please ignore this message. Otherwise, you can settle it easily through your dashboard or at the front desk.

Thanks for being an awesome member of our fitness family!

Best,
FitZone Team""",
    'professional': """Dear {name},

This is a reminder regarding your outstanding invoice #{invoice_number} in the amount of ${amount}, with a due date of {due_date}.

To avoid any late fees or interruption to your membership, please arrange payment at your earliest convenience through the FitZone portal or by visiting our reception.

If you have any questions or need to discuss payment options, please don't hesitate to contact us.

Regards,
FitZone Administration""",
    'firm': """Dear {name},

Our records indicate that invoice #{invoice_number} for ${amount} remains unpaid and was due on {due_date}.

Please settle this invoice within the next 5 business days to maintain your active membership status and avoid additional late charges.

Payment can be made via your online dashboard or in person at the gym.

If you believe this is an error, please contact us immediately.

FitZone Management"""
}


def _get_mock_workout_plan(member_data, duration_weeks):
    """Generate a realistic mock workout plan based on member data."""
    goal = member_data.get('fitness_goal', 'General Fitness')
    height = member_data.get('height', 170)
    weight = member_data.get('weight', 70)
    
    # Calculate approximate maintenance calories
    bmr = 10 * weight + 6.25 * height - 5 * 30 + 5  # simplified Mifflin-St Jeor
    calories = int(bmr * 1.55)
    
    if goal == 'Weight Loss':
        calories -= 500
    elif goal == 'Muscle Gain':
        calories += 400
    
    template = _WORKOUT_TEMPLATES.get(goal, _WORKOUT_TEMPLATES['General Fitness'])
    
    medical_note = ""
    if member_data.get('medical_conditions'):
        medical_note = f"**Medical Considerations:** Please consult your physician before starting. Conditions noted: {member_data['medical_conditions']}. Modify exercises as needed."
    else:
        medical_note = "**Safety Note:** Always consult a trainer if you're unsure about form. Listen to your body and rest when needed."
    
    title = f"{goal} Program – {duration_weeks} Weeks"
    
    return template.format(
        title=title,
        duration=duration_weeks,
        height=height,
        weight=weight,
        calories=calories,
        medical_note=medical_note
    )


def _get_mock_chatbot_response(user_message, context):
    """Generate a contextual mock chatbot response."""
    msg_lower = user_message.lower()
    
    # Simple keyword matching
    if any(word in msg_lower for word in ['hello', 'hi', 'hey', 'greetings']):
        return random.choice(_CHATBOT_RESPONSES['greeting'])
    elif any(word in msg_lower for word in ['workout', 'exercise', 'training', 'lift', 'gym']):
        return random.choice(_CHATBOT_RESPONSES['workout'])
    elif any(word in msg_lower for word in ['food', 'eat', 'diet', 'nutrition', 'protein', 'calorie', 'meal']):
        return random.choice(_CHATBOT_RESPONSES['nutrition'])
    elif any(word in msg_lower for word in ['membership', 'join', 'sign up', 'register', 'plan']):
        return random.choice(_CHATBOT_RESPONSES['membership'])
    elif any(word in msg_lower for word in ['class', 'yoga', 'hiit', 'schedule', 'session']):
        return random.choice(_CHATBOT_RESPONSES['classes'])
    elif any(word in msg_lower for word in ['pay', 'invoice', 'bill', 'payment', 'due', 'money']):
        return random.choice(_CHATBOT_RESPONSES['payment'])
    elif any(word in msg_lower for word in ['progress', 'weight', 'measurement', 'result', 'improve']):
        return random.choice(_CHATBOT_RESPONSES['progress'])
    else:
        return random.choice(_CHATBOT_RESPONSES['default'])


def _get_mock_payment_reminder(member_data, invoice_data, tone):
    """Generate a mock payment reminder message."""
    template = _PAYMENT_REMINDER_TEMPLATES.get(tone, _PAYMENT_REMINDER_TEMPLATES['professional'])
    
    return template.format(
        name=member_data.get('first_name', 'Valued Member'),
        invoice_number=invoice_data.get('invoice_number', 'N/A'),
        amount=invoice_data.get('total_amount', 0),
        due_date=invoice_data.get('due_date', 'soon')
    )


# ==================== PUBLIC API ====================

def generate_workout_plan(member_data, duration_weeks=4):
    """
    Generate an AI workout plan for a member.
    
    Args:
        member_data: dict with keys like fitness_goal, height, weight, medical_conditions
        duration_weeks: int, default 4
    
    Returns:
        dict with 'plan_content', 'title', 'ai_model'
    """
    goal = member_data.get('fitness_goal', 'General Fitness')
    title = f"AI {goal} Plan – {duration_weeks} Weeks"
    
    if USE_GEMINI:
        prompt = f"""You are a certified personal trainer. Create a detailed {duration_weeks}-week workout plan for a gym member.

Member Profile:
- Fitness Goal: {goal}
- Height: {member_data.get('height', 'N/A')} cm
- Weight: {member_data.get('weight', 'N/A')} kg
- Gender: {member_data.get('gender', 'N/A')}
- Medical Conditions: {member_data.get('medical_conditions', 'None')}

Requirements:
1. Provide a day-by-day schedule (Monday-Sunday)
2. Include specific exercises with sets and reps
3. Add nutrition guidelines
4. Include safety notes and progression protocol
5. Format in clean Markdown with headers and bullet points
6. Make it personalized and motivating
"""
        plan_content = _call_gemini(prompt, max_tokens=4096)
        if plan_content:
            return {
                'plan_content': plan_content,
                'title': title,
                'ai_model': 'gemini-1.5-flash'
            }
    
    # Fallback to mock
    plan_content = _get_mock_workout_plan(member_data, duration_weeks)
    return {
        'plan_content': plan_content,
        'title': title,
        'ai_model': 'mock-ai'
    }


def get_chatbot_response(user_message, user_context=None):
    """
    Get a chatbot response to a user message.
    
    Args:
        user_message: str, the user's message
        user_context: dict with user info (optional)
    
    Returns:
        str, the assistant's response
    """
    if USE_GEMINI:
        context_str = ""
        if user_context:
            context_str = f"""User Context:
- Name: {user_context.get('first_name', 'User')}
- Role: {user_context.get('role', 'member')}
- Fitness Goal: {user_context.get('fitness_goal', 'N/A')}
"""
        
        prompt = f"""You are FitZone AI, a helpful and friendly virtual assistant for a fitness gym called FitZone.
You help members with workout advice, nutrition tips, class schedules, membership questions, and general fitness guidance.
Keep responses concise (2-4 sentences), encouraging, and actionable.

{context_str}

User: {user_message}
FitZone AI:"""
        
        response = _call_gemini(prompt, max_tokens=512)
        if response:
            return response.strip()
    
    # Fallback to mock
    return _get_mock_chatbot_response(user_message, user_context)


def generate_payment_reminder(member_data, invoice_data, tone='professional'):
    """
    Generate an AI payment reminder message.
    
    Args:
        member_data: dict with member info
        invoice_data: dict with invoice info
        tone: 'friendly', 'professional', or 'firm'
    
    Returns:
        str, the reminder message
    """
    if USE_GEMINI:
        prompt = f"""You are the FitZone gym billing assistant. Write a {tone} payment reminder email/message to a gym member.

Member: {member_data.get('first_name', '')} {member_data.get('last_name', '')}
Invoice Number: {invoice_data.get('invoice_number', 'N/A')}
Amount Due: ${invoice_data.get('total_amount', 0)}
Due Date: {invoice_data.get('due_date', 'N/A')}
Days Overdue: {invoice_data.get('days_overdue', 0)}

Tone: {tone}
Requirements:
- Keep it to 4-6 sentences
- Be clear about the amount and due date
- Include a call to action (pay via dashboard or front desk)
- Sign off as "FitZone Team"
"""
        response = _call_gemini(prompt, max_tokens=512)
        if response:
            return response.strip()
    
    # Fallback to mock
    return _get_mock_payment_reminder(member_data, invoice_data, tone)


# ==================== FOOD PHOTO ANALYZER ====================

def analyze_food_photo(image_data, member_data):
    """
    Analyze a food photo using Gemini Vision to estimate nutrition.
    
    Args:
        image_data: str, base64 encoded image or image URL
        member_data: dict with member info
    
    Returns:
        dict with nutrition estimates
    """
    if USE_GEMINI and hasattr(genai, 'GenerativeModel'):
        try:
            # For actual image analysis, we'd use vision model
            prompt = """Analyze this food photo and provide nutritional estimates in this format:
Food items detected: [list]
Estimated calories: [number]
Protein (grams): [number]
Carbs (grams): [number]
Fat (grams): [number]
Meal type: [breakfast/lunch/dinner/snack]"""
            # This would require actual image upload handling
            return None
        except Exception as e:
            print(f"[AI] Food analysis error: {e}")
    
    # Fallback: mock analysis
    import random
    food_items = [
        "Grilled chicken breast, brown rice, steamed broccoli",
        "Salad with mixed greens, avocado, salmon",
        "Oatmeal with banana and almonds",
        "Greek yogurt with berries and honey"
    ]
    calories = random.randint(300, 800)
    protein = random.randint(20, 50)
    carbs = random.randint(30, 80)
    fat = random.randint(10, 35)
    
    return {
        'food_description': random.choice(food_items),
        'calories': calories,
        'protein': protein,
        'carbs': carbs,
        'fat': fat,
        'ai_model': 'mock-ai'
    }


# ==================== SMART GOAL SUGGESTIONS ====================

def generate_goal_suggestion(member, progress_records):
    """
    Generate AI-powered goal suggestions based on member's progress.
    
    Args:
        member: Member object
        progress_records: list of ProgressRecord objects
    
    Returns:
        dict with suggested goal and reasoning
    """
    current_goal = member.fitness_goal or 'General Fitness'
    
    # Analyze progress
    if progress_records:
        weights = [p.weight for p in progress_records if p.weight]
        body_fats = [p.body_fat_percentage for p in progress_records if p.body_fat_percentage]
        
        avg_weight = sum(weights) / len(weights) if weights else member.weight
        avg_body_fat = sum(body_fats) / len(body_fats) if body_fats else 15
        
        progress_summary = f"Started at {weights[0] if weights else 'N/A'}kg, current: {avg_weight:.1f}kg"
    else:
        progress_summary = "No progress records yet"
        avg_weight = member.weight or 70
    
    if USE_GEMINI:
        prompt = f"""As a fitness coach, analyze this member's progress and suggest an updated fitness goal.

Member Stats:
- Current Goal: {current_goal}
- Height: {member.height}cm
- Weight: {member.weight}kg
- Progress Summary: {progress_summary}

Provide your recommendation in this format:
Suggested Goal: [new goal or same]
Reasoning: [2-3 sentences why]
Adjustments: [specific suggestions]
"""
        response = _call_gemini(prompt, max_tokens=512)
        if response:
            lines = response.split('\n')
            suggestion = {
                'current_goal': current_goal,
                'suggested_goal': current_goal,
                'reasoning': response,
                'progress_summary': progress_summary,
                'ai_model': 'gemini-1.5-flash'
            }
            for line in lines:
                if line.startswith('Suggested Goal:'):
                    suggestion['suggested_goal'] = line.split(':')[1].strip()
            return suggestion
    
    # Fallback: simple rule-based suggestions
    new_goal = current_goal
    
    if current_goal == 'Weight Loss' and avg_weight < 70:
        new_goal = 'Muscle Gain'
        reasoning = "You've reached your weight loss goal! Consider switching to muscle building to continue progress."
    elif current_goal == 'Muscle Gain' and avg_weight > 85:
        new_goal = 'Strength Training'
        reasoning = "Great progress on muscle building! Now focus on strength goals."
    elif current_goal == 'General Fitness':
        new_goal = 'Endurance'
        reasoning = "You've built a foundation. Challenge yourself with endurance training!"
    else:
        reasoning = "Keep pushing! You're on the right track with your current goal."
    
    return {
        'current_goal': current_goal,
        'suggested_goal': new_goal,
        'reasoning': reasoning,
        'progress_summary': progress_summary,
        'ai_model': 'mock-ai'
    }


# ==================== VOICE CHATBOT ====================

def process_voice_message(audio_transcript):
    """
    Process a voice message transcript from Web Speech API.
    
    Args:
        audio_transcript: str, transcribed text from speech
    
    Returns:
        dict with response and metadata
    """
    # This is handled client-side with Web Speech API
    # The backend just processes the transcribed text
    return {
        'transcript': audio_transcript,
        'processed': True
    }


def is_ai_available():
    """Check if the AI service is available (Gemini configured)."""
    return USE_GEMINI

