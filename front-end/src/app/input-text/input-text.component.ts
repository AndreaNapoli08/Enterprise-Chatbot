import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { Message } from '../interfaces/message';  

@Component({
  selector: 'input-text',
  imports: [FormsModule, CommonModule],
  templateUrl: './input-text.component.html',
  styleUrl: './input-text.component.css'
})

export class InputText {
  answer = '';
  @Output() submitAnswer = new EventEmitter<Message>();

  onSubmit() {
    const text = this.answer.trim();
    if (!text) return;

    const now = new Date();
    const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const message: Message = {
      text,
      role: 'user',
      time
    };
    
    this.submitAnswer.emit(message);
    this.answer = '';
  }

  

}
