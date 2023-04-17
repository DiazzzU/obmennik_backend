import pytz

from datetime import datetime

from rest_framework import viewsets
from rest_framework.exceptions import ValidationError, PermissionDenied

from offer.models import User, Currency, Offer, Session, SessionUser, Messages, UserRating
from rest_framework.response import Response
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def MessageModelToMessageData(message: Messages):
    return {
        'messageId': message.message_id,
        'messageDate': message.message_date.strftime('%Y-%m-%d %H:%M:%S'),
        'messageText': message.message_text,
        'messageSender': UserModelToUserData(message.message_sender),
        'messageSessionId': message.message_session.session_id
    }


def SessionModelToSessionData(session: Session, currentUser: User):
    users = getUsersBySession(session=session)

    users_data = []
    for user in users:
        if user.user_id != currentUser.user_id:
            users_data.append(UserModelToUserData(user))

    session_type = 'incoming'
    if session.session_owner.user_id == currentUser.user_id:
        session_type = 'outcoming'

    messages = Messages.objects.order_by('message_date').filter(message_session_id=session.session_id)
    messages_data = []

    for message in messages:
        messages_data.append(MessageModelToMessageData(message))

    return {
        'sessionId': session.session_id,
        'sessionUsers': users_data,
        'sessionType': session_type,
        'sessionState': session.session_state,
        'sessionOffer': OfferModelToOfferData(session.offer, currentUser),
        'sessionMessages': messages_data,
        'sessionLastMessage': session.last_message_date.strftime('%Y-%m-%d %H:%M:%S')
    }


def UserModelToUserData(user):
    return {
        'user_id': user.user_id,
        'user_name': user.user_name,
        'user_rating': user.user_rating,
        'closed_sessions': len(SessionUser.objects.filter(user_id=user.user_id, session__session_state=0))
    }


def OfferModelToOfferData(offer, user):
    return {
        'offerId': offer.offer_id,
        'fromCurrencyId': offer.from_currency.currency_id,
        'toCurrencyId': offer.to_currency.currency_id,
        'fromAmount': offer.from_amount,
        'toAmount': offer.to_amount,
        'exchangeRate': offer.exchange_rate,
        'creator': UserModelToUserData(offer.user),
        'isOnWatchlist': offer in user.user_watchlist.all()
    }


def CurrencyModelToCurrencyData(currency):
    return {
        "currencyId": currency.currency_id,
        "currencyName": currency.name,
        "currencyCapitalName": currency.capital_name,
        "unicodeSymbol": currency.unicode_symbol,
        "colorHex": currency.color_hex
    }


def parseDateTime(date_time_str):
    return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')


def getUsersBySession(session: Session):
    user_sessions = SessionUser.objects.filter(session=session)
    users = []
    for userSession in user_sessions:
        users.append(userSession.user)
    return users


def getUserSessions(user: User):
    user_sessions = SessionUser.objects.filter(user=user)
    session = []
    for userSession in user_sessions:
        session.append(userSession.session)
    return session


class UserViewSet(viewsets.ViewSet):
    def create_user(self, request):
        user = User(user_name="New user", user_rating=0)
        user.save()
        user.user_name += " " + str(user.user_id)
        user.save()
        return Response(UserModelToUserData(user), status=200)

    def get_user_watchlist(self, request):
        user_id = request.GET.get('userId', None)
        if user_id is None:
            raise ValidationError("user_id does not exist")
        watchlist = User.objects.get(user_id=user_id).user_watchlist.all()
        response_data = []
        for offer in watchlist:
            response_data.append(OfferModelToOfferData(offer, User.objects.get(user_id=user_id)))
        return Response(response_data, status=200)

    def add_watchlist(self, request):
        user_id = request.GET.get('userId', None)
        offer_id = request.GET.get('offerId', None)
        if None in (user_id, offer_id):
            raise ValidationError('Some field(s) does not exist')
        user = User.objects.get(user_id=user_id)

        if user.user_watchlist.filter(offer_id=offer_id):
            raise PermissionDenied("This offer is already in watchlist")

        user.user_watchlist.add(Offer.objects.get(offer_id=offer_id))
        return Response("Offer successfully added to watchlist", status=200)

    def remove_watchlist(self, request):
        user_id = request.GET.get('userId', None)
        offer_id = request.GET.get('offerId', None)
        if None in (user_id, offer_id):
            raise ValidationError('Some field(s) does not exist')
        user = User.objects.get(user_id=user_id)

        if not user.user_watchlist.filter(offer_id=offer_id):
            raise PermissionDenied("This offer is not in watchlist")

        user.user_watchlist.remove(Offer.objects.get(offer_id=offer_id))
        return Response("Offer successfully removed from watchlist", status=200)

    def get_user_offers(self, request):
        user_id = request.GET.get('userId', None)
        if user_id is None:
            raise ValidationError("user_id does not exist")
        offers = Offer.objects.filter(user__user_id=user_id)
        data = []
        for offer in offers:
            data.append(OfferModelToOfferData(offer, User.objects.get(user_id=user_id)))
        return Response(data, status=200)

    def rename(self, request):
        user_id = request.GET.get('userId', None)
        new_name = request.GET.get('newName', None)

        if None in (user_id, new_name):
            raise ValidationError('Some field(s) does not exist')

        user = User.objects.get(user_id=user_id)
        user.user_name = new_name
        user.save()
        return Response(UserModelToUserData(user), status=200)

    def info(self, request):
        user_id = request.GET.get('userId', None)

        if user_id is None:
            raise ValidationError('Some field(s) does not exist')

        user = User.objects.get(user_id=user_id)

        return Response(UserModelToUserData(user), status=200)

    def update_rating(self, request):
        user_id = request.GET.get('userId', None)
        new_rating = request.GET.get('newRating', None)

        if None in (user_id, new_rating):
            raise ValidationError('Some field(s) does not exist')

        user_rating = UserRating.objects.create(user_id=user_id, rating=new_rating)
        user_rating.save()

        user_ratings = UserRating.objects.filter(user_id=user_id)

        sum = 0
        for rating in user_ratings:
            sum += rating.rating

        user = user_rating.user
        user.user_rating = sum / len(user_ratings)
        user.save()

        return Response("Rating successfully updated")



class OfferViewSet(viewsets.ViewSet):
    def get_all_offers(self, request):
        user_id = request.GET.get('userId', None)
        offers = Offer.objects.all()
        data = []
        for offer in offers:
            data.append(OfferModelToOfferData(offer, User.objects.get(user_id=user_id)))
        return Response(data, status=200)

    def create_offer(self, request):
        creator_id = request.data.get('creatorId', None)
        from_currency_id = request.data.get('fromCurrencyId', None)
        to_currency_id = request.data.get('toCurrencyId', None)
        from_amount = request.data.get('fromAmount', None)
        to_amount = request.data.get('toAmount', None)
        exchange_rate = request.data.get('exchangeRate', None)

        if None in (creator_id, from_amount, from_currency_id, to_currency_id, to_amount, exchange_rate):
            raise ValidationError("Some field(s) does not exist")

        offer = Offer.objects.create(from_currency_id=from_currency_id, to_currency_id=to_currency_id,
                                     from_amount=from_amount, to_amount=to_amount,
                                     user_id=creator_id, exchange_rate=exchange_rate)
        offer.save()
        return Response(OfferModelToOfferData(offer, User.objects.get(user_id=creator_id)), status=200)

    def edit_offer(self, request):
        offer_id = request.data.get('offerId', None)
        creator_id = request.data.get('creatorId', None)
        from_currency_id = request.data.get('fromCurrencyId', None)
        to_currency_id = request.data.get('toCurrencyId', None)
        from_amount = request.data.get('fromAmount', None)
        to_amount = request.data.get('toAmount', None)
        exchange_rate = request.data.get('exchangeRate', None)

        user = User.objects.get(user_id=creator_id)

        if None in (offer_id, creator_id, from_amount, from_currency_id, to_currency_id, to_amount, exchange_rate):
            raise ValidationError("Some field(s) does not exist")

        offer = Offer.objects.get(offer_id=offer_id)
        offer.user = User.objects.get(user_id=creator_id)
        offer.from_currency = Currency.objects.get(currency_id=from_currency_id)
        offer.to_currency = Currency.objects.get(currency_id=to_currency_id)
        offer.from_amount = from_amount
        offer.to_amount = to_amount
        offer.exchange_rate = exchange_rate
        offer.save()

        return Response(OfferModelToOfferData(offer, user), status=200)


class SessionViewSet(viewsets.ViewSet):
    channel_layer = get_channel_layer()

    def get_list(self, request):
        user_id = request.GET.get('userId', None)

        if user_id is None:
            raise ValidationError("Some field(s) does not exist")

        user = User.objects.get(user_id=user_id)
        sessions = getUserSessions(user=user)

        sessions_data = []
        for session in sessions:
            sessions_data.append(SessionModelToSessionData(session, user))
        return Response(sessions_data, status=200)

    def send_message_not(self, data):
        sender_id = data.get('senderId', None)
        session_id = data.get('sessionId', None)
        message_date = data.get('messageDate', None)
        message_text = data.get('messageText', None)

        if None in [sender_id, session_id, message_date, message_text]:
            raise ValidationError("Some field(s) does not exist")

        session = Session.objects.get(session_id=session_id)

        message = Messages.objects.create(message_sender_id=sender_id, message_date=parseDateTime(message_date),
                                          message_session_id=session_id, message_text=message_text)
        message.save()

        print(type(session.last_message_date))
        print(type(message.message_date))

        utc = pytz.UTC

        if session.last_message_date.replace(tzinfo=utc) < message.message_date.replace(tzinfo=utc):
            session.last_message_date = message.message_date
            session.save()

        users = getUsersBySession(session)
        for user in users:
            if user.user_channel_name != 'nc':
                async_to_sync(self.channel_layer.send)(
                    user.user_channel_name,
                    {
                        'type': 'send_message',
                        'message': MessageModelToMessageData(message)
                    }
                )


    def send_message(self, request):
        self.send_message_not(request.data)
        return Response("Message successfully sent", status=200)

    def create_session(self, request):
        owner_id = request.data.get('ownerId', None)
        user_ids = request.data.get('userIds', None)
        offer_id = request.data.get('offerId', None)

        if None in [owner_id, user_ids, offer_id]:
            raise ValidationError("Some field(s) does not exist")

        session = Session.objects.create(session_owner_id=owner_id, offer_id=offer_id)
        session.save()

        for user_id in user_ids:
            session_user = SessionUser.objects.create(session_id=session.session_id, user_id=user_id)
            session_user.save()

        for user_id in user_ids:
            user = User.objects.get(user_id=user_id)
            if user.user_channel_name != 'nc':
                async_to_sync(self.channel_layer.send)(
                    user.user_channel_name,
                    {
                        'type': 'create_session',
                        'session': SessionModelToSessionData(session=session, currentUser=user)
                    }
                )

        data = request.data['initialMessage']
        data['sessionId'] = session.session_id

        self.send_message_not(data)

        return Response("Session successfully created", status=200)

    def close(self, request):
        session_id = request.GET.get('sessionId', None)

        if session_id is None:
            raise ValidationError("Some field(s) does not exist")

        session = Session.objects.get(session_id=session_id)

        if session.session_state == 0:
            return Response("Session already closed", status=200)

        session.session_state = 0
        session.save()

        print("Send")

        users = getUsersBySession(session)
        for user in users:
            if user.user_channel_name != 'nc':
                async_to_sync(self.channel_layer.send)(
                    user.user_channel_name,
                    {
                        'type': 'close_session',
                        'session': SessionModelToSessionData(session=session, currentUser=user)
                    }
                )

        return Response("Session closed", status=200)


class CurrencyViewSet(viewsets.ViewSet):
    def get_list_currencies(self, request):
        currenciesQuerySet = Currency.objects.all()
        currencies = []
        for currency in currenciesQuerySet:
            currencies.append(CurrencyModelToCurrencyData(currency))
        return Response(currencies, status=200)

    def add_currency(self, request):
        data = request.data.get('data', None)
        if data is None:
            raise ValidationError("data does not exist")

        response_data = []
        for currencyData in data:
            name = currencyData.get('name', None)
            capital_name = currencyData.get('capitalName', None)
            unicode_symbol = currencyData.get('unicodeSymbol', None)
            color_hex = currencyData.get('colorHex', None)

            if None in (name, capital_name, unicode_symbol, color_hex):
                raise ValidationError("Some field(s) does not exist")

            currency = Currency.objects.create(name=name, capital_name=capital_name,
                                               unicode_symbol=unicode_symbol, color_hex=color_hex)
            currency.save()
            response_data.append(CurrencyModelToCurrencyData(currency))

        return Response(response_data, status=200)
