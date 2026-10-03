import os
import sqlite3
from flask import (
    Flask, render_template_string, request, jsonify, redirect, url_for, session
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-me')
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'portfolio.db')

# ==========================================
# DATABASE INITIALIZATION & HELPER FUNCTIONS
# ==========================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Admin / Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Profile Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            title TEXT,
            bio TEXT,
            about_story TEXT,
            education TEXT,
            interests TEXT,
            career_goals TEXT,
            email TEXT,
            github TEXT,
            linkedin TEXT,
            twitter TEXT,
            avatar_url TEXT
        )
    ''')

    # Skills Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            proficiency INTEGER NOT NULL
        )
    ''')

    # Projects Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            technologies TEXT NOT NULL,
            github_url TEXT,
            demo_url TEXT,
            image_url TEXT,
            challenges TEXT,
            learnings TEXT,
            featured INTEGER DEFAULT 0
        )
    ''')

    # Settings / Appearance Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')

    # Seed Default Data if Empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        # Default Admin: username='admin', password='password123'
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                       ('admin', generate_password_hash('password123')))

    cursor.execute("SELECT COUNT(*) FROM profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO profile (name, title, bio, about_story, education, interests, career_goals, email, github, linkedin, twitter, avatar_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'Blessing',
            'Full-Stack Developer & AI Specialist',
            'Building intelligent web applications, interactive software, and scalable digital platforms.',
            'Passionate about software architecture, creative coding, and modern web systems.',
            'B.Sc. Computer Science / Self-Taught Software Engineer',
            'AI/ML Workflows, Game Development, UI/UX Design, Open Source',
            'To design and architect next-generation web platforms and AI tools.',
            'blessing@example.com',
            'https://github.com',
            'https://linkedin.com',
            'https://x.com',
            'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80'
        ))

    cursor.execute("SELECT COUNT(*) FROM skills")
    if cursor.fetchone()[0] == 0:
        default_skills = [
            ('Python', 'Backend', 90),
            ('JavaScript', 'Frontend', 85),
            ('HTML/CSS', 'Frontend', 95),
            ('Flask / Web Frameworks', 'Backend', 85),
            ('SQLite / Databases', 'Backend', 80),
            ('AI / Machine Learning', 'AI', 75),
            ('Git / Version Control', 'Tools', 80)
        ]
        cursor.executemany("INSERT INTO skills (name, category, proficiency) VALUES (?, ?, ?)", default_skills)

    cursor.execute("SELECT COUNT(*) FROM projects")
    if cursor.fetchone()[0] == 0:
        default_projects = [
            (
                'AI Portfolio Management System',
                'A full-stack, dynamic portfolio content management system with authentication and real-time customization.',
                'Python, Flask, SQLite, JavaScript, HTML/CSS',
                'https://github.com',
                'https://example.com',
                'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&auto=format&fit=crop&q=80',
                'Managing state and custom dynamic theme configurations seamlessly.',
                'Mastered REST API structure, dynamic database rendering, and Flask session handling.',
                1
            ),
            (
                'AI Image Generator & Workflows',
                'Custom web UI and execution pipeline for generative media and visual script automation.',
                'Python, PyTorch, Stable Diffusion, JavaScript',
                'https://github.com',
                'https://example.com',
                'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=800&auto=format&fit=crop&q=80',
                'Optimizing GPU resource execution times and batch processing.',
                'Gained deep understanding of neural rendering and API integration.',
                1
            )
        ]
        cursor.executemany('''
            INSERT INTO projects (title, description, technologies, github_url, demo_url, image_url, challenges, learnings, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', default_projects)

    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        default_settings = [
            ('primary_color', '#6366f1'),
            ('bg_color', '#0f172a'),
            ('card_color', '#1e293b'),
            ('text_color', '#f8fafc'),
            ('font_family', 'Inter, system-ui, sans-serif'),
            ('show_about', 'true'),
            ('show_skills', 'true'),
            ('show_projects', 'true'),
            ('show_contact', 'true')
        ]
        cursor.executemany("INSERT INTO settings (key, value) VALUES (?, ?)", default_settings)

    conn.commit()
    conn.close()

# ==========================================
# SINGLE HTML TEMPLATE (Frontend + Admin CMS)
# ==========================================

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ profile.name }} — Developer Portfolio</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary-color: {{ settings.primary_color or '#6366f1' }};
            --bg-color: {{ settings.bg_color or '#0f172a' }};
            --card-color: {{ settings.card_color or '#1e293b' }};
            --text-color: {{ settings.text_color or '#f8fafc' }};
            --font-family: {{ settings.font_family or 'Inter, system-ui, sans-serif' }};
            --accent-glow: rgba(99, 102, 241, 0.25);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: var(--font-family);
        }

        body {
            background-color: var(--bg-color);
            color: var(--text-color);
            line-height: 1.6;
            overflow-x: hidden;
        }

        a {
            color: var(--primary-color);
            text-decoration: none;
            transition: all 0.3s ease;
        }

        a:hover {
            opacity: 0.8;
        }

        /* Container */
        .container {
            width: 90%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        /* Navbar */
        header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: rgba(15, 23, 42, 0.85);
            backdrop-filter: blur(12px);
            z-index: 1000;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            height: 70px;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: var(--text-color);
        }

        .logo span {
            color: var(--primary-color);
        }

        .nav-links {
            display: flex;
            list-style: none;
            gap: 25px;
            align-items: center;
        }

        .nav-links a {
            color: var(--text-color);
            font-weight: 500;
            font-size: 0.95rem;
        }

        .btn-nav {
            background: var(--primary-color);
            color: white !important;
            padding: 8px 18px;
            border-radius: 6px;
            font-weight: 600;
        }

        /* Hero Section */
        .hero {
            min-height: 100vh;
            display: flex;
            align-items: center;
            padding-top: 80px;
        }

        .hero-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 50px;
            align-items: center;
        }

        .hero-text h1 {
            font-size: 3.5rem;
            line-height: 1.1;
            margin-bottom: 15px;
            font-weight: 800;
        }

        .hero-text h1 span {
            color: var(--primary-color);
        }

        .hero-text h2 {
            font-size: 1.5rem;
            color: #94a3b8;
            margin-bottom: 20px;
            font-weight: 400;
        }

        .hero-text p {
            font-size: 1.1rem;
            color: #cbd5e1;
            margin-bottom: 30px;
        }

        .hero-buttons {
            display: flex;
            gap: 15px;
            margin-bottom: 30px;
        }

        .btn {
            display: inline-block;
            padding: 12px 28px;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            border: none;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .btn-primary {
            background: var(--primary-color);
            color: white;
            box-shadow: 0 4px 14px var(--accent-glow);
        }

        .btn-secondary {
            background: transparent;
            color: var(--text-color);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }

        .btn:hover {
            transform: translateY(-2px);
        }

        .social-links {
            display: flex;
            gap: 15px;
            font-size: 1.3rem;
        }

        .hero-image {
            text-align: center;
            position: relative;
        }

        .hero-image img {
            width: 320px;
            height: 320px;
            border-radius: 50%;
            object-fit: cover;
            border: 4px solid var(--primary-color);
            box-shadow: 0 0 30px var(--accent-glow);
        }

        /* Section Styling */
        section {
            padding: 100px 0;
        }

        .section-title {
            text-align: center;
            margin-bottom: 60px;
        }

        .section-title h2 {
            font-size: 2.2rem;
            margin-bottom: 10px;
        }

        .section-title div {
            width: 60px;
            height: 4px;
            background: var(--primary-color);
            margin: 0 auto;
            border-radius: 2px;
        }

        /* About Grid */
        .about-grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 40px;
        }

        .about-card {
            background: var(--card-color);
            padding: 30px;
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .about-card h3 {
            margin-bottom: 15px;
            color: var(--primary-color);
        }

        /* Skills Bars */
        .skills-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
        }

        .skill-item {
            background: var(--card-color);
            padding: 20px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.05);
        }

        .skill-info {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            font-weight: 600;
        }

        .progress-bar {
            width: 100%;
            height: 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 5px;
            overflow: hidden;
        }

        .progress {
            height: 100%;
            background: var(--primary-color);
            border-radius: 5px;
            transition: width 1s ease-in-out;
        }

        /* Projects Grid */
        .projects-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 30px;
        }

        .project-card {
            background: var(--card-color);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.05);
            transition: transform 0.3s ease;
            cursor: pointer;
        }

        .project-card:hover {
            transform: translateY(-8px);
        }

        .project-img {
            width: 100%;
            height: 200px;
            object-fit: cover;
        }

        .project-body {
            padding: 20px;
        }

        .project-body h3 {
            margin-bottom: 10px;
        }

        .project-body p {
            color: #94a3b8;
            font-size: 0.95rem;
            margin-bottom: 15px;

            /* Line clamp for text preview */
            display: -webkit-box;
            -webkit-line-clamp: 3;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }

        .tech-tags {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 20px;
        }

        .tech-tag {
            background: rgba(99, 102, 241, 0.15);
            color: var(--primary-color);
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .project-links {
            display: flex;
            gap: 15px;
        }

        /* Modal */
        .modal {
            display: none;
            position: fixed;
            top:0; left:0; width:100%; height:100%;
            background: rgba(0,0,0,0.8);
            z-index: 2000;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .modal-content {
            background: var(--card-color);
            max-width: 700px;
            width: 100%;
            border-radius: 12px;
            padding: 30px;
            max-height: 90vh;
            overflow-y: auto;
            position: relative;
        }

        .close-modal {
            position: absolute;
            top: 20px;
            right: 20px;
            font-size: 1.5rem;
            cursor: pointer;
            color: #94a3b8;
        }

        /* Contact Section */
        .contact-content {
            text-align: center;
            max-width: 600px;
            margin: 0 auto;
        }

        .contact-content p {
            margin-bottom: 30px;
            color: #94a3b8;
        }

        /* Footer */
        footer {
            text-align: center;
            padding: 30px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            color: #64748b;
            font-size: 0.9rem;
        }

        /* Admin Dashboard overlay & styles */
        .admin-panel {
            display: {% if show_admin %}block{% else %}none{% endif %};
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: var(--bg-color);
            z-index: 3000;
            overflow-y: auto;
        }

        .admin-header {
            background: var(--card-color);
            padding: 20px 40px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }

        .admin-container {
            display: grid;
            grid-template-columns: 240px 1fr;
            min-height: calc(100vh - 75px);
        }

        .admin-sidebar {
            background: rgba(0, 0, 0, 0.2);
            padding: 20px;
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }

        .admin-sidebar button {
            width: 100%;
            padding: 12px 15px;
            text-align: left;
            background: transparent;
            border: none;
            color: var(--text-color);
            font-weight: 500;
            border-radius: 6px;
            cursor: pointer;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .admin-sidebar button.active, .admin-sidebar button:hover {
            background: var(--primary-color);
            color: white;
        }

        .admin-main {
            padding: 40px;
        }

        .admin-tab {
            display: none;
        }

        .admin-tab.active {
            display: block;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: 500;
            color: #cbd5e1;
        }

        .form-group input, .form-group textarea, .form-group select {
            width: 100%;
            padding: 12px;
            background: rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 6px;
            color: white;
            font-size: 0.95rem;
        }

        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }

        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .data-table th, .data-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }

        .data-table th {
            background: rgba(0,0,0,0.3);
            color: #94a3b8;
        }

        .action-btn {
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            border: none;
            font-size: 0.8rem;
        }

        .btn-delete { background: #ef4444; color: white; }

        @media (max-width: 768px) {
            .hero-content { grid-template-columns: 1fr; text-align: center; }
            .hero-buttons { justify-content: center; }
            .about-grid { grid-template-columns: 1fr; }
            .admin-container { grid-template-columns: 1fr; }
            .admin-sidebar { display: flex; overflow-x: auto; }
        }
    </style>
</head>
<body>

    <!-- NAV -->
    <header>
        <div class="container">
            <nav>
                <div class="logo">{{ profile.name }}<span>.dev</span></div>
                <ul class="nav-links">
                    {% if settings.show_about == 'true' %}<li><a href="#about">About</a></li>{% endif %}
                    {% if settings.show_skills == 'true' %}<li><a href="#skills">Skills</a></li>{% endif %}
                    {% if settings.show_projects == 'true' %}<li><a href="#projects">Projects</a></li>{% endif %}
                    {% if settings.show_contact == 'true' %}<li><a href="#contact">Contact</a></li>{% endif %}
                    {% if logged_in %}
                        <li><a href="#" onclick="openAdmin()" class="btn-nav"><i class="fa-solid fa-gauge"></i> Dashboard</a></li>
                        <li><a href="/logout" style="color: #ef4444;"><i class="fa-solid fa-right-from-bracket"></i></a></li>
                    {% else %}
                        <li><a href="#" onclick="openLoginModal()" class="btn-nav"><i class="fa-solid fa-lock"></i> Dev Access</a></li>
                    {% endif %}
                </ul>
            </nav>
        </div>
    </header>

    <!-- HERO -->
    <section class="hero">
        <div class="container">
            <div class="hero-content">
                <div class="hero-text">
                    <h1>Hi, I'm <span>{{ profile.name }}</span></h1>
                    <h2>{{ profile.title }}</h2>
                    <p>{{ profile.bio }}</p>
                    <div class="hero-buttons">
                        <a href="#projects" class="btn btn-primary">View Projects</a>
                        <a href="#contact" class="btn btn-secondary">Contact Me</a>
                    </div>
                    <div class="social-links">
                        {% if profile.github %}<a href="{{ profile.github }}" target="_blank"><i class="fa-brands fa-github"></i></a>{% endif %}
                        {% if profile.linkedin %}<a href="{{ profile.linkedin }}" target="_blank"><i class="fa-brands fa-linkedin"></i></a>{% endif %}
                        {% if profile.twitter %}<a href="{{ profile.twitter }}" target="_blank"><i class="fa-brands fa-x-twitter"></i></a>{% endif %}
                    </div>
                </div>
                <div class="hero-image">
                    <img src="{{ profile.avatar_url or 'https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80' }}" alt="Profile Avatar">
                </div>
            </div>
        </div>
    </section>

    <!-- ABOUT -->
    {% if settings.show_about == 'true' %}
    <section id="about">
        <div class="container">
            <div class="section-title">
                <h2>About Me</h2>
                <div></div>
            </div>
            <div class="about-grid">
                <div class="about-card">
                    <h3>Biography & Background</h3>
                    <p>{{ profile.about_story }}</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 20px;">
                    <div class="about-card">
                        <h3><i class="fa-solid fa-graduation-cap"></i> Education</h3>
                        <p>{{ profile.education }}</p>
                    </div>
                    <div class="about-card">
                        <h3><i class="fa-solid fa-bullseye"></i> Career Goals</h3>
                        <p>{{ profile.career_goals }}</p>
                    </div>
                </div>
            </div>
        </div>
    </section>
    {% endif %}

    <!-- SKILLS -->
    {% if settings.show_skills == 'true' %}
    <section id="skills">
        <div class="container">
            <div class="section-title">
                <h2>Technical Proficiency</h2>
                <div></div>
            </div>
            <div class="skills-grid">
                {% for skill in skills %}
                <div class="skill-item">
                    <div class="skill-info">
                        <span>{{ skill.name }}</span>
                        <span>{{ skill.proficiency }}%</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress" style="width: {{ skill.proficiency }}%;"></div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}

    <!-- PROJECTS -->
    {% if settings.show_projects == 'true' %}
    <section id="projects">
        <div class="container">
            <div class="section-title">
                <h2>Featured Projects</h2>
                <div></div>
            </div>
            <div class="projects-grid">
                {% for project in projects %}
                <div class="project-card" onclick="openProjectModal({{ project.id }})">
                    <img src="{{ project.image_url }}" class="project-img" alt="{{ project.title }}">
                    <div class="project-body">
                        <h3>{{ project.title }}</h3>
                        <p>{{ project.description }}</p>
                        <div class="tech-tags">
                            {% for tech in project.technologies.split(',') %}
                            <span class="tech-tag">{{ tech.strip() }}</span>
                            {% endfor %}
                        </div>
                        <div class="project-links">
                            {% if project.github_url %}<a href="{{ project.github_url }}" target="_blank" onclick="event.stopPropagation()"><i class="fa-brands fa-github"></i> Code</a>{% endif %}
                            {% if project.demo_url %}<a href="{{ project.demo_url }}" target="_blank" onclick="event.stopPropagation()"><i class="fa-solid fa-arrow-up-right-from-square"></i> Demo</a>{% endif %}
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </section>
    {% endif %}

    <!-- CONTACT -->
    {% if settings.show_contact == 'true' %}
    <section id="contact">
        <div class="container">
            <div class="section-title">
                <h2>Get In Touch</h2>
                <div></div>
            </div>
            <div class="contact-content">
                <p>Have an exciting project, full-time offer, or software opportunity? Let's connect!</p>
                <a href="mailto:{{ profile.email }}" class="btn btn-primary"><i class="fa-solid fa-envelope"></i> Send Email ({{ profile.email }})</a>
            </div>
        </div>
    </section>
    {% endif %}

    <footer>
        <div class="container">
            <p>&copy; 2026 {{ profile.name }}. Built using Flask CMS Architecture.</p>
        </div>
    </footer>

    <!-- MODAL: PROJECT DETAILS -->
    <div id="projectModal" class="modal">
        <div class="modal-content">
            <span class="close-modal" onclick="closeProjectModal()">&times;</span>
            <div id="modalBody"></div>
        </div>
    </div>

    <!-- MODAL: LOGIN -->
    <div id="loginModal" class="modal">
        <div class="modal-content" style="max-width: 400px;">
            <span class="close-modal" onclick="closeLoginModal()">&times;</span>
            <h2 style="margin-bottom: 20px; text-align: center;">Developer Access</h2>
            <form action="/login" method="POST">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width: 100%;">Login to Dashboard</button>
            </form>
        </div>
    </div>

    <!-- ADMIN DASHBOARD PANEL -->
    {% if logged_in %}
    <div id="adminPanel" class="admin-panel">
        <div class="admin-header">
            <h2>⚙️ Developer Dashboard System</h2>
            <div>
                <a href="/" class="btn btn-secondary" style="margin-right: 10px;">View Public Site</a>
                <a href="/logout" class="btn btn-delete">Logout</a>
            </div>
        </div>

        <div class="admin-container">
            <div class="admin-sidebar">
                <button class="active" onclick="showTab('overview')"><i class="fa-solid fa-chart-pie"></i> Overview</button>
                <button onclick="showTab('projects_mgr')"><i class="fa-solid fa-diagram-project"></i> Projects Manager</button>
                <button onclick="showTab('profile_mgr')"><i class="fa-solid fa-user-gear"></i> Profile Manager</button>
                <button onclick="showTab('skills_mgr')"><i class="fa-solid fa-code"></i> Skills Manager</button>
                <button onclick="showTab('appearance_mgr')"><i class="fa-solid fa-paint-roller"></i> Appearance</button>
            </div>

            <div class="admin-main">
                <!-- OVERVIEW TAB -->
                <div id="overview" class="admin-tab active">
                    <h2 style="margin-bottom: 20px;">Welcome Back, {{ profile.name }}</h2>
                    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
                        <div class="about-card">
                            <h3>Total Projects</h3>
                            <p style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">{{ projects|length }}</p>
                        </div>
                        <div class="about-card">
                            <h3>Total Skills</h3>
                            <p style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">{{ skills|length }}</p>
                        </div>
                        <div class="about-card">
                            <h3>System Health</h3>
                            <p style="font-size: 1.2rem; color: #10b981; font-weight: 600;">Active / SQLite DB</p>
                        </div>
                    </div>
                </div>

                <!-- PROJECTS MANAGER -->
                <div id="projects_mgr" class="admin-tab">
                    <h2>Add / Manage Projects</h2>
                    <form action="/api/projects/add" method="POST" style="margin-top: 20px;" class="about-card">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Project Title</label>
                                <input type="text" name="title" required>
                            </div>
                            <div class="form-group">
                                <label>Technologies (comma separated)</label>
                                <input type="text" name="technologies" placeholder="Python, Flask, JavaScript" required>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Short Description</label>
                            <textarea name="description" rows="3" required></textarea>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>GitHub URL</label>
                                <input type="url" name="github_url">
                            </div>
                            <div class="form-group">
                                <label>Live Demo URL</label>
                                <input type="url" name="demo_url">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Image URL</label>
                            <input type="url" name="image_url" placeholder="https://..." required>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Key Challenges</label>
                                <textarea name="challenges" rows="2"></textarea>
                            </div>
                            <div class="form-group">
                                <label>Key Learnings</label>
                                <textarea name="learnings" rows="2"></textarea>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Save Project</button>
                    </form>

                    <h3 style="margin-top: 40px;">Existing Projects</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Tech Stack</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in projects %}
                            <tr>
                                <td>{{ p.title }}</td>
                                <td>{{ p.technologies }}</td>
                                <td>
                                    <form action="/api/projects/delete/{{ p.id }}" method="POST" style="display:inline;">
                                        <button type="submit" class="action-btn btn-delete">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- PROFILE MANAGER -->
                <div id="profile_mgr" class="admin-tab">
                    <h2>Edit Public Profile</h2>
                    <form action="/api/profile/update" method="POST" class="about-card" style="margin-top:20px;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Name</label>
                                <input type="text" name="name" value="{{ profile.name }}">
                            </div>
                            <div class="form-group">
                                <label>Developer Title</label>
                                <input type="text" name="title" value="{{ profile.title }}">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Short Bio</label>
                            <textarea name="bio" rows="2">{{ profile.bio }}</textarea>
                        </div>
                        <div class="form-group">
                            <label>About / Story</label>
                            <textarea name="about_story" rows="4">{{ profile.about_story }}</textarea>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Education</label>
                                <input type="text" name="education" value="{{ profile.education }}">
                            </div>
                            <div class="form-group">
                                <label>Career Goals</label>
                                <input type="text" name="career_goals" value="{{ profile.career_goals }}">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Email</label>
                                <input type="email" name="email" value="{{ profile.email }}">
                            </div>
                            <div class="form-group">
                                <label>Avatar / Profile Image URL</label>
                                <input type="url" name="avatar_url" value="{{ profile.avatar_url }}">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>GitHub URL</label>
                                <input type="url" name="github" value="{{ profile.github }}">
                            </div>
                            <div class="form-group">
                                <label>LinkedIn URL</label>
                                <input type="url" name="linkedin" value="{{ profile.linkedin }}">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Update Profile</button>
                    </form>
                </div>

                <!-- SKILLS MANAGER -->
                <div id="skills_mgr" class="admin-tab">
                    <h2>Manage Technical Skills</h2>
                    <form action="/api/skills/add" method="POST" class="about-card" style="margin-top:20px;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Skill Name</label>
                                <input type="text" name="name" required>
                            </div>
                            <div class="form-group">
                                <label>Category</label>
                                <input type="text" name="category" placeholder="Frontend / Backend / Tools" required>
                            </div>
                            <div class="form-group">
                                <label>Proficiency (%)</label>
                                <input type="number" name="proficiency" min="1" max="100" required>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary">Add Skill</button>
                    </form>

                    <h3 style="margin-top: 40px;">Current Skills</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>Skill</th>
                                <th>Category</th>
                                <th>Level</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for s in skills %}
                            <tr>
                                <td>{{ s.name }}</td>
                                <td>{{ s.category }}</td>
                                <td>{{ s.proficiency }}%</td>
                                <td>
                                    <form action="/api/skills/delete/{{ s.id }}" method="POST" style="display:inline;">
                                        <button type="submit" class="action-btn btn-delete">Delete</button>
                                    </form>
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- APPEARANCE MANAGER -->
                <div id="appearance_mgr" class="admin-tab">
                    <h2>Customization & Styling</h2>
                    <form action="/api/settings/update" method="POST" class="about-card" style="margin-top: 20px;">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Primary Accent Color</label>
                                <input type="color" name="primary_color" value="{{ settings.primary_color }}">
                            </div>
                            <div class="form-group">
                                <label>Background Color</label>
                                <input type="color" name="bg_color" value="{{ settings.bg_color }}">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Card Background Color</label>
                                <input type="color" name="card_color" value="{{ settings.card_color }}">
                            </div>
                            <div class="form-group">
                                <label>Text Color</label>
                                <input type="color" name="text_color" value="{{ settings.text_color }}">
                            </div>
                        </div>

                        <h3 style="margin: 20px 0 10px;">Toggle Sections</h3>
                        <div class="form-group">
                            <label><input type="checkbox" name="show_about" value="true" {% if settings.show_about == 'true' %}checked{% endif %}> Display About Section</label>
                            <label><input type="checkbox" name="show_skills" value="true" {% if settings.show_skills == 'true' %}checked{% endif %}> Display Skills Section</label>
                            <label><input type="checkbox" name="show_projects" value="true" {% if settings.show_projects == 'true' %}checked{% endif %}> Display Projects Section</label>
                            <label><input type="checkbox" name="show_contact" value="true" {% if settings.show_contact == 'true' %}checked{% endif %}> Display Contact Section</label>
                        </div>
                        <button type="submit" class="btn btn-primary">Save Appearance</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- CLIENT JAVASCRIPT -->
    <script>
        const projectsData = {{ projects_json | safe }};

        function openProjectModal(id) {
            const project = projectsData.find(p => p.id === id);
            if(!project) return;

            const body = document.getElementById('modalBody');
            body.innerHTML = `
                <img src="${project.image_url}" style="width:100%; height:250px; object-fit:cover; border-radius:8px; margin-bottom:20px;">
                <h2>${project.title}</h2>
                <p style="color:var(--primary-color); margin-bottom:15px;"><strong>Tech:</strong> ${project.technologies}</p>
                <p style="margin-bottom:20px;">${project.description}</p>
                ${project.challenges ? `<h4>Challenges Handled</h4><p style="color:#94a3b8; margin-bottom:15px;">${project.challenges}</p>` : ''}
                ${project.learnings ? `<h4>Key Insights & Learnings</h4><p style="color:#94a3b8; margin-bottom:20px;">${project.learnings}</p>` : ''}
                <div style="display:flex; gap:15px;">
                    ${project.github_url ? `<a href="${project.github_url}" target="_blank" class="btn btn-primary">GitHub Repository</a>` : ''}
                    ${project.demo_url ? `<a href="${project.demo_url}" target="_blank" class="btn btn-secondary">Live Demo</a>` : ''}
                </div>
            `;
            document.getElementById('projectModal').style.display = 'flex';
        }

        function closeProjectModal() {
            document.getElementById('projectModal').style.display = 'none';
        }

        function openLoginModal() {
            document.getElementById('loginModal').style.display = 'flex';
        }

        function closeLoginModal() {
            document.getElementById('loginModal').style.display = 'none';
        }

        function openAdmin() {
            const adminPanel = document.getElementById('adminPanel');
            if(adminPanel) adminPanel.style.display = 'block';
        }

        function showTab(tabId) {
            document.querySelectorAll('.admin-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.admin-sidebar button').forEach(b => b.classList.remove('active'));
            
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
"""

# ==========================================
# BACKEND CONTROLLERS & API ROUTES
# ==========================================

@app.route('/')
def public_portfolio():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM profile LIMIT 1")
    profile = dict(cursor.fetchone() or {})

    cursor.execute("SELECT * FROM skills")
    skills = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM projects")
    projects = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}

    conn.close()

    import json
    return render_template_string(
        MAIN_TEMPLATE,
        profile=profile,
        skills=skills,
        projects=projects,
        projects_json=json.dumps(projects),
        settings=settings,
        logged_in=session.get('admin_logged_in', False),
        show_admin=session.get('admin_logged_in', False)
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user['password_hash'], password):
        session['admin_logged_in'] = True
    return redirect(url_for('public_portfolio'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('public_portfolio'))

@app.route('/api/projects/add', methods=['POST'])
def add_project():
    if not session.get('admin_logged_in'): return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO projects (title, description, technologies, github_url, demo_url, image_url, challenges, learnings)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form.get('title'),
        request.form.get('description'),
        request.form.get('technologies'),
        request.form.get('github_url'),
        request.form.get('demo_url'),
        request.form.get('image_url'),
        request.form.get('challenges'),
        request.form.get('learnings')
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('public_portfolio'))

@app.route('/api/projects/delete/<int:project_id>', methods=['POST'])
def delete_project(project_id):
    if not session.get('admin_logged_in'): return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('public_portfolio'))

@app.route('/api/skills/add', methods=['POST'])
def add_skill():
    if not session.get('admin_logged_in'): return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO skills (name, category, proficiency) VALUES (?, ?, ?)",
                   (request.form.get('name'), request.form.get('category'), request.form.get('proficiency')))
    conn.commit()
    conn.close()
    return redirect(url_for('public_portfolio'))

@app.route('/api/skills/delete/<int:skill_id>', methods=['POST'])
def delete_skill(skill_id):
    if not session.get('admin_logged_in'): return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('public_portfolio'))

@app.route('/api/profile/update', methods=['POST'])
def update_profile():
    if not session.get('admin_logged_in'): return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE profile SET name=?, title=?, bio=?, about_story=?, education=?, career_goals=?, email=?, avatar_url=?, github=?, linkedin=? WHERE id=1
    ''', (
        request.form.get('name'),
        request.form.get('title'),
        request.form.get('bio'),
        request.form.get('about_story'),
        request.form.get('education'),
        request.form.get('career_goals'),
        request.form.get('email'),
        request.form.get('avatar_url'),
        request.form.get('github'),
        request.form.get('linkedin')
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('public_portfolio'))

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    if not session.get('admin_logged_in'): return redirect('/')
    
    conn = get_db()
    cursor = conn.cursor()
    
    settings_data = {
        'primary_color': request.form.get('primary_color'),
        'bg_color': request.form.get('bg_color'),
        'card_color': request.form.get('card_color'),
        'text_color': request.form.get('text_color'),
        'show_about': 'true' if request.form.get('show_about') else 'false',
        'show_skills': 'true' if request.form.get('show_skills') else 'false',
        'show_projects': 'true' if request.form.get('show_projects') else 'false',
        'show_contact': 'true' if request.form.get('show_contact') else 'false',
    }

    for key, value in settings_data.items():
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    conn.close()
    return redirect(url_for('public_portfolio'))

# ==========================================
# APPLICATION LAUNCHER
# ==========================================

# Runs on import so gunicorn (Render) also creates/seeds the tables
init_db()

if __name__ == '__main__':
    print("\n🚀 Starting Portfolio CMS Server...")
    print("👉 Public Site: http://127.0.0.1:5000/")
    print("🔑 Admin Username: admin")
    print("🔑 Admin Password: password123\n")
    app.run(debug=True, port=5000)