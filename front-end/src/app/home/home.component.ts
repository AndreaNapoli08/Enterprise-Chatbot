import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';
import { Profile } from '../profile/profile.component';
import { AuthService } from '../services/auth.service';
import { Message } from '../interfaces/message';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatBubble, InputText, Profile],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class Home implements AfterViewChecked {
  messages: Message[] = [];
  email: string | null = null;
  initials: string = '';
  shouldScroll = false;
  loading = false;
  buttons = false;
  waiting_answer = false;

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
  constructor(private authService: AuthService) {}

  ngOnInit() {
    this.email = this.authService.getEmail();
    this.initials = this.getInitialsFromEmail(this.email);
  }

  handleMessage(message: any) {
    this.loading = true;
    this.shouldScroll = true;

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

}
