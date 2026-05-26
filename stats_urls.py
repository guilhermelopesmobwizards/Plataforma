from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender="core.ExchangeRate")
def exchange_rate_saved(sender, instance, **kwargs):
    from core.tasks import apply_exchange_rates_to_metrics
    apply_exchange_rates_to_metrics.delay(year=instance.year, month=instance.month)
