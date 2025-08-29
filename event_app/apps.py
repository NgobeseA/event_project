from django.apps import AppConfig
from django import forms


class EventAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'event_app'

from flask import Flask, render_template, request, redirect

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def submit_ticket():
    if request.method == 'POST':
        title = request.form.get('title')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        message = request.form.get('message')

        # For demonstration, just print to console
        print(f"Title: {title}")
        print(f"Name: {first_name} {last_name}")
        print(f"Email: {email}")
        print(f"Message: {message}")

        return redirect('/success')

    return render_template('form.html')

@app.route('/success')
def success():
    return "<h2>Thank you! Your message has been received.</h2>"

if __name__ == '__main__':
    app.run(debug=True)
