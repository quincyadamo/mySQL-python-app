import re
from datetime import datetime
from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnection
from flask_bcrypt import Bcrypt

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
app = Flask(__name__)
app.secret_key = 'secretKey'
mysql = MySQLConnection(app, 'wall')
bcrypt = Bcrypt(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/check', methods=['POST'])
def check():
    #Registering:
    if 'reg_submit' in request.form:
        # print request.form
        # first name: letters only, at least 2 characters, was submitted
        if len(request.form['reg_first_name']) < 2:
            flash('First name must include at least two characters.', 'reg')
        if not request.form['reg_first_name'].isalpha():
            flash('First name may only include alphabetic characters.', 'reg')

        # last name: letters only, at least 2 characters, was submitted
        if len(request.form['reg_last_name']) < 2:
            flash('Last name must include at least two characters.', 'reg')
        if not request.form['reg_last_name'].isalpha():
            flash('Last name may only include alphabetic characters.', 'reg')

        # email: valid format, was submitted
        email_query = (
            'SELECT COUNT(id) AS count FROM users WHERE users.email = :email_field LIMIT 1'
        )
        email_data = {
            'email_field': request.form['reg_email'].lower()
        }
        email_count = mysql.query_db(email_query, email_data)
        if int(email_count[0]['count']) > 0:
            flash('An account already exists with that email address.', 'reg')
        if not EMAIL_REGEX.match(request.form['reg_email']):
            flash('Please provide a valid email.', 'reg')

        # password: minimum 8 characters, submitted, NOT "password"
        if len(request.form['reg_password']) < 8:
            flash('Password must include no fewer than eight characters.', 'reg')
        if request.form['reg_password'].upper == 'PASSWORD':
            flash('Never, ever, ever, ever use "password" as your password.', 'reg')

        # password confirmation: matches password
        if not request.form['reg_confirm'] == request.form['reg_password']:
            flash('Password confirmation does not match password.', 'reg')

        # if valid: hashes+salts password using bcrypt
        if not '_flashes' in session:
            query = ("INSERT INTO users (first_name, last_name, email, " +
                     "password, created_at, updated_at) VALUES " +
                     "(:first_name, :last_name, :email, :password, NOW(), NOW())")
            data = {
                'first_name': request.form['reg_first_name'],
                'last_name': request.form['reg_last_name'],
                'email': request.form['reg_email'].lower(),
                'password': bcrypt.generate_password_hash(request.form['reg_password'])
                }
            session['user_id'] = mysql.query_db(query, data)
            session['user_first_name'] = request.form['reg_first_name']
            return redirect('/wall')

        # if logging in:
    elif 'log_submit' in request.form:
        # print request.form
        query = ('SELECT * FROM users WHERE users.email = ' +
                 ':log_email LIMIT 1')
        data = {
            'log_email' : request.form['log_email'].lower()
        }
        print request.form['log_email'].lower()
        grab_hash = mysql.query_db(query, data)
        print grab_hash
        if (
                grab_hash and
                bcrypt.check_password_hash(grab_hash[0]['password'],
                                           request.form['log_password'])
        ):
            print 'ok'
            session['user_id'] = grab_hash[0]['id']
            session['user_first_name'] = grab_hash[0]['first_name']
            return redirect('/wall')
        else:
            print 'what?'
            flash('Invalid login attempt.', 'log')
    return redirect('/')

@app.route('/wall')
def wall():
    # print 'you know nothing john snow'
    # LOGIC TO GRAB ALL MESSAGES:
    query = (
        'SELECT messages.id, messages.user_id, messages.created_at, ' +
        'messages.message, users.first_name, users.last_name, ' +
        'DATE_FORMAT(messages.created_at, "%M %D %Y") AS display_date FROM ' +
        'messages JOIN users ON messages.user_id = users.id ORDER BY ' +
        'messages.created_at DESC'
    )
    all_messages = mysql.query_db(query)
    # print all_messages
    # LOGIC TO GRAB ALL COMMENTS:
    query2 = (
        'SELECT comments.id, comments.user_id, comments.created_at, ' +
        'comments.comment, comments.message_id, users.first_name, ' +
        'users.last_name, DATE_FORMAT(comments.created_at, "%b %D %Y") AS ' +
        'cdisplay_date FROM comments JOIN users ON comments.user_id = ' +
        'users.id ORDER BY comments.created_at ASC'
    )
    all_comments = mysql.query_db(query2)
    # LOGIC FOR GRABBING THINGS FROM SESSION:
    first_name = session['user_first_name']
    suser_id = session['user_id']
    # LOGIC FOR CHECKING WHETHER DELETE BUTTON SHOULD SHOW:
    # 1800 seconds in a half hour
    for each in all_messages:
        deletable = False
        time_since_creation = datetime.utcnow() - each['created_at']
        if time_since_creation.total_seconds() < 1800:
            deletable = True
        else:
            deletable = False
        each['deletable'] = deletable
    return render_template(
        'wall.html', all_messages=all_messages,
        first_name=first_name, suser_id=suser_id, all_comments=all_comments
        )

@app.route('/logoff')
def logoff():
    session.clear()
    return render_template('loggedoff.html')

@app.route('/post_message', methods=['POST'])
def post_messsage():
    query = (
        'INSERT INTO messages (user_id, message, created_at, updated_at)' +
        'VALUES (:user_id, :message, :message_time, :message_time)'
    )
    data = {
        'user_id': session['user_id'],
        'message': request.form['message_box'],
        'message_time': datetime.utcnow()
    }
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/post_comment', methods=['POST'])
def post_comment():
    query = (
        'INSERT INTO comments(user_id, comment, message_id, created_at, ' +
        'updated_at) VALUES (:user_id, :comment, :message_id, :comment_time, ' +
        ':comment_time)'
    )
    data = {
        'user_id': session['user_id'],
        'comment': request.form['comment_box'],
        'message_id': request.form['post_comment_button'],
        'comment_time': datetime.utcnow()
    }
    mysql.query_db(query, data)
    return redirect('/wall')

@app.route('/delete_message', methods=['POST'])
def delete_message():
    # flash if not (add html to wall for this)
    query = (
        'SELECT messages.created_at FROM messages WHERE messages.id = ' +
        ':message_id LIMIT 1'
    )
    data = {
        'message_id': request.form['delete_message_button']
    }
    check_message_time = mysql.query_db(query, data)
    # print check_message_time
    time_since_creation = (
        datetime.utcnow() - check_message_time[0]['created_at']
    )

    if time_since_creation.total_seconds() < 1800:
        query2 = (
            'DELETE FROM comments WHERE comments.message_id = :message_id'
        )
        data2 = {
            'message_id': request.form['delete_message_button']
        }
        mysql.query_db(query2, data2)
        query3 = (
            'DELETE FROM messages WHERE messages.id = :message_id'
        )
        data3 = {
            'message_id': request.form['delete_message_button']
        }
        mysql.query_db(query3, data3)
    else:
        flash('Message may no longer be deleted after 30 minutes.', 'del')
    return redirect('/wall')

app.run(debug=True)
