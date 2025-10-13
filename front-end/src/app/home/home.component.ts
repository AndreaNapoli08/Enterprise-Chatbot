import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { InputText } from '../input-text/input-text.component';
import { ChatBubble } from '../chat-bubble/chat-bubble.component';

@Component({
  selector: 'app-home',
  imports: [CommonModule, ChatBubble, InputText],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css'
})
export class Home {
  messages: string[] = [];

  handleMessage(msg: string[]) {
    this.messages = msg;
  }

}
