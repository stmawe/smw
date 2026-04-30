"""
WebSocket consumers for real-time messaging.
"""

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils.timezone import now
from mydak.models import Conversation, Message

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat between buyer and seller.
    Handles message sending/receiving, typing indicators, read tracking.
    """
    
    async def connect(self):
        """Handle WebSocket connection."""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Check if user is part of the conversation
        is_member = await self.check_conversation_membership()
        if not is_member:
            await self.close()
            return
        
        # Join the channel group
        await self.channel_layer.group_add(
            self.conversation_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send online status
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_status',
                'status': 'online',
                'user_id': self.user.id,
                'timestamp': now().isoformat(),
            }
        )
        
        logger.info(f'User {self.user.id} connected to chat {self.conversation_id}')
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Send offline status
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_status',
                'status': 'offline',
                'user_id': self.user.id,
                'timestamp': now().isoformat(),
            }
        )
        
        # Leave the channel group
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )
        
        logger.info(f'User {self.user.id} disconnected from chat {self.conversation_id}')
    
    async def receive(self, text_data):
        """Handle incoming WebSocket message."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'message')
            
            if message_type == 'message':
                await self.handle_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'read':
                await self.handle_read(data)
            else:
                logger.warning(f'Unknown message type: {message_type}')
        
        except json.JSONDecodeError:
            logger.error('Invalid JSON received')
        except Exception as e:
            logger.error(f'Error handling message: {e}')
    
    async def handle_message(self, data):
        """Handle incoming chat message."""
        content = data.get('content', '').strip()
        attachment = data.get('attachment')
        
        if not content and not attachment:
            return
        
        # Save message to database
        message = await self.save_message(content, attachment)
        
        if message:
            # Broadcast message to group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'sender_id': self.user.id,
                    'sender_email': self.user.email,
                    'content': message.content,
                    'attachment': str(message.attachment.url) if message.attachment else None,
                    'timestamp': message.created_at.isoformat(),
                    'is_read': message.is_read,
                }
            )
    
    async def handle_typing(self, data):
        """Handle typing indicator."""
        is_typing = data.get('is_typing', False)
        
        # Broadcast typing status to group
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'user_typing',
                'user_id': self.user.id,
                'user_email': self.user.email,
                'is_typing': is_typing,
                'timestamp': now().isoformat(),
            }
        )
    
    async def handle_read(self, data):
        """Handle message read receipt."""
        message_ids = data.get('message_ids', [])
        
        if message_ids:
            await self.mark_messages_as_read(message_ids)
            
            # Broadcast read status to group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'messages_read',
                    'message_ids': message_ids,
                    'user_id': self.user.id,
                    'timestamp': now().isoformat(),
                }
            )
    
    # Group message handlers
    
    async def chat_message(self, event):
        """Send chat message to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_email': event['sender_email'],
            'content': event['content'],
            'attachment': event['attachment'],
            'timestamp': event['timestamp'],
            'is_read': event['is_read'],
        }))
    
    async def user_typing(self, event):
        """Send typing indicator to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_email': event['user_email'],
            'is_typing': event['is_typing'],
            'timestamp': event['timestamp'],
        }))
    
    async def user_status(self, event):
        """Send user status to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'status',
            'user_id': event['user_id'],
            'status': event['status'],
            'timestamp': event['timestamp'],
        }))
    
    async def messages_read(self, event):
        """Send read receipt to WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_ids': event['message_ids'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp'],
        }))
    
    # Database operations
    
    @database_sync_to_async
    def check_conversation_membership(self):
        """Check if user is part of the conversation."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in [conversation.seller, conversation.buyer]
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content, attachment=None):
        """Save message to database."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            
            # Determine sender and receiver
            if self.user == conversation.seller:
                receiver = conversation.buyer
            else:
                receiver = conversation.seller
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                receiver=receiver,
                listing=conversation.listing,
                content=content,
            )
            
            # Update conversation last_message_at
            conversation.last_message_at = now()
            conversation.save()
            
            return message
        
        except Conversation.DoesNotExist:
            logger.error(f'Conversation {self.conversation_id} not found')
            return None
        except Exception as e:
            logger.error(f'Error saving message: {e}')
            return None
    
    @database_sync_to_async
    def mark_messages_as_read(self, message_ids):
        """Mark messages as read."""
        try:
            # Only mark messages sent to this user as read
            Message.objects.filter(
                id__in=message_ids,
                receiver=self.user,
                is_read=False
            ).update(is_read=True)
        except Exception as e:
            logger.error(f'Error marking messages as read: {e}')
