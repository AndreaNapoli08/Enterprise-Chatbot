import { Component, ElementRef, EventEmitter, Input, Output, ViewChild, SimpleChanges  } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';  
import { ChatService } from '../services/chat.service';  
import { take } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

@Component({
  selector: 'input-text',
  standalone: true,
  imports: [FormsModule, CommonModule],
  templateUrl: './input-text.component.html',
  styleUrls: ['./input-text.component.css']
})

export class InputText {
  answer = '';
  @Output() submitAnswer = new EventEmitter<Message>();
  @Input() disabled!: boolean;
  @ViewChild('textarea') textarea!: ElementRef<HTMLTextAreaElement>;
  @Input() conversationEnded = false;
  @Input() humanOperator = false;
  @Output() stateEmptyInput = new EventEmitter<boolean>();

  constructor(
    private chatService: ChatService, 
    private authService: AuthService,
    private router: Router
  ) {}
  
  ngOnChanges(changes: SimpleChanges) {
    // Quando humanOperator diventa true → disabilita subito la barra
    if (changes['humanOperator'] && changes['humanOperator'].currentValue === true) {
      this.disabled = true;
      this.conversationEnded = true;
      return;
    }

    // Se non è disabilitato, metti il focus sull'input text
    if (!this.disabled) {
      setTimeout(() => {
        this.textarea?.nativeElement.focus();
      }, 0);
    }
  }

  onTextChange(value: string) {
    this.stateEmptyInput.emit(value.trim().length === 0);
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
    this.authService.getCurrentUser().pipe(take(1)).subscribe(user => {
      if (!user) {
        console.error('Nessun utente loggato');
        return;
      }

      const email = user.email; // ora è sempre definito
      this.chatService.sendMessage(text, email).pipe(take(1)).subscribe(responses => {
        responses.forEach(resp => {
          const botMessage: Message = {
            text: resp.text || resp.custom?.text || '',
            image: resp.image || '',
            custom: resp.custom || {},
            buttons: resp.buttons || [],
            attachment: resp.attachment || undefined,
            role: 'bot',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          this.submitAnswer.emit(botMessage); 
        });
      });
      this.answer = '';
    });
  }

  createNewChat() {
    this.router.navigateByUrl('/', { skipLocationChange: true }).then(() => {
      this.router.navigate(['/home']);
    });
  }
}
