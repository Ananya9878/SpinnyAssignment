from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Box(models.Model):
    length = models.IntegerField(default=0)
    width = models.IntegerField(default=0)
    height = models.IntegerField(default=0)
    area = models.IntegerField(default=0)
    volume = models.IntegerField(default=0)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def get_area(self):
        return 2 * ((self.length * self.width) + (self.length * self.height) + (self.width * self.height))

    def get_volume(self):
        return (self.length * self.width * self.height)

    def save(self, *args, **kwargs):
        self.area = self.get_area()
        self.volume = self.get_volume()
        super().save(*args, **kwargs)


