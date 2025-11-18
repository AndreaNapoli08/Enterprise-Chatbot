import { Component, ElementRef, ViewChild, AfterViewChecked, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';
import { Profile } from '../profile/profile.component';
import { AuthService } from '../services/auth.service';
import { Message } from '../interfaces/message';
import { take } from 'rxjs/internal/operators/take';
import { ChatService } from '../services/chat.service';
import { Sidebar } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatBubble, InputText, Profile, Sidebar],
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

  empty_input = true;
  sessions: any[] = [];
  current_session = "";

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
    this.getSession();
    // Ottieni l'utente corrente dal backend
    this.authService.getCurrentUser().subscribe(user => {
      if (user && typeof user !== 'string') { 
        this.email = user.email;
        this.initials = this.getInitialsFromEmail(this.email);
        this.name = user.firstName;
        this.surname = user.lastName;
        this.role = user.role;
        //this.loadChatHistory();
      } else {
        this.email = null;
        this.initials = '';
      }
    });
  }

  getSession() {
    this.authService.getCurrentUser().pipe(take(1)).subscribe(user => {
      if (!user) return;
      const email = user.email;

      fetch(`http://localhost:5050/chat/get_sessions/${email}`)
        .then(response => {
          if (response.status === 404) {
            return []; // non  un errore, vuol dire solo che l'utente non ha chat attualmente
          }
          if (!response.ok) throw new Error('Errore nella richiesta');
          return response.json(); 
        })
        .then(sessions => {
          this.sessions = sessions;
          console.log('Sessioni recuperate:', this.sessions);
        })
        .catch(err => console.error('Errore nel recuperare le sessioni:', err));
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  scrollToBottom(): void {
    try {
      this.scrollContainer.nativeElement.scroll({
        top: this.scrollContainer.nativeElement.scrollHeight,
        behavior: 'smooth'
      });
    } catch (err) {
      console.warn('Scroll error:', err);
    }
  }

  handleMessage(message: any): void {
    this.loading = true;
    this.shouldScroll = true;
    this.getSession();

    console.log('Messaggio ricevuto:', message);
    // Controllo d’ingresso
    if (!message || typeof message !== 'object') return;

    if(message.text.startsWith("Grazie per aver utilizzato il nostro servizio")){
      this.closeChatSession();
    }
    console.log(message);
    this.saveMessageToBackend(message);
    
    const isBot = message.role === 'bot';
    const isHumanOperatorTrigger = isBot && message.text.toLowerCase().includes('operatore umano');

    if (isHumanOperatorTrigger) {
      this.human_operator = true;
    }

    // Gestione messaggi del bot
    if (isBot) {
      this.handleBotMessage(message);
      return;
    }

    // Gestione messaggi utente
    this.handleUserMessage(message);
  }

  closeChatSession() {
    this.authService.getCurrentUser().pipe(take(1)).subscribe(user => {
      if (!user) return;
      const email = user.email;

      fetch(`http://localhost:5050/chat/close_session/${this.current_session}`, {
        method: 'POST'
      })
      .then(() => {
        console.log('Chat session chiusa');
      })
      .catch(err => console.error('Errore nel chiudere la sessione:', err));
    });
  }

  async saveMessageToBackend(message: any) {
    if (!this.email) return;

    try {
      const res = await fetch(`http://localhost:5050/chat/save_message/${this.current_session}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_email: this.email,
          sender: message.role,
          type: this.getMessageType(message),
          content: {
            text: message.text || '',
            buttons: message.buttons || [],
            image: message.image || '',
            custom: message.custom || {},
            attachment: message.attachment || null,
          },
          timestamp: new Date().toISOString(),
        }),
      });

      const data = await res.json();

      // 🔥 se è stata creata una nuova sessione → aggiornala
      if (data.session_id && this.current_session !== data.session_id) {
        this.current_session = data.session_id;
      }

    } catch (error) {
      console.error('Errore nel salvataggio del messaggio:', error);
    }
  }


  async loadChatHistory(sessionId: string) {
    this.current_session = sessionId;
    if (!this.email) return;

    try {
      const res = await fetch(`http://localhost:5050/chat/get_messages/${sessionId}`);
      const data = await res.json();
      if (data.messages) {
        // Sovrascrive i messaggi attuali con quelli salvati
        this.messages = data.messages.map((m:any) => ({
          role: m.sender,
          text: m.content.text || '',
          buttons: m.content.buttons || [],
          image: m.content.image || '',
          custom: m.content.custom || {},
          attachment: m.content.attachment || null,
          time: new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          disabled: !data.active
        }));
      }
      if(data.active == false){
        this.conversationEnded = true;
      }else{
        this.conversationEnded = false;
      }
    } catch (err) {
      console.error("Errore nel caricamento della chat:", err);
    }
    this.shouldScroll = true;
  }

  getMessageType(message: any): string {
    if (message.buttons?.length) return 'buttons';
    if (message.attachment) return 'file';
    if (message.custom?.type) return message.custom.type;
    return 'text';
  }

  handleBotMessage(message: any) {
    this.resetLongWait();

    const elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000);

    this.messages.push({
      ...message,
      elapsedSeconds: elapsedSeconds > 20 ? elapsedSeconds : null,
    });

    this.waiting_answer = message.buttons?.length > 0;
    this.loading = this.waiting_answer;

    if (message.text === 'Perfetto, cerco subito nei documenti') {
      this.startLongWaiting();
      this.startTime = Date.now();
    }
    this.empty_input = true;
    this.shouldScroll = true;

    const interactiveTypes = [
      'date_picker',
      'number_partecipants',
      'features_meeting_room',
      'change_password',
    ];

    this.reservationInProgress = interactiveTypes.includes(message.custom?.type);
  }

  handleUserMessage(message: any) {
    this.messages.push(message);
    this.startTime = Date.now();
    this.startLongWaiting();
  }

  resetLongWait() {
    clearTimeout(this.longWaitTimer);
    clearInterval(this.textChangeTimer);
    this.long_waiting = false;
    this.long_waiting_text = '';
  }

  // Funzione di utilità per avviare l'indicatore di "attesa prolungata"
  startLongWaiting (delay = 20000, interval = 10000) {
    clearTimeout(this.longWaitTimer);
    clearInterval(this.textChangeTimer);
    this.longWaitTimer = setTimeout(() => {
      this.long_waiting = true;
      this.textIndex = 0;
      this.long_waiting_text = this.waitingTexts[this.textIndex];

      this.textChangeTimer = setInterval(() => {
        this.textIndex = (this.textIndex + 1) % this.waitingTexts.length;
        this.long_waiting_text = this.waitingTexts[this.textIndex];
      }, interval);
    }, delay);
  };

  getInitialsFromEmail(email: string | null): string {
    if (!email) return '';
    const [name] = email.split('@');
    return name
      .split('.')
      .map(part => part[0]?.toUpperCase())
      .join('') || name[0].toUpperCase();
  }

  sendMessageToChat(message: string) {
    this.loading = true;
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
          this.handleMessage(botMessage);
        });
      });
    });
  }

  booking_room() {
    const text = "Vorrei prenotare una sala riunioni";
    const message = {
      text,
      role: 'user',
      buttons: [],
      image: '',
      custom: {},
      attachment: null,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    this.handleMessage(message);
    this.startTime = Date.now();
    this.sendMessageToChat(text);
  }

  show_bookings() {
    const text = "Mi mostri le mie prenotazioni";
    const message = {
      text,
      role: 'user',
      buttons: [],
      image: '',
      custom: {},
      attachment: null,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    this.handleMessage(message);
    this.startTime = Date.now();
    this.sendMessageToChat(text);
  }

  change_password() {
    const text = "Vorrei cambiare la mia password";
    const message = {
      text,
      role: 'user',
      buttons: [],
      image: '',
      custom: {},
      attachment: null,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    this.handleMessage(message);
    this.startTime = Date.now();
    this.sendMessageToChat(text);
  }

  frequently_asked_questions() {
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
    const text = faqs[randomIndex];
    const message = {
      text,
      role: 'user',
      buttons: [],
      image: '',
      custom: {},
      attachment: null,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    this.handleMessage(message);
    this.startTime = Date.now();
    this.sendMessageToChat(text);
  }

  closeConversation() {
    const text = "Grazie per aver utilizzato il nostro servizio. Buona giornata!";
    const message = {
      text,
      role: 'bot',
      buttons: [],
      image: '',
      custom: {},
      attachment: null,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    this.handleMessage(message);
    this.closeChatSession();
    this.conversationEnded = true;
  }
  
}
