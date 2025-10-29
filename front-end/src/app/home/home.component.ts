import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';
import { Profile } from '../profile/profile.component';
import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatBubble, InputText, Profile],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class Home implements AfterViewChecked {
  messages: any[] = [];
  email: string | null = null;
  initials: string = '';
  shouldScroll = false;
  loading = false;
  buttons = false;
  waiting_answer = false;

  // Visualizzazione elementi dopo un'attesa prolungata
  long_waiting = false;
  long_waiting_text = '';
  private longWaitTimer: any = null;
  private textChangeTimer: any = null;
  private textIndex = 0;
  private waitingTexts = [
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
    if(message.role === 'bot'){ 
      console.log("Received bot message:", message);
      clearTimeout(this.longWaitTimer);
      clearInterval(this.textChangeTimer);
      this.long_waiting = false;
      this.long_waiting_text = '';

      this.messages.push(message);  
      if(message.buttons.length === 0){
        this.waiting_answer = false;
        this.loading = false;
      }else{
        this.waiting_answer = true;
      }
      this.shouldScroll = true;
      if(message.text === "Perfetto, cerco subito nei documenti"){
        clearTimeout(this.longWaitTimer);
        clearInterval(this.textChangeTimer);
        this.longWaitTimer = setTimeout(() => {
          this.long_waiting = true;
          this.textIndex = 0;
          this.long_waiting_text = this.waitingTexts[this.textIndex];
          this.textChangeTimer = setInterval(() => {
            this.textIndex = (this.textIndex + 1) % this.waitingTexts.length;
            this.long_waiting_text = this.waitingTexts[this.textIndex];
          }, 1000);
        }, 2000);
      }
    }else{
      this.messages.push(message);
      this.shouldScroll = true;
      
      // dopo 30 secondi di attesa mostra "Sto pensando...", dopodiché ogni 10 secondi cambia il testo mostrato
      // per indicare che il bot sta ancora elaborando la risposta e non si è bloccato
      clearTimeout(this.longWaitTimer);
      clearInterval(this.textChangeTimer);
      this.longWaitTimer = setTimeout(() => {
        this.long_waiting = true;
        this.textIndex = 0;
        this.long_waiting_text = this.waitingTexts[this.textIndex];
        this.textChangeTimer = setInterval(() => {
          this.textIndex = (this.textIndex + 1) % this.waitingTexts.length;
          this.long_waiting_text = this.waitingTexts[this.textIndex];
        }, 1000);
      }, 2000);
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
