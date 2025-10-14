import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, ChatBubble, InputText],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class Home implements AfterViewChecked {
  messages: any[] = [];
  shouldScroll = false;
  loading = false;

  @ViewChild('scrollContainer') private scrollContainer!: ElementRef<HTMLDivElement>;

  handleMessage(message: any) {
    this.messages.push(message);
    this.shouldScroll = true;
    this.loading = true;

    setTimeout(() => {
      const now = new Date();
      const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      this.messages.push({
        text: `Hai detto: "${message.text}"`,
        role: 'bot',
        time
      });
      this.loading = false;
      this.shouldScroll = true;
    }, 1000);
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
}
