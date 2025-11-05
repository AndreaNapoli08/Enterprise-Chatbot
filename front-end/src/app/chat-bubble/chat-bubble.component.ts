import { Component, Input, Output, EventEmitter } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';
import { ChatService } from '../services/chat.service';
import { take } from 'rxjs/operators';
import { MessageBusService } from '../services/message-bus.service';
import { Datepicker } from 'flowbite-datepicker';

@Component({
  selector: 'chat-bubble',
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.css',
  imports: [CommonModule, FormsModule]
})
export class ChatBubble {
  @Input() message!: Message;
  @Input() initials: string = '';
  @Output() botResponse = new EventEmitter<Message>();
  @Output() stateChangeLoading = new EventEmitter<boolean>();
  @Output() stateChangeConversation = new EventEmitter<boolean>();
  buttonsDisabled: boolean = false;
  
  constructor(
    private chatService: ChatService, 
    private messageBus: MessageBusService
  ) {}

  selectedDate: Date | null = null;
  formatted: string = '';
  startTime?: string = '';
  duration: number = 0.5; // valore selezionato in minuti
  disabledInputs = false;
  countId: number = 0;
  peopleCount = 1;

  ngAfterViewInit() {
    if(this.message.custom?.type === 'date_picker') {
      const inputEl = document.getElementById('date-picker-' + this.countId);
      if (inputEl) {
        const today = new Date();

        const datepicker = new Datepicker (inputEl, {
          autohide: true,
          format: 'dd/mm/yyyy',
          minDate: today,
        });

        // Esempio: catturare evento di cambio data
        inputEl.addEventListener('changeDate', (event: any) => {
          this.selectedDate = event.detail.date;
          this.formatted = this.selectedDate?.toLocaleDateString('it-IT', {
            weekday: 'long',
            day: '2-digit',
            month: 'long',
            year: 'numeric'
          }) ?? '';
        });
      }
      this.countId += 1;
    }
  }

  sendButtonPayload(payload: string) {
    this.buttonsDisabled = true;
    if(payload.startsWith("/choose_document")) {
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
        console.log('📤 Risposta bot:', botMessage);
        this.botResponse.emit(botMessage); 
      });
    });
  }

  sendDate() {
    if (this.selectedDate && this.startTime && this.duration) {
      // Combina data e orario in formato leggibile
      const dateString = this.selectedDate.toLocaleDateString('it-IT', {
        weekday: 'long',
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      });
       // Disabilita input
      this.disabledInputs = true;

      const message = `La riunione è ${dateString} alle ${this.startTime} per ${this.duration} ore.`;
      // invio la data selezionata a RASA
      this.chatService.sendMessage(message).pipe(take(1)).subscribe(responses => {
        responses.forEach(resp => {
          const botMessage: Message = {
            text: resp.text || '',
            image: resp.image || '',
            custom: resp.custom || {},
            buttons: resp.buttons || [],
            attachment: resp.attachment || undefined,
            role: 'bot',
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          };
          this.botResponse.emit(botMessage); 
        });
      });
    }      
  }

  incrementPeople() {
    if (this.peopleCount < 20) {
      this.peopleCount++;
    }
  }

  decrementPeople() {
    if (this.peopleCount > 1) {
      this.peopleCount--;
    }
  }

  sendPeopleCount() {
    this.disabledInputs = true;

    const message = `Saremo in ${this.peopleCount} persone alla riunione`;
    this.chatService.sendMessage(message).pipe(take(1)).subscribe(responses => {
      responses.forEach(resp => {
        const botMessage: Message = {
          text: resp.text || '',
          image: resp.image || '',
          custom: resp.custom || {},
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

  isLongButtonLayout(buttons: any[]): boolean {
    return buttons.some(b => b.title.length > 10);
  }
  
}
