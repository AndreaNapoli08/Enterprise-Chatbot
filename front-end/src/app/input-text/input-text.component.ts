import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';  
import { ChatService } from '../services/chat.service';  // importa il servizio
import { take } from 'rxjs/operators';

@Component({
  selector: 'input-text',
  imports: [FormsModule, CommonModule],
  templateUrl: './input-text.component.html',
  styleUrl: './input-text.component.css'
})

export class InputText {
  answer = '';
  @Output() submitAnswer = new EventEmitter<Message>();
  @Output() botResponse = new EventEmitter<Message>();

  constructor(private chatService: ChatService) {}

  onSubmit() {
    const text = this.answer.trim();
    if (!text) return;

    const now = new Date();
    const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const message: Message = {
      text,
      role: 'user',
      time
    };
    
    // invio ad home per visualizzare il messaggio graficamente
    this.submitAnswer.emit(message);

    // invio a Rasa
    this.chatService.sendMessage(text).pipe(take(1)).subscribe(responses => {
      responses.forEach(resp => {
        const botMessage: Message = {
          text: resp.text,
          role: 'bot',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        this.botResponse.emit(botMessage); //mandiamo la risposta al componente padre
      });
    });
    this.answer = '';
  }

}
