from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "abcd"
socketio = SocketIO(app)

active_rooms = {}

def generate_code(length:int):
    while True:
        code = ''
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in active_rooms: break
    return code


@app.route('/', methods = ["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)

        if not name:
            return render_template('home.html', error = "Name cannot be empty DUMBO!", name = name, code = code)
        if join!=False and not code:
            return render_template('home.html', error = "How are you planning to join a room without entering a code?!!", name = name, code = code)
        
        room = code
        if create!=False:
            room = generate_code(6)
            active_rooms[room] = {"members":0, "messages":[]}
        elif room not in active_rooms:
            
            return render_template('home.html', error = "Imagine being so idiotic that you can't even enter a valid code.", name = name, code = code)
        print(active_rooms)
        session["room"] = room
        session['name'] = name

        return redirect(url_for("room"))

    return render_template('home.html')

@app.route('/room')
def room():
    room = session.get('room')
    if room is None or session.get('name') is None or room not in active_rooms:
        return redirect(url_for('home'))
    return render_template('room.html', code=room, messages = active_rooms[room]['messages'])

@socketio.on("message-send")
def message_send(data):
    room = session.get("room")
    name = session.get("name")
    if room not in active_rooms:return
    content = {"name":name, "message":data['data']}
    send(content, to=room)
    active_rooms[room]['messages'].append(content)
    print(f"{name}: {data['data']}")


@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name: return
    if room not in active_rooms:
        leave_room(room)
        return
    join_room(room)
    send({"name":name, "message":"has entered the room. Say hello!"}, to=room)
    active_rooms[room]["members"]+=1
    print(f"{name} joined {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    if room in active_rooms:
        active_rooms[room]["members"]-=1
        if active_rooms[room]["members"]<=0:
            del active_rooms[room]
    send({"name":name, "message":"has left the room :( Hope they come back soon."}, to=room)
    print(f"{name} left {room}")



if __name__ == "__main__":
    socketio.run(app, debug=False)