from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import os
import io
import random

app = Flask(__name__)
app.secret_key = 'interview_prep_secret_key_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///interview_prep.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ─────────────────────────────────────────────
# DATABASE MODELS
# ─────────────────────────────────────────────

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sessions = db.relationship('InterviewSession', backref='user', lazy=True)

class InterviewSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    job_role = db.Column(db.String(100), nullable=False)
    difficulty = db.Column(db.String(20), nullable=False)
    score = db.Column(db.Float, default=0)
    total_questions = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    answers = db.relationship('Answer', backref='interview_session', lazy=True)

class Answer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('interview_session.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    user_answer = db.Column(db.Text, nullable=False)
    ai_feedback = db.Column(db.Text)
    score = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────
# QUESTION BANK (Fallback without API)
# ─────────────────────────────────────────────

QUESTION_BANK = {
    "Software Developer": {
        "Easy": [
            "What is the difference between a stack and a queue?",
            "Explain what Object-Oriented Programming (OOP) means.",
            "What is a loop? Give an example of when you'd use one.",
            "What is the difference between compiled and interpreted languages?",
            "Explain what a function/method is and why we use them.",
            "What is version control and why is it important?",
            "What does HTML stand for and what is it used for?",
            "What is a variable in programming?",
            "Explain the difference between == and === in JavaScript.",
            "What is an API and how does it work?"
        ],
        "Medium": [
            "Explain the concept of recursion with an example.",
            "What is the difference between REST and GraphQL?",
            "How does garbage collection work in programming languages?",
            "Explain the MVC (Model-View-Controller) architecture pattern.",
            "What are design patterns? Name three common ones.",
            "Explain the difference between synchronous and asynchronous programming.",
            "What is database indexing and why is it important?",
            "How does HTTPS work and why is it important?",
            "What is the difference between SQL and NoSQL databases?",
            "Explain the SOLID principles in software development."
        ],
        "Hard": [
            "Design a URL shortening service like bit.ly. What would your architecture look like?",
            "Explain the CAP theorem and its implications for distributed systems.",
            "How would you optimize a slow database query?",
            "Describe how you would implement a rate limiter for an API.",
            "Explain the differences between microservices and monolithic architecture.",
            "How would you design a real-time chat application that scales to millions of users?",
            "What is eventual consistency and when would you use it?",
            "Explain memory management and common issues like memory leaks.",
            "How would you implement a distributed cache system?",
            "Describe the challenges and solutions for handling concurrent transactions in databases."
        ]
    },
    "Data Analyst": {
        "Easy": [
            "What is the difference between mean, median, and mode?",
            "What does SQL stand for and what is it used for?",
            "Explain what a pivot table is and how it's used.",
            "What is data cleaning and why is it important?",
            "What is the difference between qualitative and quantitative data?",
            "What tools have you used for data visualization?",
            "Explain what an outlier is in a dataset.",
            "What is the difference between a bar chart and a histogram?",
            "What is data normalization?",
            "What is a KPI (Key Performance Indicator)?"
        ],
        "Medium": [
            "Explain the difference between correlation and causation with an example.",
            "What is A/B testing and how would you design one?",
            "How do you handle missing data in a dataset?",
            "Explain the concept of statistical significance.",
            "What is regression analysis and when would you use it?",
            "How would you identify trends in a large dataset?",
            "What is the difference between supervised and unsupervised learning?",
            "Explain what a data warehouse is versus a data lake.",
            "How would you validate a data model?",
            "What metrics would you use to measure user engagement for an app?"
        ],
        "Hard": [
            "Design a dashboard to monitor real-time business performance. What metrics would you include?",
            "How would you approach analyzing customer churn for a subscription business?",
            "Explain the concept of cohort analysis and when you'd use it.",
            "How would you detect and handle data quality issues at scale?",
            "Describe how you would build a recommendation system.",
            "How would you communicate a complex statistical finding to a non-technical executive?",
            "Explain time series forecasting and methods you would use.",
            "How would you design an analytics pipeline for streaming data?",
            "What is Bayesian analysis and when is it preferred over frequentist methods?",
            "How would you measure the ROI of a marketing campaign using data?"
        ]
    },
    "Product Manager": {
        "Easy": [
            "What does a Product Manager do on a daily basis?",
            "What is the difference between a feature and a product?",
            "How do you prioritize features in a product backlog?",
            "What is an MVP (Minimum Viable Product)?",
            "How do you gather user feedback?",
            "What is the product lifecycle?",
            "Explain the difference between B2B and B2C products.",
            "What is user research and why is it important?",
            "What metrics would you track for a mobile app?",
            "What is a product roadmap?"
        ],
        "Medium": [
            "How would you decide whether to build, buy, or partner for a new feature?",
            "Describe a time when you had to say no to a feature request. How did you handle it?",
            "How do you work with engineering teams to deliver features on time?",
            "What frameworks do you use to prioritize product decisions?",
            "How would you define success for a new product launch?",
            "Explain the concept of product-market fit.",
            "How would you approach launching a product in a new market?",
            "What is the difference between output and outcome metrics?",
            "How do you handle conflicting requirements from different stakeholders?",
            "Describe your process for writing a product requirements document (PRD)."
        ],
        "Hard": [
            "You're the PM for a social media app that's losing users. What's your action plan?",
            "How would you design a new product feature from ideation to launch?",
            "How do you balance technical debt vs. new feature development?",
            "Design a monetization strategy for a free productivity app.",
            "How would you build a product strategy for entering a market dominated by one competitor?",
            "Describe how you would lead a cross-functional team through a product pivot.",
            "How do you measure the success of a product after launch and iterate accordingly?",
            "Walk me through how you would conduct competitive analysis.",
            "How would you approach pricing strategy for a SaaS product?",
            "Describe how you would handle a major product failure or outage."
        ]
    },
    "UI/UX Designer": {
        "Easy": [
            "What is the difference between UI and UX design?",
            "What is wireframing and why is it used?",
            "Explain what user personas are.",
            "What tools do you use for designing interfaces?",
            "What is a style guide and why is it important?",
            "Explain the concept of visual hierarchy.",
            "What is responsive design?",
            "What is accessibility in design?",
            "What is the difference between a prototype and a mockup?",
            "Explain the term 'information architecture'."
        ],
        "Medium": [
            "How do you conduct user research and what methods do you use?",
            "Explain the design thinking process.",
            "How do you handle feedback and criticism on your designs?",
            "What is usability testing and how do you run a session?",
            "How do you ensure accessibility in your designs?",
            "What is the role of color psychology in UI design?",
            "How do you design for different screen sizes?",
            "What is a design system and how do you build one?",
            "How do you balance aesthetic design with usability?",
            "Describe your process for redesigning an existing product."
        ],
        "Hard": [
            "Walk me through your end-to-end design process for a complex application.",
            "How would you redesign the checkout flow for an e-commerce app to reduce cart abandonment?",
            "How do you design for users with disabilities?",
            "Describe a time when data/research changed your design direction.",
            "How would you build a design system from scratch for a large organization?",
            "How do you measure the success of a UX design?",
            "How would you design an onboarding experience for a complex enterprise tool?",
            "Describe how you collaborate with product managers and engineers.",
            "How would you approach designing for emerging platforms like AR/VR?",
            "How do you handle conflicting feedback from users and stakeholders?"
        ]
    },
    "Machine Learning Engineer": {
        "Easy": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain what a neural network is in simple terms.",
            "What is overfitting and how do you prevent it?",
            "What is the difference between classification and regression?",
            "What is a training dataset vs a test dataset?",
            "What is feature engineering?",
            "What is a confusion matrix?",
            "Explain what gradient descent is.",
            "What is cross-validation?",
            "What are hyperparameters in a machine learning model?"
        ],
        "Medium": [
            "Explain the bias-variance tradeoff.",
            "What is the difference between bagging and boosting?",
            "How does backpropagation work in neural networks?",
            "What is transfer learning and when would you use it?",
            "Explain the attention mechanism in Transformer models.",
            "How do you handle imbalanced datasets?",
            "What is regularization and what are the different types?",
            "Explain the difference between generative and discriminative models.",
            "What is the curse of dimensionality?",
            "How do you evaluate a machine learning model?"
        ],
        "Hard": [
            "Design a machine learning system to detect fraud in real-time transactions.",
            "How would you build and deploy a recommendation system at scale?",
            "Explain how you would approach a new ML problem end-to-end.",
            "How would you handle concept drift in a deployed ML model?",
            "Design an ML pipeline for processing and analyzing millions of images daily.",
            "How do you ensure fairness and reduce bias in machine learning models?",
            "Explain how you would implement a large language model from scratch.",
            "What strategies would you use to reduce inference latency for a deep learning model?",
            "How would you design an A/B testing framework for ML models?",
            "Describe the challenges and solutions for federated learning."
        ]
    }
}

# ─────────────────────────────────────────────
# AI FEEDBACK ENGINE (Built-in, no API needed)
# ─────────────────────────────────────────────

def evaluate_answer(question, answer, job_role, difficulty):
    """Intelligent built-in evaluation engine."""
    if not answer or len(answer.strip()) < 10:
        return {
            "score": 0,
            "rating": "No Answer",
            "feedback": "You didn't provide an answer. In a real interview, always attempt to answer, even if you're unsure.",
            "strengths": [],
            "improvements": ["Provide a complete answer", "Even a partial answer is better than silence", "Try to structure your thinking out loud"],
            "sample_answer": generate_sample_answer(question, job_role)
        }
    
    word_count = len(answer.split())
    has_examples = any(kw in answer.lower() for kw in ['example', 'for instance', 'such as', 'like', 'when i', 'in my', 'e.g'])
    has_structure = any(kw in answer.lower() for kw in ['first', 'second', 'finally', 'however', 'therefore', 'additionally', 'furthermore'])
    is_detailed = word_count > 60
    uses_technical = check_technical_terms(answer, job_role)
    
    # Calculate score
    score = 40  # Base score for attempting
    if word_count > 30: score += 10
    if word_count > 80: score += 10
    if has_examples: score += 15
    if has_structure: score += 10
    if uses_technical: score += 15
    if is_detailed: score += 10
    score = min(score, 98)  # Cap at 98
    
    # Determine rating
    if score >= 85: rating = "Excellent"
    elif score >= 70: rating = "Good"
    elif score >= 55: rating = "Average"
    elif score >= 40: rating = "Needs Work"
    else: rating = "Poor"
    
    # Build feedback
    strengths = []
    improvements = []
    
    if word_count > 50: strengths.append("Good level of detail in your response")
    if has_examples: strengths.append("Great use of examples to illustrate your point")
    if has_structure: strengths.append("Well-structured answer with clear flow")
    if uses_technical: strengths.append("Strong use of technical terminology")
    if word_count < 10: improvements.append("Provide a much more detailed answer")
    if not has_examples: improvements.append("Add concrete examples from your experience")
    if not has_structure: improvements.append("Structure your answer (e.g., use 'First... Then... Finally...')")
    if not uses_technical: improvements.append("Use more domain-specific terminology to demonstrate expertise")
    if word_count > 200: improvements.append("Try to be more concise — aim for 100-150 words in interviews")
    
    if not strengths: strengths.append("You attempted the question, which is a good start")
    if not improvements: improvements.append("Practice delivering this answer more confidently and concisely")
    
    feedback = generate_contextual_feedback(score, rating, word_count, has_examples, has_structure, difficulty)
    
    return {
        "score": round(score, 1),
        "rating": rating,
        "feedback": feedback,
        "strengths": strengths[:3],
        "improvements": improvements[:3],
        "sample_answer": generate_sample_answer(question, job_role)
    }

def check_technical_terms(answer, job_role):
    terms = {
        "Software Developer": ['algorithm', 'function', 'class', 'object', 'api', 'database', 'code', 'loop', 'array', 'variable', 'framework', 'library', 'method', 'debug', 'deploy'],
        "Data Analyst": ['data', 'analysis', 'sql', 'query', 'metric', 'dashboard', 'visualization', 'trend', 'statistics', 'excel', 'python', 'insight', 'dataset', 'model'],
        "Product Manager": ['user', 'feature', 'roadmap', 'backlog', 'sprint', 'stakeholder', 'metric', 'kpi', 'mvp', 'iteration', 'priority', 'customer', 'market'],
        "UI/UX Designer": ['user', 'design', 'prototype', 'wireframe', 'usability', 'interface', 'layout', 'color', 'typography', 'accessibility', 'research', 'flow'],
        "Machine Learning Engineer": ['model', 'training', 'dataset', 'neural', 'algorithm', 'accuracy', 'feature', 'prediction', 'gradient', 'loss', 'epoch', 'layer']
    }
    role_terms = terms.get(job_role, [])
    answer_lower = answer.lower()
    return sum(1 for term in role_terms if term in answer_lower) >= 2

def generate_contextual_feedback(score, rating, word_count, has_examples, has_structure, difficulty):
    if score >= 85:
        return f"Outstanding answer! You demonstrated a strong understanding of the concept. Your response was well-articulated and showed depth of knowledge appropriate for a {difficulty} level question."
    elif score >= 70:
        return f"Good answer overall. You covered the key points effectively. With a bit more detail and structured delivery, this would be a near-perfect interview response."
    elif score >= 55:
        return f"Decent attempt, but there's room to improve. Your answer had the right direction but lacked the depth interviewers expect. Focus on adding specific examples and technical depth."
    elif score >= 40:
        return f"Your answer needs more work. While you attempted the question, the response was too vague. Interviewers want to see that you can articulate concepts clearly and back them up with examples."
    else:
        return f"This answer would not impress in an interview. Take time to study this topic thoroughly. Research the concept, find real-world examples, and practice explaining it in your own words."

def generate_sample_answer(question, job_role):
    samples = {
        "What is the difference between a stack and a queue?": "A stack follows LIFO (Last In, First Out) — like a stack of plates where you add and remove from the top. A queue follows FIFO (First In, First Out) — like a line at a store where people join at the back and leave from the front. Stacks are used in function call management and undo operations, while queues are used in task scheduling and breadth-first search algorithms.",
        "Explain what Object-Oriented Programming (OOP) means.": "OOP is a programming paradigm that organizes code around objects — which are instances of classes that combine data (attributes) and behavior (methods). It's built on four pillars: Encapsulation (bundling data and methods together), Inheritance (child classes inheriting from parent classes), Polymorphism (objects behaving differently based on context), and Abstraction (hiding complex implementation details). For example, a 'Car' class might have attributes like color and speed, and methods like accelerate() and brake().",
        "What is the difference between mean, median, and mode?": "Mean is the average — sum all values and divide by count. Median is the middle value when data is sorted — useful when there are outliers. Mode is the most frequently occurring value. For example, with salaries [30k, 40k, 45k, 50k, 500k], the mean is distorted by the outlier at 108k, but the median of 45k is more representative. I'd use median for salary analysis and mode for categorical data like most popular product category.",
    }
    return samples.get(question, f"A strong answer would define the concept clearly, explain why it matters, provide a concrete example from experience, and connect it to real-world applications. Practice articulating this in 1-2 minutes.")

# ─────────────────────────────────────────────
# ROUTES — AUTH
# ─────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        if user and check_password_hash(user.password_hash, data.get('password')):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Invalid email or password'})
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'success': False, 'message': 'Email already registered'})
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'success': False, 'message': 'Username already taken'})
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            password_hash=generate_password_hash(data.get('password'))
        )
        db.session.add(user)
        db.session.commit()
        session['user_id'] = user.id
        session['username'] = user.username
        return jsonify({'success': True})
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────────
# ROUTES — MAIN APP
# ─────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    sessions = InterviewSession.query.filter_by(user_id=user.id, completed=True).order_by(InterviewSession.created_at.desc()).limit(10).all()
    
    stats = {
        'total_sessions': InterviewSession.query.filter_by(user_id=user.id, completed=True).count(),
        'avg_score': 0,
        'best_score': 0,
        'total_questions': 0
    }
    completed = InterviewSession.query.filter_by(user_id=user.id, completed=True).all()
    if completed:
        scores = [s.score for s in completed if s.score > 0]
        stats['avg_score'] = round(sum(scores) / len(scores), 1) if scores else 0
        stats['best_score'] = round(max(scores), 1) if scores else 0
        stats['total_questions'] = sum(s.total_questions for s in completed)
    
    return render_template('dashboard.html', user=user, sessions=sessions, stats=stats)

@app.route('/interview')
def interview():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('interview.html')

@app.route('/api/start_session', methods=['POST'])
def start_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    job_role = data.get('job_role')
    difficulty = data.get('difficulty')
    num_questions = int(data.get('num_questions', 5))
    
    questions_pool = QUESTION_BANK.get(job_role, {}).get(difficulty, [])
    if not questions_pool:
        return jsonify({'error': 'Invalid role or difficulty'}), 400
    
    questions = random.sample(questions_pool, min(num_questions, len(questions_pool)))
    
    interview_session = InterviewSession(
        user_id=session['user_id'],
        job_role=job_role,
        difficulty=difficulty,
        total_questions=len(questions)
    )
    db.session.add(interview_session)
    db.session.commit()
    
    return jsonify({
        'session_id': interview_session.id,
        'questions': questions,
        'job_role': job_role,
        'difficulty': difficulty
    })

@app.route('/api/submit_answer', methods=['POST'])
def submit_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    session_id = data.get('session_id')
    question = data.get('question')
    user_answer = data.get('answer')
    
    interview_session = InterviewSession.query.get(session_id)
    if not interview_session or interview_session.user_id != session['user_id']:
        return jsonify({'error': 'Invalid session'}), 400
    
    evaluation = evaluate_answer(question, user_answer, interview_session.job_role, interview_session.difficulty)
    
    answer = Answer(
        session_id=session_id,
        question=question,
        user_answer=user_answer,
        ai_feedback=json.dumps(evaluation),
        score=evaluation['score']
    )
    db.session.add(answer)
    db.session.commit()
    
    return jsonify(evaluation)

@app.route('/api/complete_session', methods=['POST'])
def complete_session():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    data = request.get_json()
    session_id = data.get('session_id')
    
    interview_session = InterviewSession.query.get(session_id)
    if not interview_session:
        return jsonify({'error': 'Session not found'}), 404
    
    answers = Answer.query.filter_by(session_id=session_id).all()
    if answers:
        avg_score = sum(a.score for a in answers) / len(answers)
        interview_session.score = round(avg_score, 1)
    
    interview_session.completed = True
    db.session.commit()
    
    return jsonify({'success': True, 'final_score': interview_session.score})

@app.route('/api/session_history/<int:session_id>')
def session_history(session_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    interview_session = InterviewSession.query.get(session_id)
    if not interview_session or interview_session.user_id != session['user_id']:
        return jsonify({'error': 'Not found'}), 404
    
    answers = Answer.query.filter_by(session_id=session_id).all()
    result = []
    for a in answers:
        feedback = json.loads(a.ai_feedback) if a.ai_feedback else {}
        result.append({
            'question': a.question,
            'answer': a.user_answer,
            'score': a.score,
            'feedback': feedback
        })
    
    return jsonify({
        'job_role': interview_session.job_role,
        'difficulty': interview_session.difficulty,
        'score': interview_session.score,
        'date': interview_session.created_at.strftime('%b %d, %Y'),
        'answers': result
    })

@app.route('/api/download_report/<int:session_id>')
def download_report(session_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    interview_session = InterviewSession.query.get(session_id)
    if not interview_session or interview_session.user_id != session['user_id']:
        return "Not found", 404
    
    user = User.query.get(session['user_id'])
    answers = Answer.query.filter_by(session_id=session_id).all()
    
    # Generate plain text report
    report_lines = [
        "=" * 60,
        "       AI INTERVIEW PREPARATION REPORT",
        "=" * 60,
        f"Candidate: {user.username}",
        f"Job Role: {interview_session.job_role}",
        f"Difficulty: {interview_session.difficulty}",
        f"Date: {interview_session.created_at.strftime('%B %d, %Y')}",
        f"Overall Score: {interview_session.score}/100",
        "=" * 60,
        ""
    ]
    
    for i, answer in enumerate(answers, 1):
        feedback = json.loads(answer.ai_feedback) if answer.ai_feedback else {}
        report_lines.extend([
            f"QUESTION {i}: {answer.question}",
            "-" * 40,
            f"Your Answer: {answer.user_answer}",
            f"Score: {answer.score}/100 ({feedback.get('rating', 'N/A')})",
            f"Feedback: {feedback.get('feedback', 'N/A')}",
            "",
            "Strengths:",
            *[f"  + {s}" for s in feedback.get('strengths', [])],
            "",
            "Areas to Improve:",
            *[f"  - {i}" for i in feedback.get('improvements', [])],
            "",
            f"Sample Answer: {feedback.get('sample_answer', 'N/A')}",
            "",
            "=" * 60,
            ""
        ])
    
    report_text = "\n".join(report_lines)
    buf = io.BytesIO(report_text.encode('utf-8'))
    buf.seek(0)
    
    return send_file(
        buf,
        as_attachment=True,
        download_name=f"interview_report_{session_id}.txt",
        mimetype='text/plain'
    )

@app.route('/api/roles')
def get_roles():
    return jsonify(list(QUESTION_BANK.keys()))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)