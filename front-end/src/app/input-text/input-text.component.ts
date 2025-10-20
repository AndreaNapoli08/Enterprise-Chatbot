import { Component, ElementRef, EventEmitter, Input, Output, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';  
import { ChatService } from '../services/chat.service';  
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
  @Input() disabled!: boolean;
  @ViewChild('textarea') textarea!: ElementRef<HTMLTextAreaElement>;

  conversationEnded = false;

  constructor(private chatService: ChatService) {}
  
  ngOnChanges() {
      setTimeout(() => {
        this.textarea.nativeElement.focus();
      }, 0);
  }

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
          text: resp.text || '',
          image: resp.image || '',
          buttons: resp.buttons || [],
          attachment: resp.attachment || undefined,
          role: 'bot',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };
        console.log('Intent:', resp.intent, 'Confidence:', resp.confidence);

        if(resp.intent === 'conversation_end' || resp.intent === 'goodbye') {
          // aggiungo un timer così viene visualizzato il messaggio di bot prima di disabilitare l'input
          setTimeout(() => {
              this.disabled = true;
              this.conversationEnded = true;
          }, 800);
        } 
        this.submitAnswer.emit(botMessage); 
      });
    });
    this.answer = '';
  }

}
