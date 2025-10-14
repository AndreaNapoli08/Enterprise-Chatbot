import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';

@Component({
  selector: 'chat-bubble',
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.css',
  imports: [CommonModule]
})
export class ChatBubble {
  @Input() message!: Message;

}
