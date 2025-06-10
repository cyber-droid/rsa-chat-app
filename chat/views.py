from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import User, ChatRoom, Message

def index(request):
    if request.user.is_authenticated:
        return render(request, 'chat/index.html', {'user': request.user})
    return render(request, 'chat/index.html')

def login_user(request, username):
    user = User.objects.get(username=username)
    login(request, user)
    return redirect('room', room_name='general')

def logout_user(request):
    logout(request)
    return redirect('index')

@login_required
def room(request, room_name):
    # Fetch the chat room and its messages
    room, created = ChatRoom.objects.get_or_create(name=room_name)
    messages = Message.objects.filter(room=room).order_by('timestamp')
    
    # Prepare messages for display (we'll decrypt on the client side)
    message_history = []
    for message in messages:
        # Ensure timestamp is a string; handle potential None values
        timestamp_str = message.timestamp.strftime('%Y-%m-%d %H:%M:%S') if message.timestamp else ''
        message_history.append({
            'username': message.user.username if message.user else '',
            'content': message.content if message.content else '',
            'timestamp': timestamp_str
        })
    welcome_message = f"Welcome, {request.user.username}!"
    return render(request, 'chat/room.html', {
        'room_name': room_name,
        'message_history': message_history, # Pass the message history to the template
        'welcome_message': welcome_message,
    })