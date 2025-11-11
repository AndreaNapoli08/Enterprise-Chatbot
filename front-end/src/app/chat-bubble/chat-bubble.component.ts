import { Component, Input, Output, EventEmitter, ChangeDetectorRef } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';
import { ChatService } from '../services/chat.service';
import { take } from 'rxjs/operators';
import { MessageBusService } from '../services/message-bus.service';
import { Datepicker } from 'flowbite-datepicker';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'chat-bubble',
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.css',
  imports: [CommonModule, FormsModule]
})
export class ChatBubble {
  @Input() message!: Message;
  @Input() initials: string = '';
  @Input() name: string | null = null;
  @Input() surname: string | null = null;
  @Output() botResponse = new EventEmitter<Message>();
  @Output() stateChangeLoading = new EventEmitter<boolean>();
  @Output() stateChangeConversation = new EventEmitter<boolean>();

  buttonsDisabled = false;
  selectedDate: Date | null = null;
  formatted = '';
  startTime?: string = '';
  duration = 0.5;
  disabledInputs = false;
  uniqueId = Math.random().toString(36).substring(2, 9);
  peopleCount = 1;
  passwordFields = [
    { key: 'old', label: 'Vecchia password', model: 'oldPassword' },
    { key: 'new', label: 'Nuova password', model: 'newPassword' }
  ];
  passwordVisibility: { [key: string]: boolean } = {
    old: false,
    new: false
  };
  passwords: { [key: string]: string } = {
    oldPassword: '',
    newPassword: ''
  };

  featuresList = [
    { id: 'proiettore', label: 'Videoproiettore', selected: false },
    { id: 'monitor', label: 'Monitor', selected: false },
    { id: 'microfono', label: 'Microfono', selected: false },
    { id: 'prese', label: 'Prese di corrente multiple', selected: false },
    { id: 'accesso_disabili', label: 'Accesso disabili', selected: false },
    { id: 'lavagna_digitale', label: 'Lavagna digitale', selected: false },
    { id: 'aria_condizionata', label: 'Aria condizionata', selected: false },
  ];

  constructor(
    private chatService: ChatService,
    private messageBus: MessageBusService,
    private cd: ChangeDetectorRef,
    private authService: AuthService
  ) {}

  ngAfterViewInit() {
    if (this.message.custom?.type === 'date_picker') {
      const inputEl = document.getElementById('date-picker-' + this.uniqueId);
      if (inputEl) {
        const today = new Date();
        const datepicker = new Datepicker(inputEl, {
          autohide: true,
          format: 'dd/mm/yyyy',
          minDate: today,
        });
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
      this.cd.detectChanges();
      console.log("uniqueId ", this.uniqueId);
    }
  }

  /** 🔧 Metodo riutilizzabile per inviare messaggi */
  private sendMessageToChat(message: string) {
    this.authService.getCurrentUser().pipe(take(1)).subscribe(user => {
      if (!user) {
        console.error('Nessun utente loggato');
        return;
      }

      const email = user.email; // ora è sempre definito
      this.chatService.sendMessage(message, email).pipe(take(1)).subscribe(responses => {
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
          console.log('📤 Risposta bot:', botMessage);
          this.botResponse.emit(botMessage);
        });
      });
    });
  }

  sendButtonPayload(payload: string) {
    this.buttonsDisabled = true;

    if (payload.startsWith("/choose_document")) {
      const botMessage: Message = {
        text: "Perfetto, cerco subito nei documenti",
        image: '',
        buttons: [],
        role: 'bot',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      this.botResponse.emit(botMessage);
      this.stateChangeLoading.emit(true);
    }

    if (payload === "/yes_close_conversation") {
      this.stateChangeConversation.emit(true);
    }

    this.sendMessageToChat(payload);
  }

  sendDate() {
    if (this.selectedDate && this.startTime && this.duration) {
      this.disabledInputs = true;
      const dateString = this.selectedDate.toLocaleDateString('it-IT', {
        weekday: 'long',
        day: '2-digit',
        month: 'long',
        year: 'numeric'
      });
      const message = `La riunione è ${dateString} alle ${this.startTime} per ${this.duration} ore.`;
      console.log(message);
      this.sendMessageToChat(message);
    }
  }

  incrementPeople() {
    if (this.peopleCount < 20) this.peopleCount++;
  }

  decrementPeople() {
    if (this.peopleCount > 1) this.peopleCount--;
  }

  sendPeopleCount() {
    this.disabledInputs = true;
    const message = `Saremo in ${this.peopleCount} persone alla riunione`;
    this.sendMessageToChat(message);
  }

  sendSelectedFeatures() {
    const selectedFeatures = this.featuresList.filter(f => f.selected).map(f => f.label);
    const message = `Le caratteristiche richieste per la sala sono: ${selectedFeatures.join(', ')}`;
    this.disabledInputs = true;
    this.stateChangeLoading.emit(true);
    this.sendMessageToChat(message);
  }

  deleteReservation(id: string) {
    const message = `Elimina la prenotazione con id: ${id}`;
    const button = document.getElementById('delete-reservation-' + id) as HTMLButtonElement;
    if (button) button.disabled = true;
    this.stateChangeLoading.emit(true);
    this.sendMessageToChat(message);
  }

  sendNewPassword() {
    this.disabledInputs = true;
    const message = `La vecchia password è: ${this.passwords['oldPassword']} La nuova password è: ${this.passwords['newPassword']}`;
    console.log(message);
    this.stateChangeLoading.emit(true);
    this.sendMessageToChat(message);
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

  togglePasswordVisibility(fieldKey: string) {
    this.passwordVisibility[fieldKey] = !this.passwordVisibility[fieldKey];
  }
}
