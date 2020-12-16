from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.forms import LoginForm, RegistrationForm, JoinRoomForm, CreateRoomForm, EditProfileForm
from app.models import User, Room
from app.engine import process_matches

import dload


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    create = CreateRoomForm()
    join   = JoinRoomForm()
    if join.identifier.data == 'joinf' and join.validate_on_submit():
        room_id = join.room_id.data
        room = Room.query.filter_by(id=room_id).first()
        if room is None or room.active_users == 10:
            flash('Unfortunately, this room is full or does not exist.')
            return redirect(url_for('join'))
        if current_user.preferences is None:
            # TODO: redirect to appropriate page instead?
            flash('Please set your preferences before joining a room!')
            return redirect(url_for('edit_profile'))
        room.add_user(current_user)
        if room.active_users == 10:
            # Start the matching process
            users = User.query.filter_by(room_id=id).all()
            team_1, team_2, score = process_matches(users)
            db.session.delete(room)
            for user in users:
                user.room_id = None
            db.session.commit()
            return render_template('completed_match.html', team_1=team_1, team_2=team_2, score=score)
        return redirect(url_for('room', id=room_id))

    if create.identifier.data == 'createf' and create.validate_on_submit():
        room_id = create.room_id.data
        room = Room.query.filter_by(id=room_id).first()
        if room is not None:
            # TODO: handle join more gracefully??
            flash('Unfortunately, this room exists. Please join it instead.')
            return redirect(url_for('join'))
        if current_user.preferences is None:
            flash('Please set your preferences before joining a room!')
            return redirect(url_for('edit_profile'))
        current_user.room_id = room_id
        room = Room(id=room_id, active_users=1)
        db.session.add(room)
        db.session.commit()
        return redirect(url_for('room', id=room_id))

    return render_template('join.html', join_form=join, create_form=create)

@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    url_base = 'https://na.whatismymmr.com/api/v1/summoner?name='
    url = url_base + "+".join(username.split())
    res = dload.json(url)
    if not res["normal"]["warn"]:
        mmr = res["normal"]["avg"]
    elif not res["ranked"]["warn"]:
        mmr = res["ranked"]["avg"]
    else:
        mmr = 1100
    return render_template('user.html', user=user, mmr=mmr)

@app.route('/room/<id>')
@login_required
def room(id):
    room  = Room.query.filter_by(id=id).first_or_404()
    users = User.query.filter_by(room_id=id).all()
    return render_template('room.html', room=room, users=users)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.preferences = form.preferences.data
        print(current_user.preferences)
        print(form.preferences.data)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    return render_template('edit_profile.html', title='Edit Profile', form=form)
