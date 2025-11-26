import { Component, ElementRef, ViewChild, AfterViewChecked, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';
import { AuthService } from '../services/auth.service';
import { Message } from '../interfaces/message';
import { take } from 'rxjs/internal/operators/take';
import { ChatService } from '../services/chat.service';
import { Sidebar } from '../sidebar/sidebar.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatBubble, InputText, Sidebar],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class Home implements AfterViewChecked {
  /* ----------------- USER DATA ----------------- */
  email: string | null = null;
  name: string | null = null;
  surname: string | null = null;
  initials = '';
  role: string | null = null;

  /* ----------------- CHAT STATE ---------------- */
  messages: Message[] = [];
  sessions: any[] = [];
  current_session = '';
  conversationEnded = false;
  human_operator = false;
  reservationInProgress = false;
  shouldScroll = false;
  loading = false;
  waiting_answer = false;

  /* ----------------- LONG WAITING INDICATOR ----- */
  long_waiting = false;
  long_waiting_text = '';
  waitingTexts = [
    'Sto pensando...',
    'Lettura dei documenti...',
    'Sto cercando una risposta...',
  ];
  longWaitTimer: any = null;
  textChangeTimer: any = null;
  textIndex = 0;
  startTime = 0;

  sidebarOpen = false;
  isDesktop = window.innerWidth >= 768;

  @ViewChild('scrollContainer') scrollContainer!: ElementRef<HTMLDivElement>;
  @ViewChild(Sidebar) sidebar!: Sidebar;

  constructor(
    private auth: AuthService,
    private chatService: ChatService
  ) {}

  /* ------------------------------------------------------*/
  /*  INIZIALIZZAZIONE COMPONENTE                          */
  /*  -----------------------------------------------------*/
  
  private _empty_input = true;

  get empty_input(): boolean {
    return this._empty_input;
  }

  set empty_input(value: boolean) {
    this._empty_input = value;

    // Se diventa true, scrolla in basso
    if (value) {
      setTimeout(() => this.scrollToBottom(), 0);
    }
  }


  ngOnInit() {
    this.loadUser();
    this.getSessions();
  }

  loadUser() {
    this.auth.getCurrentUser().subscribe((u) => {
      if (!u || typeof u === 'string') return;

      this.email = u.email;
      this.name = u.firstName;
      this.surname = u.lastName;
      this.role = u.role;
      this.initials = this.getInitialsFromEmail(this.email);
    });
  }

  /* -------------------------------------------------------- */
  /*  SESSIONS                                                */
  /* -------------------------------------------------------- */

  getSessions() {
    this.auth.getCurrentUser().pipe(take(1)).subscribe((user) => {
      if (!user) return;

      fetch(`http://localhost:5050/chat/get_sessions/${user.email}`)
        .then((res) => (res.status === 404 ? [] : res.json()))
        .then((s) => (this.sessions = s))
        .catch((e) => console.error('Errore sessioni:', e));
    });
  }

  closeChatSession() {
    fetch(`http://localhost:5050/chat/close_session/${this.current_session}`, {
      method: 'POST',
    }).catch((e) =>
      console.error('Errore nel chiudere la sessione:', e)
    );
  }

  async loadChatHistory(sessionId: string) {
    this.current_session = sessionId;

    try {
      const res = await fetch(
        `http://localhost:5050/chat/get_messages/${sessionId}`
      );
      const data = await res.json();

      this.messages = data.messages?.map((m: any) => ({
        role: m.sender,
        text: m.content.text,
        buttons: m.content.buttons,
        image: m.content.image,
        custom: m.content.custom,
        attachment: m.content.attachment,
        time: new Date(m.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
        disabled: !data.active,
      }));

      this.conversationEnded = !data.active;
      this.shouldScroll = true;
    } catch (err) {
      console.error('Errore caricando chat:', err);
    }
  }

  /* -------------------------------------------------------- */
  /*  MESSAGE HELPERS                                         */
  /* -------------------------------------------------------- */

  createMessage(text: string | undefined, role: 'user' | 'bot'): Message {
    return {
      text,
      role,
      buttons: [],
      image: '',
      custom: {},
      attachment: undefined,
      time: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      }),
    };
  }

  getMessageType(m: any): string {
    if (m.buttons?.length) return 'buttons';
    if (m.attachment) return 'file';
    if (m.custom?.type) return m.custom.type;
    return 'text';
  }

  /* -------------------------------------------------------- */
  /*  HANDLE INCOMING MESSAGE                                 */
  /* -------------------------------------------------------- */

  handleMessage(message: Message): void {
    this.loading = true;
    this.shouldScroll = true;
    this.getSessions();

    if (!message || typeof message !== 'object') return;

    if(message.text?.startsWith("Grazie per aver utilizzato il nostro servizio")){
      this.closeChatSession();
    }

    this.saveMessageToBackend(message);

    const isBot = message.role === 'bot';
    const isHumanOperatorTrigger = isBot && message.text?.toLowerCase().includes('operatore umano');

    if (isHumanOperatorTrigger) {
      this.human_operator = true;
    }

    if (isBot) {
      this.handleBotMessage(message);
      return;
    }

    this.handleUserMessage(message);
  }

   handleBotMessage(message: Message) {
    this.resetLongWait();

    const elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000);

    this.messages.push({
      ...message,
      elapsedSeconds: elapsedSeconds > 20 ? elapsedSeconds : null,
    });

    this.waiting_answer = !!message.buttons?.length;
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

    this.reservationInProgress = interactiveTypes.includes(message.custom?.type ?? '');
  }

  handleUserMessage(message: Message) {
    this.messages.push(message);
    this.startTime = Date.now();
    this.startLongWaiting();
  }

  /* ------------------------------------------------------*/
  /*  SALVATAGGIO MESSAGGI NEL BACKEND                     */ 
  /* ------------------------------------------------------*/

  async saveMessageToBackend(message: Message) {
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

      if (data.session_id && this.current_session !== data.session_id) {
        this.current_session = data.session_id;
      }

    } catch (error) {
      console.error('Errore nel salvataggio del messaggio:', error);
    }
  }

  /* -------------------------------------------------------- */
  /*  LONG WAITING                                            */
  /* -------------------------------------------------------- */

  resetLongWait() {
    clearTimeout(this.longWaitTimer);
    clearInterval(this.textChangeTimer);
    this.long_waiting = false;
    this.long_waiting_text = '';
  }

  startLongWaiting (delay = 20000, interval = 10000) {
    clearTimeout(this.longWaitTimer);
    clearInterval(this.textChangeTimer);
    this.longWaitTimer = setTimeout(() => {
      this.long_waiting = true;
      this.textIndex = 0;
      this.long_waiting_text = this.waitingTexts[0];

      this.textChangeTimer = setInterval(() => {
        this.textIndex = (this.textIndex + 1) % this.waitingTexts.length;
        this.long_waiting_text = this.waitingTexts[this.textIndex];
      }, interval);
    }, delay);
  }


  /* ------------------------------------------------------*/
  /*  INVIO MESSAGGI ALLA CHATBOT                          */  
  /*  -----------------------------------------------------*/

  sendMessageToChat(text: string) {
    this.loading = true;
    this.auth.getCurrentUser().pipe(take(1)).subscribe((user) => {
      if (!user) return;

      this.chatService.sendMessage(text, user.email).pipe(take(1)).subscribe((res) => {
        res.forEach((r) => {
          const msg = this.createMessage(r.text, 'bot');
          msg.buttons = r.buttons || [];
          msg.custom = r.custom || {};
          msg.image = r.image || '';
          msg.attachment = r.attachment;
          this.handleMessage(msg);
        });
      });
    });
  }

  /* -------------------------------------------------------- */
  /*  QUICK ACTIONS (COMPATTATE)                              */
  /* -------------------------------------------------------- */

  quickSend(text: string) {
    this.handleMessage(this.createMessage(text, 'user'));
    this.startTime = Date.now();
    this.sendMessageToChat(text);
  }

  booking_room() {
    this.quickSend('Vorrei prenotare una sala riunioni');
  }

  show_bookings() {
    this.quickSend('Mi mostri le mie prenotazioni');
  }

  change_password() {
    this.quickSend('Vorrei cambiare la mia password');
  }
  
  frequently_asked_questions() {
    const faqs = [
      'Quanti giorni di ferie ha un lavoratore full time?',
      'Entro quando devo pianificare le mie ferie?',
      'Come posso richiedere un permesso per visita medica?',
      'A quanto ammonta il valore dei buoni pasto elettronici?',
      'Cosa devo fare se perdo la mia card dei buoni pasto?',
      'Come posso aggiornare i miei dati bancari o anagrafici?',
      'Quando viene accreditato lo stipendio mensile?',
      "Che cos'è la VPN aziendale?",
      'Chi devo contattare se ho problemi con la vpn?',
      'Mi puoi elencare tutti i benefit a cui hanno diritto i dipendenti?',
    ];
    this.quickSend(faqs[Math.floor(Math.random() * faqs.length)]);
  }

  closeConversation() {
    this.handleMessage(
      this.createMessage(
        'Grazie per aver utilizzato il nostro servizio. Buona giornata!',
        'bot'
      )
    );
    this.closeChatSession();
    this.conversationEnded = true;
  }

 /* -------------------------------------------------------- */
 /*  UTILS                                                   */
 /* -------------------------------------------------------  */

  ngAfterViewChecked() {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  scrollToBottom() {
    this.scrollContainer?.nativeElement.scroll({
      top: this.scrollContainer.nativeElement.scrollHeight,
      behavior: 'smooth',
    });
  }

  getInitialsFromEmail(email: string | null) {
    if (!email) return '';
    const [name] = email.split('@');
    return name
      .split('.')
      .map((p) => p[0]?.toUpperCase())
      .join('');
  }

  // Chisura sidebar da overlay mobile
  onOverlayClick() {
    this.sidebar.closeDrawer(); // chiude la sidebar tramite il metodo interno
  }
}