from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    public_key = models.TextField()
    private_key = models.TextField()

class ChatRoom(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)  # Fixed the room field
    content = models.TextField()
    timestamp = models.DateTimeField()  # We set this earlier to allow manual timestamps

    def __str__(self):
        return f'{self.user.username}: {self.content} ({self.timestamp})'