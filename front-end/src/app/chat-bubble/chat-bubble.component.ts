import { Component, Input } from '@angular/core';


@Component({
  selector: 'chat-bubble',
  imports: [],
  templateUrl: './chat-bubble.component.html',
  styleUrl: './chat-bubble.component.css'
})
export class ChatBubble {
  @Input() message: string | null = null;

}
