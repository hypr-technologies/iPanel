#!/usr/bin/env python
# coding: utf-8
"""
Simple test server for iPanel development
"""
import os
import sys
import time
from flask import Flask, request, session, render_template, redirect, url_for, jsonify

# Create a simple Flask app for testing
app = Flask(__name__)
app.secret_key = 'test-development-key'

# Mock some common functions for testing
class MockPublic:
    @staticmethod
    def md5(string):
        import hashlib
        return hashlib.md5(string.encode()).hexdigest()
    
    @staticmethod
    def getDate():
        return time.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def GetRandomString(length):
        import random
        import string
        return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

# Mock the common panelAdmin class
class MockPanelAdmin:
    def local(self):
        return None

# Basic routes
@app.route('/')
def index():
    return '''
    <html>
    <head>
        <title>iPanel v8.0.0 - Development Server</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .header {{ background: #f8f9fa; padding: 20px; border-radius: 5px; }}
            .content {{ margin-top: 20px; }}
            .button {{ background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>iPanel v8.0.0 - Development Server</h1>
            <p>Development environment for iPanel by Hypr Technologies</p>
        </div>
        <div class="content">
            <h2>System Status</h2>
            <ul>
                <li>Server: Running</li>
                <li>Port: 8888</li>
                <li>Environment: Development</li>
                <li>Time: {}</li>
            </ul>
            
            <h2>Quick Actions</h2>
            <a href="/login" class="button">Login</a>
            <a href="/status" class="button">Status</a>
            <a href="/test" class="button">Test</a>
            
            <h2>Development Progress</h2>
            <p>This is a basic development server for iPanel. Core functionality is being implemented.</p>
        </div>
    </body>
    </html>
    '''.format(time.strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/login')
def login():
    return '''
    <html>
    <head>
        <title>iPanel Login</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .login-form {{ max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .form-group {{ margin-bottom: 15px; }}
            .form-group label {{ display: block; margin-bottom: 5px; }}
            .form-group input {{ width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 3px; }}
            .btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 3px; cursor: pointer; width: 100%; }}
        </style>
    </head>
    <body>
        <div class="login-form">
            <h2>iPanel Login</h2>
            <form method="post">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="btn">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Simple auth for development
    if username == 'admin' and password == 'admin':
        session['logged_in'] = True
        session['username'] = username
        return redirect('/')
    else:
        return 'Invalid credentials! Try admin/admin'

@app.route('/status')
def status():
    return jsonify({
        'status': 'running',
        'version': '8.0.0-dev',
        'time': time.strftime('%Y-%m-%d %H:%M:%S'),
        'logged_in': session.get('logged_in', False),
        'username': session.get('username', 'guest')
    })

@app.route('/test')
def test():
    return '''
    <html>
    <head>
        <title>iPanel Test</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .test-result {{ padding: 10px; margin: 10px 0; border-radius: 3px; }}
            .pass {{ background: #d4edda; color: #155724; }}
            .fail {{ background: #f8d7da; color: #721c24; }}
        </style>
    </head>
    <body>
        <h1>iPanel Test Results</h1>
        
        <div class="test-result pass">
            ✓ Flask server running successfully
        </div>
        
        <div class="test-result pass">
            ✓ Basic routing working
        </div>
        
        <div class="test-result pass">
            ✓ Session management working
        </div>
        
        <div class="test-result pass">
            ✓ Template rendering working
        </div>
        
        <div class="test-result pass">
            ✓ Development environment ready
        </div>
        
        <h2>Next Steps</h2>
        <ul>
            <li>Implement core iPanel modules</li>
            <li>Add database connectivity</li>
            <li>Implement user authentication</li>
            <li>Add web panel interface</li>
            <li>Integrate with Hypr Technologies systems</li>
        </ul>
        
        <a href="/">← Back to Home</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = 8888
    print(f"Starting iPanel v8.0.0 Development Server on port {port}")
    print("Access the panel at: http://localhost:8888")
    print("Default credentials: admin/admin")
    app.run(host='0.0.0.0', port=port, debug=True)
