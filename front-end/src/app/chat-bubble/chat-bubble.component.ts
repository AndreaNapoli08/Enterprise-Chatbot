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
  @Output() stateChangeLoading = new EventEmitter<boolean>();
  @Output() stateChangeConversation = new EventEmitter<boolean>();
  buttonsDisabled: boolean = false;
  
  constructor(private chatService: ChatService) {}

  sendButtonPayload(payload: string) {
    this.buttonsDisabled = true;
    if(payload == "/choose_yes_document") {
      const botMessage: Message = {
          text: "Perfetto, cerco subito nei documenti",
          image:'',
          buttons: [],
          role: 'bot',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        this.botResponse.emit(botMessage); 
        this.stateChangeLoading.emit(true);
    }
    if(payload == "/yes_close_conversation") {
      this.stateChangeConversation.emit(true);
    }
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

  downloadFile(fileUrl: string, fileName: string) {
    const link = document.createElement('a');
    link.href = fileUrl;
    link.download = fileName;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
}
