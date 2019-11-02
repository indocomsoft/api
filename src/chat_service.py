import socketio

from src.services import (
    ChatRoomService,
    ChatService,
    LinkedInLogin,
    OfferService,
    UserService,
)


class ChatSocketService(socketio.AsyncNamespace):
    def __init__(self, namespace, config, sio):
        super().__init__(namespace)
        self.chat_service = ChatService(config)
        self.chat_room_service = ChatRoomService(config)
        self.linkedin_login = LinkedInLogin(config)
        self.user_service = UserService(config)
        self.offer_service = OfferService(config)
        self.config = config

    async def on_req_testing(self, sid, data):
        await self.emit("res_testing", {"data": "hello world"})

    async def _authenticate(self, token):
        linkedin_user = self.linkedin_login._get_linkedin_user(token=token)
        user = self.user_service.get_user_by_linkedin_id(
            user_id=linkedin_user.get("user_id")
        )
        return user.get("id")

    async def _get_chat_rooms(self, sid, user_id):
        rooms = self.chat_room_service.get_chat_rooms(user_id=user_id)
        for room in rooms:
            self.enter_room(sid, room.get("chat_room_id"))
        self.enter_room(sid, user_id)
        return rooms

    async def on_connect(self, sid, environ):
        return {"data": "success"}

    async def on_disconnect(self, sid):
        return {"data": "success"}

    async def on_req_chat_rooms(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        rooms = await self._get_chat_rooms(sid=sid, user_id=user_id)
        await self.emit("res_chat_rooms", rooms, room=user_id)

    async def on_req_conversation(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        conversation = self.chat_service.get_conversation(
            user_id=user_id, chat_room_id=data.get("chat_room_id")
        )
        await self.emit("res_conversation", conversation, room=user_id)

    async def on_req_new_message(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        room_id = data.get("chat_room_id")
        chat = self.chat_service.set_new_message(
            chat_room_id=data.get("chat_room_id"),
            message=data.get("message"),
            author_id=user_id,
        )

        await self.emit("res_new_message", chat, room=room_id)

    async def on_req_new_offer(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        room_id = data.get("chat_room_id")
        offer = self.offer_service.set_new_offer(
            author_id=user_id,
            chat_room_id=data.get("chat_room_id"),
            price=data.get("price"),
            number_of_shares=data.get("number_of_shares"),
        )
        await self.emit("res_new_offer", offer, room=room_id)

    async def on_req_accept_offer(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        room_id = data.get("chat_room_id")
        offer = self.offer_service.set_accept_offer(
            chat_room_id=room_id, offer_id=data.get("offer_id"), user_id=user_id
        )
        await self.emit("res_accept_offer", offer, room=room_id)

    async def on_req_decline_offer(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        room_id = data.get("chat_room_id")
        offer = self.offer_service.set_reject_offer(
            chat_room_id=room_id, offer_id=data.get("offer_id"), user_id=user_id
        )
        await self.emit("res_decline_offer", offer, room=room_id)

    async def on_req_other_party_details(self, sid, data):
        user_id = await self._authenticate(token=data.get("token"))
        room_id = data.get("chat_room_id")

        other_party_details = self.chat_room_service.get_other_party_details(
            chat_room_id=room_id, user_id=user_id
        )

        await self.emit("res_other_party_details", other_party_details, room=room_id)
