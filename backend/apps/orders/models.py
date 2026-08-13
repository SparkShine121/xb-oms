from django.db import models

class ExchangeRate(models.Model):
    currency_pair = models.CharField(max_length=16, default='USD/CNY')
    rate = models.DecimalField(max_digits=10, decimal_places=4)
    effective_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-effective_date', '-id']

    @classmethod
    def get_effective_rate(cls, date):
        qs = cls.objects.filter(effective_date__lte=date).order_by('-effective_date', '-id')
        return qs.first() if qs.exists() else None