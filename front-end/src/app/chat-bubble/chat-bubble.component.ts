import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';
import { ChatService } from '../services/chat.service';
import { take } from 'rxjs/operators';

@Component({
  selector: 'chat-bubble',
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.css',
  imports: [CommonModule]
})
export class ChatBubble {
  @Input() message!: Message;
  @Input() initials: string = '';
  @Output() botResponse = new EventEmitter<Message>();

  constructor(private chatService: ChatService) {}

  sendButtonPayload(payload: string) {
    this.chatService.sendMessage(payload).pipe(take(1)).subscribe(responses => {
      responses.forEach(resp => {
        const botMessage: Message = {
          text: resp.text || '',
          image: resp.image || '',
          buttons: resp.buttons || [],
          role: 'bot',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        this.botResponse.emit(botMessage); 
      });
    });
  }
  
}
