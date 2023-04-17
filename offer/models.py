from datetime import datetime

from django.db import models


def parseDateTime(date_time_str):
    return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=256)
    user_rating = models.FloatField()
    user_watchlist = models.ManyToManyField('Offer', related_name="watchlist")
    user_channel_name = models.CharField(max_length=256, default='nc')

    class Meta:
        db_table = 'user'


class Currency(models.Model):
    currency_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=256)
    capital_name = models.CharField(max_length=256)
    unicode_symbol = models.CharField(max_length=256)
    color_hex = models.CharField(max_length=256)

    class Meta:
        db_table = 'currency'


class Offer(models.Model):
    offer_id = models.AutoField(primary_key=True)
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="from_currency")
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="to_currency")
    from_amount = models.FloatField()
    to_amount = models.FloatField()
    exchange_rate = models.FloatField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'offer'


class Session(models.Model):
    session_id = models.AutoField(primary_key=True)
    session_state = models.IntegerField(default=1)
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE)
    session_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    last_message_date = models.DateTimeField(default=parseDateTime('1000-12-31 23:59:00'))

    class Meta:
        db_table = 'session'


class SessionUser(models.Model):
    session_user_id = models.AutoField(primary_key=True)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'user_session'


class Messages(models.Model):
    message_id = models.AutoField(primary_key=True)
    message_sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message_date = models.DateTimeField()
    message_session = models.ForeignKey(Session, on_delete=models.CASCADE)
    message_text = models.CharField(max_length=1024)

    class Meta:
        db_table = 'message'


class UserRating(models.Model):
    user_rating_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.FloatField()

    class Meta:
        db_table = 'user_rating'
