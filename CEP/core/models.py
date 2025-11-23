from django.db import models

class Subscription(models.Model):
    email = models.EmailField()
    city = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('email', 'city')

    def __str__(self):
        return f"{self.email} - {self.city}"
