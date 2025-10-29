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

    const startTime = performance.now();

    // invio a Rasa
    this.chatService.sendMessage(text).pipe(take(1)).subscribe(responses => {
      const elapesedTime = (performance.now() - startTime) / 1000;
      console.log(`Rasa response time: ${elapesedTime.toFixed(2)} seconds`);

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
        
        if(resp.intent === 'conversation_end' || resp.intent === 'goodbye' || resp.text?.toLowerCase().includes('operatore umano')) {
          // aggiungo un timer così viene visualizzato il messaggio di bot prima di disabilitare l'input
          // dobbiamo controllare se la risposta contiene "operatore umano" perché l'intent è sempre nlu_fallback quindi non possiamo basarci 
          // solo su quello per disabilitare l'input
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
