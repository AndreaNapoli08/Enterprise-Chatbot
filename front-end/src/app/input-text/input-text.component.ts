import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'input-text',
  imports: [FormsModule, CommonModule],
  templateUrl: './input-text.component.html',
  styleUrl: './input-text.component.css'
})
export class InputText {
  answer = '';
  messages: string[] = [];

  @Output() submitAnswer = new EventEmitter<string[]>();

  onSubmit() {
    // emit current answer, then clear
    const toSend = this.answer?.trim();
    if (toSend) {
      this.messages.push(toSend);
      this.submitAnswer.emit(this.messages);
    }
    this.answer = '';
  }

}
