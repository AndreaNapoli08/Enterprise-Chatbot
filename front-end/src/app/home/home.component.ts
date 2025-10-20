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

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef<HTMLDivElement>;
  constructor(private authService: AuthService) {}

  ngOnInit() {
    this.email = this.authService.getEmail();
    this.initials = this.getInitialsFromEmail(this.email);
  }

  handleMessage(message: any) {
    this.loading = true;
    if(message.role === 'bot') {
      setTimeout(() => {
        this.messages.push(message);    
        if(message.buttons.length === 0){
          this.waiting_answer = false;
          this.loading = false;
        }else{
          this.waiting_answer = true;
        }
        this.shouldScroll = true;
      }, 500);
    }else{
      this.messages.push(message);
      this.shouldScroll = true;
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

  onConversationEnded() {
    
  }
}
