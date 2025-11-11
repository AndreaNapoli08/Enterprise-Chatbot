import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';
import { Profile } from '../profile/profile.component';
import { AuthService } from '../services/auth.service';
import { Message } from '../interfaces/message';
import { take } from 'rxjs/internal/operators/take';
import { ChatService } from '../services/chat.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatBubble, InputText, Profile],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class Home implements AfterViewChecked {
  // dati utente
  email: string | null = null;
  initials: string = '';
  name: string | null = null;
  surname: string | null = null;
  role: string | null = null;
  // chat
  messages: Message[] = [];
  shouldScroll = false;
  loading = false;
  buttons = false;
  waiting_answer = false;
  reservationInProgress = false;
  conversationEnded = false;
  human_operator = false;

  // Visualizzazione elementi dopo un'attesa prolungata e tempo di ragionamento
  long_waiting = false;
  long_waiting_text = '';
  longWaitTimer: any = null;
  textChangeTimer: any = null;
  textIndex = 0;
  startTime = 0;
  waitingTexts = [
    'Sto pensando...',
    'Lettura dei documenti...',
    'Sto cercando una risposta...'
  ];

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef<HTMLDivElement>;
  constructor(
    private authService: AuthService,
    private chatService: ChatService
  ) {}

  ngOnInit() {
    // Ottieni l'utente corrente dal backend
    this.authService.getCurrentUser().subscribe(user => {
      if (user && typeof user !== 'string') { 
        this.email = user.email;
        this.initials = this.getInitialsFromEmail(this.email);
        this.name = user.firstName;
        this.surname = user.lastName;
        this.role = user.role;
      } else {
        this.email = null;
        this.initials = '';
      }
    });
  }

  handleMessage(message: any) {
    this.loading = true;
    this.shouldScroll = true;
    if(message.role === 'bot' && message.text.toLowerCase().includes('operatore umano')) {
      this.human_operator = true;
    }

    // Funzione di utilità per avviare l'indicatore di "attesa prolungata"
    const startLongWaiting = (delay = 20000, interval = 10000) => {
      clearTimeout(this.longWaitTimer);
      clearInterval(this.textChangeTimer);
      this.longWaitTimer = setTimeout(() => {
        this.long_waiting = true;
        this.textIndex = 0;
        this.long_waiting_text = this.waitingTexts[this.textIndex];

        this.textChangeTimer = setInterval(() => {
          // Cambia ciclicamente il testo mostrato per indicare attività
          this.textIndex = (this.textIndex + 1) % this.waitingTexts.length;
          this.long_waiting_text = this.waitingTexts[this.textIndex];
        }, interval);
      }, delay);
    };

    if (message.role === 'bot') {
      clearTimeout(this.longWaitTimer);
      clearInterval(this.textChangeTimer);

      const elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000);

      // Reset dello stato di attesa lunga
      this.long_waiting = false;
      this.long_waiting_text = '';

      this.messages.push({
        ...message,
        elapsedSeconds: elapsedSeconds > 20 ? elapsedSeconds : null
      });
      // Se il messaggio del bot non ha pulsanti, non è in attesa di risposta
      this.waiting_answer = message.buttons.length > 0;
      this.loading = this.waiting_answer;

      // Se il bot inizia una ricerca, mostra il messaggio di attesa dopo un po’
      if (message.text === "Perfetto, cerco subito nei documenti") {
        startLongWaiting();
        this.startTime = Date.now();
      }
      if(message.custom?.type == "date_picker" || message.custom?.type == "number_partecipants" || message.custom?.type == "features_meeting_room") {
        this.reservationInProgress = true;
      }else{
        this.reservationInProgress = false;
      }
    } else {
      // Messaggio utente
      this.messages.push(message);

      this.startTime = Date.now();

      // Dopo un breve ritardo, mostra un messaggio di "Sto pensando..."
      // e cambialo ciclicamente per indicare che il bot sta ancora elaborando
      startLongWaiting();
    }
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  private scrollToBottom(): void {
    try {
      this.scrollContainer.nativeElement.scroll({
        top: this.scrollContainer.nativeElement.scrollHeight,
        behavior: 'smooth'
      });
    } catch (err) {
      console.warn('Scroll error:', err);
    }
  }

  getInitialsFromEmail(email: string | null): string {
    if (!email) return '';
    const [name] = email.split('@');
    return name
      .split('.')
      .map(part => part[0]?.toUpperCase())
      .join('') || name[0].toUpperCase();
  }

  sendMessageToChat(message: string) {
    this.authService.getCurrentUser().pipe(take(1)).subscribe(user => {
      if (!user) {
        console.error('Nessun utente loggato');
        return;
      }

      const email = user.email;
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
          this.handleMessage(botMessage);
        });
      });
    });
  }

  booking_room() {
    this.loading = true;
    const message = "Vorrei prenotare una sala riunioni";
    this.messages.push(
      { text: message, role: 'user', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    });
    this.startTime = Date.now();
    this.sendMessageToChat(message);
  }

  show_bookings() {
    this.loading = true;
    const message = "Mi mostri le mie prenotazioni";
    this.messages.push(
      { text: message, role: 'user', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    });
    this.startTime = Date.now();
    this.sendMessageToChat(message);
  }

  change_password() {
    this.loading = true;
    const message = "Vorrei cambiare la mia password";
    this.messages.push(
      { text: message, role: 'user', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    });
    this.startTime = Date.now();
    this.sendMessageToChat(message);
  }

  frequently_asked_questions() {
    this.loading = true;
    const faqs = [
      "Quanti giorni di ferie ha un lavoratore full time?",
      "Entro quando devo pianificare le mie ferie?",
      "Come posso richiedere un permesso per visita medica?",
      "A quanto ammonta il valore dei buoni pasto elettronici?",
      "Cosa devo fare se perdo la mia card dei buoni pasto?",
      "Come posso aggiornare i miei dati bancari o anagrafici?",
      "Quando viene accreditato lo stipendio mensile?",
      "Che cos'è la VPN aziendale?",
      "Chi devo contattare se ho problemi con la vpn?",
      "Mi puoi elencare tutti i benefit a cui hanno diritto i dipendenti?"
    ];

    // Estrae una domanda casuale
    const randomIndex = Math.floor(Math.random() * faqs.length);
    const message = faqs[randomIndex];
    this.messages.push(
      { text: message, role: 'user', time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    });
    this.startTime = Date.now();
    this.sendMessageToChat(message);
  }

}
