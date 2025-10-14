export interface Message {
  text: string;
  role: 'user' | 'bot';
  time: string;
}